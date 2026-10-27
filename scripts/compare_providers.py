"""I compare generation providers on the same original evidence and record real costs."""

import asyncio
import json
import os
import time

from pydantic import SecretStr

from scripts.cloud_setup import BUCKET
from src.config import ROOT, Settings
from src.library import Library
from src.providers import Providers
from src.store import make_store


async def compare():
    os.environ["CLOUDSDK_CONFIG"] = str(ROOT / ".cache/gcloud")
    settings = Settings(app_env="cloud", state_backend="firestore", gcs_bucket=BUCKET)
    store = make_store(settings)
    library = Library(settings, store)
    book = next(b for b in store.query("books", owner_id="public") if b["gutenberg_id"] == 11)
    chunks = library.chunks(book["id"])[:2]
    prompt = (
        "Why does Alice follow the White Rabbit? Answer briefly with original source IDs.\n"
        + "\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
    )
    records = []
    for provider in ("nvidia", "openai", "anthropic"):
        selected = settings.model_copy(
            update={
                f"{other}_api_key": SecretStr("")
                for other in ("nvidia", "openai", "anthropic")
                if other != provider
            }
        )
        calls, answer, first = [], "", None
        started = time.monotonic()
        async for token in Providers(selected, store).stream(
            "Use only the supplied book evidence. Distinguish interpretation from fact.",
            prompt,
            task="research",
            emit=lambda event, data, calls=calls: calls.append(data),
        ):
            if first is None:
                first = time.monotonic() - started
            answer += token
        assert answer.strip() and any(c["id"] in answer for c in chunks)
        records.append(
            {
                "provider": provider,
                "ttft_seconds": first,
                "total_seconds": time.monotonic() - started,
                "answer": answer,
                "traces": calls,
            }
        )
        print("Provider comparison completed:", provider, flush=True)
    (ROOT / "reports/provider_comparison.json").write_text(json.dumps(records, indent=2))
    ledgers = {p: store.get("budgets", p) for p in ("openai", "anthropic")}
    (ROOT / "reports/budgets.json").write_text(json.dumps(ledgers, indent=2))
    print("Cumulative reserved/spent ledger:", ledgers, flush=True)


if __name__ == "__main__":
    asyncio.run(compare())
