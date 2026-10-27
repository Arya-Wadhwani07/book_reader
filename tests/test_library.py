import asyncio
import gzip
import hashlib
import json
import time

import pytest

from src.config import ROOT, Settings
from src.library import Library
from src.store import Conflict, SQLiteStore


@pytest.fixture
def library(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    return Library(settings, SQLiteStore(tmp_path / "state.sqlite3"))


def book_record(library, status="queued"):
    book = {
        "id": "book",
        "owner_id": "reader",
        "filename": "book.txt",
        "title": "Book",
        "created_at": time.time(),
        "status": status,
        "chapters": [],
    }
    library.store.put("books", "book", book)
    library.artifacts.put(
        "book/original",
        b"CHAPTER I\n"
        + b"Alice reads a book beside the river. She follows the rabbit and discovers a new world. "
        * 40,
    )
    return book


def test_ingestion_resume_reuses_facts_and_publishes_only_complete(library, monkeypatch):
    book_record(library)
    writes, calls = [], []

    class Vectors:
        def add_texts(self, **kwargs):
            assert library.book("reader", "book")["status"] == "indexing"
            writes.extend(kwargs["ids"])

    class Provider:
        async def complete(self, *args, **kwargs):
            calls.append(True)
            return json.dumps(
                {
                    "summary": "Alice follows a rabbit.",
                    "characters": ["Alice"],
                    "events": ["Following"],
                    "concepts": [],
                }
            )

    monkeypatch.setattr(library, "vector_store", lambda _: Vectors())
    library.providers = Provider()
    asyncio.run(library.ingest("book"))
    ready = library.book("reader", "book")
    assert ready["status"] == "ready"
    assert len(writes) == ready["chunk_count"]
    count = len(calls)
    asyncio.run(library.ingest("book"))
    assert len(calls) == count
    ready["status"] = "failed"
    library.store.put("books", "book", ready)
    asyncio.run(library.ingest("book"))
    assert len(calls) == count
    assert set(writes) == {c["id"] for c in library.chunks("book")}


def test_ingestion_failure_never_publishes_ready(library, monkeypatch):
    book_record(library)

    class BrokenVectors:
        def add_texts(self, **kwargs):
            raise RuntimeError("private key and endpoint")

    monkeypatch.setattr(library, "vector_store", lambda _: BrokenVectors())
    with pytest.raises(RuntimeError):
        asyncio.run(library.ingest("book"))
    book = library.book("reader", "book")
    assert book["status"] == "failed"
    assert "private" not in book["error"]


def test_retry_is_owner_scoped_and_deduplicated(library, monkeypatch):
    book_record(library, "failed")
    started = []

    async def start(identifier):
        started.append(identifier)

    monkeypatch.setattr(library, "start_ingestion", start)
    with pytest.raises(KeyError):
        asyncio.run(library.retry("other", "book"))
    assert asyncio.run(library.retry("reader", "book"))["status"] == "queued"
    with pytest.raises(Conflict):
        asyncio.run(library.retry("reader", "book"))
    assert started == ["book"]


def test_live_ingestion_lease_rejects_competing_worker(library):
    book = book_record(library, "indexing")
    book["ingestion_lease"] = time.time() + 60
    library.store.put("books", "book", book)
    with pytest.raises(Conflict):
        asyncio.run(library.ingest("book"))


def test_retrieval_filters_owner_book_and_spoiler(library, monkeypatch):
    book_record(library, "ready")
    calls = []

    class Vectors:
        def similarity_search(self, query, **kwargs):
            calls.append(kwargs)
            return []

    monkeypatch.setattr(library, "vector_store", lambda _: Vectors())
    with pytest.raises(KeyError):
        library.retrieve("other", "book", "query", 1)
    assert library.retrieve("reader", "book", "query", 2, k=3) == []
    assert calls == [{"k": 3, "filter": {"book_id": {"$eq": "book"}, "chapter": {"$lte": 2}}}]


def test_public_snapshot_integrity_and_complete_provenance():
    snapshot = json.loads(gzip.decompress((ROOT / "corpus/snapshot.json.gz").read_bytes()))
    manifest = json.loads((ROOT / "corpus/manifest.json").read_text())
    assert {b["gutenberg_id"] for b in snapshot["books"]} == {b["gutenberg_id"] for b in manifest}
    assert snapshot["source"] == "deployed"
    for book in snapshot["books"]:
        assert hashlib.sha256(book["original"].encode()).hexdigest() == book["original_sha256"]
        assert book["pipeline_version"] == 2
        chunks = {c["id"] for c in book["chunks"]}
        assert len(chunks) == book["chunk_count"]
        assert {c for f in book["facts"] for c in f["chunk_ids"]} == chunks
        assert book["source_url"].startswith("https://gutenberg.pglaf.org/")
        assert not {"owner_id", "session_id", "api_key"} & book.keys()


def test_category_correction_cannot_modify_another_owners_book(library):
    book_record(library)
    assert library.set_kind("reader", "book", "Nonfiction")["kind"] == "Nonfiction"
    with pytest.raises(KeyError):
        library.set_kind("other", "book", "Fiction")
    with pytest.raises(ValueError):
        library.set_kind("reader", "book", "invented")
    assert library.book("reader", "book")["kind"] == "Nonfiction"


def test_api_upload_limit_does_not_charge_duplicate_files(library, monkeypatch):
    from fastapi.testclient import TestClient
    from test_app import EngineFixture

    from src.app import create_app

    async def start(identifier):
        return None

    monkeypatch.setattr(library, "start_ingestion", start)
    with TestClient(
        create_app(library.settings, library.store, EngineFixture(), library)
    ) as client:
        client.get("/api/bootstrap")
        for index in range(3):
            content = f"A distinct English book number {index}.".encode()
            response = client.post(
                "/api/books", content=content, headers={"X-Filename": "book.txt"}
            )
            assert response.status_code == 202
            assert (
                client.post(
                    "/api/books", content=content, headers={"X-Filename": "book.txt"}
                ).status_code
                == 409
            )
        assert (
            client.post(
                "/api/books", content=b"A fourth distinct book.", headers={"X-Filename": "book.txt"}
            ).status_code
            == 429
        )
