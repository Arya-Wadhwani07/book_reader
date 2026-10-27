import io
import json
import os
import time
import uuid

import httpx
import pytest

from scripts.verify_release import read_events, verify_stream


@pytest.fixture(scope="module")
def client():
    url = os.environ["BASE_URL"]
    with httpx.Client(base_url=url, timeout=300, headers={"Origin": url.rstrip("/")}) as session:
        response = session.get("/api/bootstrap")
        response.raise_for_status()
        yield session


def test_live_readiness_and_assets(client):
    assert client.get("/readyz").json()["ready"] is True
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    books = client.get("/api/books").json()
    ready = [b for b in books if b["status"] == "ready"]
    assert len(ready) >= 8
    assert {"Fiction", "Nonfiction"} <= {b["kind"] for b in ready}


def test_live_rag_routing_sources_and_memory(client, record_testsuite_property):
    book = next(book for book in client.get("/api/books").json() if book["status"] == "ready")
    chat = client.post("/api/chats", json={}).json()
    payload = {
        "query": "Use the research specialist and semantic retrieval to explain the opening of this book with original passage citations.",
        "session_id": chat["id"],
        "turn_id": str(uuid.uuid4()),
        "book_id": book["id"],
        "spoiler_limit": None,
        "depth": "brief",
    }
    started, first_token = time.monotonic(), None
    raw = bytearray()
    with client.stream("POST", "/api/chat", json=payload) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line == "event: token" and first_token is None:
                first_token = time.monotonic() - started
            raw.extend((line + "\n").encode())
    verify_stream(io.BytesIO(raw))
    events = list(read_events(io.BytesIO(raw)))
    providers = {
        data.get("provider")
        for event, data in events
        if event == "trace" and data.get("type") == "llm_route"
    }
    assert len(providers) >= 2
    citation = next(data for event, data in events if event == "citation" and data.get("chunk_id"))
    passage = client.get(f"/api/books/{book['id']}/sources/{citation['chunk_id']}")
    assert passage.status_code == 200
    assert passage.json()["text"].strip()
    restored = client.get(f"/api/chats/{chat['id']}").json()
    assert restored["turns"][0]["status"] == "complete"
    assert restored["turns"][0]["answer"].strip()
    record_testsuite_property("live_ttft_seconds", first_token)
    record_testsuite_property("live_total_seconds", time.monotonic() - started)
    assert client.post("/api/chat", json=payload).status_code == 409
    other = httpx.Client(base_url=str(client.base_url), timeout=30)
    try:
        other.get("/api/bootstrap").raise_for_status()
        assert other.get(f"/api/chats/{chat['id']}").status_code == 404
    finally:
        other.close()


def test_live_shared_mcp(client):
    book = next(book for book in client.get("/api/books").json() if book["status"] == "ready")
    chat = client.post("/api/chats", json={}).json()
    payload = {
        "query": "Research the author and film adaptations, then find current hardcover editions to buy. Use both research and data specialists.",
        "session_id": chat["id"],
        "turn_id": str(uuid.uuid4()),
        "book_id": book["id"],
        "spoiler_limit": None,
        "depth": "brief",
    }
    response = client.post("/api/chat", json=payload)
    response.raise_for_status()
    events = list(read_events(io.BytesIO(response.content)))
    assert events[-1] == ("done", json.loads(response.text.split("event: done\ndata: ")[-1]))
    assert events[-1][1]["success"] is True
    sharing = [
        data for event, data in events if event == "trace" and data.get("type") == "mcp_tool_call"
    ]
    assert {"research", "data"} <= {data["agent"] for data in sharing}
    assert {data["tool"] for data in sharing} == {"tavily_search"}
    assert len({data["reason"] for data in sharing}) >= 2
