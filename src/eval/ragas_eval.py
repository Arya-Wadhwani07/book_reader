import argparse
import asyncio
import io
import json
import os
import time
import uuid

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, Field

from scripts.cloud_setup import BUCKET
from scripts.verify_release import read_events
from src.config import ROOT, Settings
from src.library import BudgetedEmbeddings, Library
from src.providers import Providers
from src.store import make_store


class BudgetedJudge(BaseChatModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    providers: Providers = Field(exclude=True)

    @property
    def _llm_type(self):
        return "budgeted-openai-ragas-judge"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        text = await self.providers.complete(
            "I evaluate grounded answers. Follow the requested evaluation JSON schema exactly.",
            "\n".join(str(message.content) for message in messages),
            task="evaluate",
        )
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=text), generation_info={"finish_reason": "stop"}
                )
            ]
        )


def evaluate_service(url, cloud, reuse_answers=False):
    os.environ["RAGAS_DO_NOT_TRACK"] = "true"
    os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
    os.environ["XDG_CACHE_HOME"] = str(ROOT / ".cache")
    os.environ["CLOUDSDK_CONFIG"] = str(ROOT / ".cache/gcloud")
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.run_config import RunConfig

    settings = (
        Settings(app_env="cloud", state_backend="firestore", gcs_bucket=BUCKET)
        if cloud
        else Settings()
    )
    store = make_store(settings)
    providers = Providers(settings, store)
    library = Library(settings, store)
    questions = json.loads((ROOT / "src/eval/questions.json").read_text())
    rows, measurements = [], []
    with httpx.Client(base_url=url, timeout=300) as client:
        client.get("/api/bootstrap").raise_for_status()
        books = client.get("/api/books").json()
        for item in [] if reuse_answers else questions:
            book = next(book for book in books if book.get("gutenberg_id") == item["gutenberg_id"])
            chat = client.post("/api/chats", json={}).json()
            request = {
                "query": "Use semantic retrieval to answer with citations: " + item["question"],
                "session_id": chat["id"],
                "turn_id": str(uuid.uuid4()),
                "book_id": book["id"],
                "depth": "brief",
                "spoiler_limit": None,
            }
            started, first, raw = time.monotonic(), None, bytearray()
            with client.stream("POST", "/api/chat", json=request) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line == "event: token" and first is None:
                        first = time.monotonic() - started
                    raw.extend((line + "\n").encode())
            events = list(read_events(io.BytesIO(raw)))
            if not events or events[-1][0] != "done" or not events[-1][1]["success"]:
                raise RuntimeError("An evaluation query did not complete.")
            ids = list(
                dict.fromkeys(
                    identifier
                    for event, data in events
                    if event == "trace" and data.get("type") == "rag_retrieval"
                    for identifier in data["chunk_ids"]
                )
            )
            rows.append(
                {
                    "user_input": item["question"],
                    "response": "".join(data["text"] for event, data in events if event == "token"),
                    "retrieved_contexts": [
                        library.chunk(book["id"], identifier)["text"] for identifier in ids
                    ],
                    "reference": item["reference"],
                }
            )
            measurements.append(
                {
                    "question": item["question"],
                    "ttft_seconds": first,
                    "total_seconds": time.monotonic() - started,
                    "traces": [data for event, data in events if event == "trace"],
                }
            )
            print("Generated evaluation answer:", item["question"], flush=True)
    if reuse_answers:
        saved = json.loads((ROOT / "reports/evaluation_answers.json").read_text())
        rows, measurements = saved["rows"], saved["measurements"]
        if [row["user_input"] for row in rows] != [item["question"] for item in questions]:
            raise ValueError("Saved answers do not match the fixed question set.")
        for row, measurement in zip(rows, measurements, strict=True):
            identifiers = list(
                dict.fromkeys(
                    identifier
                    for trace in measurement["traces"]
                    if trace.get("type") == "rag_retrieval"
                    for identifier in trace["chunk_ids"]
                )
            )
            if not identifiers:
                raise ValueError("The saved answer has no actual retrieval trace.")
            row["retrieved_contexts"] = [
                library.chunk(identifier.split("-s")[0], identifier)["text"]
                for identifier in identifiers
            ]
    (ROOT / "reports/evaluation_answers.json").write_text(
        json.dumps({"rows": rows, "measurements": measurements}, indent=2)
    )
    result = evaluate(
        EvaluationDataset.from_list(rows),
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(BudgetedJudge(providers=providers)),
        embeddings=LangchainEmbeddingsWrapper(BudgetedEmbeddings(providers)),
        run_config=RunConfig(max_workers=2, max_retries=1, timeout=120),
        raise_exceptions=True,
    )
    records = result.to_pandas().to_dict(orient="records")
    (ROOT / "reports/ragas_results.json").write_text(json.dumps(records, indent=2, allow_nan=False))
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--cloud", action="store_true")
    parser.add_argument("--reuse-answers", action="store_true")
    args = parser.parse_args()
    evaluate_service(args.url, args.cloud, args.reuse_answers)
