import json
import os

from scripts.cloud_setup import BUCKET, PROJECT
from src.artifacts import Artifacts
from src.config import ROOT, Settings
from src.store import FirestoreStore, make_store


def migrate():
    os.environ["CLOUDSDK_CONFIG"] = str(ROOT / ".cache/gcloud")
    local = Settings()
    source = make_store(local)
    destination = FirestoreStore(PROJECT)
    cloud_settings = Settings(app_env="cloud", state_backend="firestore", gcs_bucket=BUCKET)
    artifacts = Artifacts(cloud_settings)
    books = source.query("books", owner_id="public")
    if len(books) < 8 or any(book["status"] != "ready" for book in books):
        raise RuntimeError("My complete curated corpus must be ready before migration.")
    for book in books:
        for name in ("original", "chunks.json"):
            content = (local.data_dir / "files" / book["id"] / name).read_bytes()
            artifacts.put(f"{book['id']}/{name}", content)
        for fact in source.query("book_facts", book_id=book["id"]):
            destination.put("book_facts", fact["id"], fact)
        destination.put("books", book["id"], book)
        print("Migrated", book["title"], flush=True)
    for provider in ("openai", "anthropic"):
        ledger = source.get("budgets", provider)
        if ledger:
            if ledger["reservations"]:
                raise RuntimeError(
                    "Finish all local paid calls before migrating the budget ledger."
                )
            if destination.get("budgets", provider):
                raise RuntimeError(
                    "A cloud budget ledger already exists; I will not overwrite spending."
                )
            destination.put("budgets", provider, ledger)
    for usage in source.query("usage"):
        destination.put("usage", usage["id"], usage)
    (ROOT / "reports/corpus.json").write_text(
        json.dumps(
            [
                {
                    key: book.get(key)
                    for key in (
                        "id",
                        "title",
                        "author",
                        "kind",
                        "words",
                        "tokens",
                        "chunk_count",
                        "source_url",
                    )
                }
                for book in books
            ],
            indent=2,
        )
    )
    print(
        "Eight books, source artifacts, structured facts, and cumulative budgets migrated.",
        flush=True,
    )


if __name__ == "__main__":
    migrate()
