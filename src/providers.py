import asyncio
import time
import uuid

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.budget import Budget

# I verified standard short-context prices on official pricing pages on 2026-10-27.
PRICES = {"gpt-6-luna": (0.1, 0.5), "claude-sonnet-5": (2, 10)}


class Providers:
    def __init__(self, settings, store):
        self.settings, self.store = settings, store
        self.budget = Budget(store, settings)

    def route(self, task, depth="brief"):
        available = self.settings.available_providers()
        if not available:
            raise RuntimeError("No generation provider is configured.")
        preferred = "openai" if task in {"plan", "extract", "evaluate", "reduce"} else "nvidia"
        reason = (
            "I use low-cost structured planning and extraction."
            if preferred == "openai"
            else "I use student-quota generation for focused book evidence."
        )
        if depth == "deep" and task != "plan":
            preferred, reason = "anthropic", "I use Sonnet 5 for detailed cross-section synthesis."
        if preferred not in available:
            preferred = next(p for p in ("openai", "nvidia", "anthropic") if p in available)
            reason = "I select an available provider because the preferred service is unconfigured."
        return preferred, reason

    def model(self, provider, max_output, task="answer"):
        model = getattr(self.settings, f"{provider}_model")
        key = getattr(self.settings, f"{provider}_api_key").get_secret_value()
        if provider == "anthropic":
            return ChatAnthropic(
                model=model, api_key=key, max_tokens=max_output, timeout=90, max_retries=0
            )
        options = dict(model=model, api_key=key, max_tokens=max_output, timeout=90, max_retries=0)
        if provider == "nvidia":
            options["base_url"] = "https://integrate.api.nvidia.com/v1"
            options["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        else:
            options.update(use_responses_api=True, reasoning={"effort": "none"})
            if task in {"plan", "extract"}:
                properties = (
                    {
                        "workers": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["research", "summary", "data"]},
                        },
                        "reason": {"type": "string"},
                    }
                    if task == "plan"
                    else {
                        "summary": {"type": "string"},
                        **{
                            field: {"type": "array", "items": {"type": "string"}}
                            for field in ("characters", "events", "concepts")
                        },
                    }
                )
                options["model_kwargs"] = {
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": task,
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": properties,
                                "required": list(properties),
                                "additionalProperties": False,
                            },
                        },
                    }
                }
        return ChatOpenAI(**options)

    async def stream(self, system, prompt, task="answer", depth="brief", emit=None):
        preferred, reason = self.route(task, depth)
        alternatives = [
            p
            for p in ("openai", "nvidia", "anthropic")
            if p != preferred and p in self.settings.available_providers()
        ]
        providers = [preferred] + alternatives[:1]
        for index, provider in enumerate(providers):
            emitted = False
            try:
                async for text in self._stream_attempt(
                    system, prompt, task, depth, emit, provider, reason
                ):
                    emitted = True
                    yield text
                return
            except RuntimeError:
                if emitted or index + 1 == len(providers):
                    raise
                reason = f"I use {providers[index + 1]} because {provider} failed before producing answer text."
                if emit:
                    emit(
                        "trace",
                        {"type": "provider_recovery", "provider": provider, "reason": reason},
                    )

    async def _stream_attempt(self, system, prompt, task, depth, emit, provider, reason):
        if len((system + prompt).encode()) > 120_000:
            raise ValueError("The bounded evidence context is too large.")
        model_name = getattr(self.settings, f"{provider}_model")
        output_limit = 4096 if depth == "deep" else 2048 if task == "extract" else 1200
        reservation = None
        if provider in self.budget.limits:
            if model_name not in PRICES:
                raise ValueError("This model has no verified price bound.")
            rates = PRICES[model_name]
            bound = Budget.upper_bound(len((system + prompt).encode()) + 2048, output_limit, *rates)
            reservation = await asyncio.to_thread(self.budget.reserve, provider, bound)
        if emit:
            emit(
                "trace",
                {
                    "type": "llm_route",
                    "provider": provider,
                    "model": model_name,
                    "reason": reason,
                    "task": task,
                },
            )
        started, usage, success, received = time.monotonic(), None, False, False
        truncated = False
        try:
            async for chunk in self.model(provider, output_limit, task).astream(
                [SystemMessage(content=system), HumanMessage(content=prompt)]
            ):
                metadata = chunk.response_metadata
                truncated = (
                    truncated
                    or metadata.get("finish_reason") in {"length", "max_tokens"}
                    or metadata.get("stop_reason") == "max_tokens"
                    or metadata.get("status") == "incomplete"
                )
                if chunk.usage_metadata:
                    usage = chunk.usage_metadata
                content = chunk.content
                text = (
                    content
                    if isinstance(content, str)
                    else "".join(
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") in {"text", "output_text"}
                    )
                )
                if text:
                    received = True
                    yield text
            if truncated:
                raise RuntimeError("The provider reached its output limit before completion.")
            if not received:
                raise RuntimeError("The provider returned no answer text.")
            success = True
        except Exception as error:
            # I sanitize third-party errors, which can contain URLs or request credentials.
            raise RuntimeError(f"{provider} generation failed ({type(error).__name__}).") from None
        finally:
            actual = None
            if reservation and success and usage:
                actual = Budget.upper_bound(
                    usage["input_tokens"], usage["output_tokens"], *PRICES[model_name]
                )
            if reservation:
                await asyncio.to_thread(self.budget.settle, provider, reservation, actual)
            record = {
                "id": str(uuid.uuid4()),
                "provider": provider,
                "model": model_name,
                "task": task,
                "seconds": time.monotonic() - started,
                "usage": usage,
                "cost_usd": float(actual) if actual is not None else None,
                "success": success,
                "created_at": time.time(),
            }
            await asyncio.to_thread(self.store.put, "usage", record["id"], record)
            if emit:
                emit(
                    "trace",
                    {
                        "type": "llm_call",
                        "provider": provider,
                        "model": model_name,
                        "seconds": record["seconds"],
                        "cost_usd": record["cost_usd"],
                        "usage": usage,
                        "success": success,
                    },
                )

    async def complete(self, system, prompt, task="extract", depth="brief", emit=None):
        return "".join([text async for text in self.stream(system, prompt, task, depth, emit)])

    def embeddings(self, texts):
        if self.settings.openai_embedding_model != "text-embedding-3-small":
            raise ValueError("Only the verified embedding model is enabled.")
        bound = Budget.upper_bound(sum(len(t.encode()) for t in texts) + 100, 0, 0.02, 0)
        reservation = self.budget.reserve("openai", bound)
        started = time.monotonic()
        try:
            client = OpenAIEmbeddings(
                model=self.settings.openai_embedding_model,
                api_key=self.settings.openai_api_key.get_secret_value(),
                max_retries=0,
                request_timeout=60,
                check_embedding_ctx_length=False,
            )
            return client.embed_documents(texts)
        except Exception as error:
            raise RuntimeError(f"Embedding failed ({type(error).__name__}).") from None
        finally:
            # I charge the conservative bound because this wrapper does not expose billed usage.
            self.budget.settle("openai", reservation)
            identifier = str(uuid.uuid4())
            self.store.put(
                "usage",
                identifier,
                {
                    "id": identifier,
                    "provider": "openai",
                    "model": self.settings.openai_embedding_model,
                    "task": "embedding",
                    "seconds": time.monotonic() - started,
                    "cost_usd": float(bound),
                    "cost_basis": "conservative byte-token upper bound",
                    "created_at": time.time(),
                },
            )
