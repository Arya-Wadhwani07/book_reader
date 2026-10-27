"""I export only the public curated corpus, with source and artifact checksums."""

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone

from src.artifacts import Artifacts
from src.config import ROOT, Settings
from src.store import make_store


def export(settings):
    store, artifacts = make_store(settings), Artifacts(settings)
    manifest = json.loads((ROOT / "corpus/manifest.json").read_text())
    selected = {item["gutenberg_id"] for item in manifest}
    books = store.query("books", owner_id="public")
    books = [book for book in books if book.get("gutenberg_id") in selected]
    if len(books) != len(selected) or any(book["status"] != "ready" for book in books):
        raise ValueError("My complete curated corpus must be ready.")
    records = []
    for book in sorted(books, key=lambda b: b["gutenberg_id"]):
        original = artifacts.get(f"{book['id']}/original")
        chunks = artifacts.get(f"{book['id']}/chunks.json")
        facts = store.query("book_facts", book_id=book["id"])
        parsed = json.loads(chunks)
        ids = {chunk["id"] for chunk in parsed}
        if len(ids) != book["chunk_count"] or any(
            source not in ids for fact in facts for source in fact["chunk_ids"]
        ):
            raise ValueError("My source metadata is inconsistent.")
        record = {
            key: book[key]
            for key in (
                "id",
                "gutenberg_id",
                "title",
                "author",
                "kind",
                "filename",
                "source_url",
                "rights",
                "created_at",
                "indexed_at",
                "pipeline_version",
                "chapters",
                "words",
                "tokens",
                "chunk_count",
            )
        }
        record.update(
            original_sha256=hashlib.sha256(original).hexdigest(),
            chunks_sha256=hashlib.sha256(chunks).hexdigest(),
            original=original.decode("utf-8"),
            chunks=parsed,
            facts=facts,
        )
        records.append(record)
    snapshot = {
        "version": "2026-10-27-pipeline-2",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": "deployed" if settings.app_env == "cloud" else "local",
        "books": records,
    }
    output = ROOT / "corpus/snapshot.json.gz"
    output.write_bytes(gzip.compress(json.dumps(snapshot, ensure_ascii=False).encode(), mtime=0))
    print(
        json.dumps(
            {
                "books": len(records),
                "chunks": sum(b["chunk_count"] for b in records),
                "snapshot_bytes": output.stat().st_size,
                "source": snapshot["source"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cloud", action="store_true")
    args = parser.parse_args()
    options = {}
    if args.cloud:
        from scripts.cloud_setup import BUCKET

        options = {"app_env": "cloud", "state_backend": "firestore", "gcs_bucket": BUCKET}
    export(Settings(**options))
