import asyncio

import pytest
from pydantic import SecretStr

from src.config import Settings
from src.providers import Providers
from src.store import SQLiteStore


def configured(tmp_path):
    return Settings(
        _env_file=None,
        data_dir=tmp_path,
        nvidia_api_key=SecretStr("fake"),
        nvidia_model="fixture",
        openai_api_key=SecretStr("fake"),
        openai_model="gpt-6-luna",
    )


def test_provider_recovery_before_first_token_is_visible(tmp_path):
    calls, events = [], []

    class Recovering(Providers):
        async def _stream_attempt(self, system, prompt, task, depth, emit, provider, reason):
            calls.append(provider)
            if provider == "nvidia":
                raise RuntimeError("simulated quota error")
            yield "Recovered answer"

    providers = Recovering(configured(tmp_path), SQLiteStore(tmp_path / "state.sqlite3"))

    async def run():
        return [
            t
            async for t in providers.stream(
                "system", "question", emit=lambda event, data: events.append(data)
            )
        ]

    assert asyncio.run(run()) == ["Recovered answer"]
    assert calls == ["nvidia", "openai"]
    assert events[0]["type"] == "provider_recovery"
    assert "before publishing" in events[0]["reason"]


def test_partial_provider_failure_never_switches_models(tmp_path):
    calls = []

    class Interrupted(Providers):
        async def _stream_attempt(self, system, prompt, task, depth, emit, provider, reason):
            calls.append(provider)
            yield "Partial"
            raise RuntimeError("simulated disconnect")

    providers = Interrupted(configured(tmp_path), SQLiteStore(tmp_path / "state.sqlite3"))

    async def run():
        return [t async for t in providers.stream("system", "question")]

    with pytest.raises(RuntimeError, match="disconnect"):
        asyncio.run(run())
    assert calls == ["nvidia"]


def test_truncated_output_is_not_a_success(tmp_path):
    from langchain_core.messages import AIMessageChunk

    class TruncatedModel:
        async def astream(self, messages):
            yield AIMessageChunk(
                content="Incomplete sentence", response_metadata={"finish_reason": "length"}
            )

    class TruncatedProvider(Providers):
        def model(self, *args):
            return TruncatedModel()

    store = SQLiteStore(tmp_path / "state.sqlite3")
    provider = TruncatedProvider(configured(tmp_path), store)

    async def run():
        return [text async for text in provider.stream("system", "question")]

    with pytest.raises(RuntimeError):
        asyncio.run(run())
    assert len(store.query("usage")) == 1
    assert store.query("usage")[0]["success"] is False


def test_buffered_specialist_failure_can_retry_without_mixing_text(tmp_path):
    calls = []

    class PartialSpecialist(Providers):
        async def _stream_attempt(self, system, prompt, task, depth, emit, provider, reason):
            calls.append(provider)
            if provider == "nvidia":
                yield "Discarded incomplete evidence"
                raise RuntimeError("Truncated worker output")
            yield "Complete replacement evidence"

    providers = PartialSpecialist(configured(tmp_path), SQLiteStore(tmp_path / "state.sqlite3"))
    assert (
        asyncio.run(providers.complete("system", "question", task="research"))
        == "Complete replacement evidence"
    )
    assert calls == ["nvidia", "openai"]
