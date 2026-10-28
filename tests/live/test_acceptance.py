import io
import json
import os
import re
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


@pytest.mark.parametrize(
    "query",
    ["What is the weather in Los Angeles today?", "Write an unrelated poem about my new bicycle."],
)
def test_live_off_topic_redirect(client, query):
    book = next(b for b in client.get("/api/books").json() if b["status"] == "ready")
    chat = client.post("/api/chats", json={}).json()
    response = client.post(
        "/api/chat",
        json={
            "query": query,
            "session_id": chat["id"],
            "turn_id": str(uuid.uuid4()),
            "book_id": book["id"],
            "spoiler_limit": 1,
            "depth": "brief",
        },
    )
    response.raise_for_status()
    events = list(read_events(io.BytesIO(response.content)))
    assert events[-1][0] == "done" and events[-1][1]["success"] is True
    assert "book reading companion" in response.text
    assert any("Off-topic, no worker" in data.get("reason", "") for _, data in events)
    assert not any(data.get("type") in {"agent_input", "mcp_tool_call"} for _, data in events)
    saved = client.get(f"/api/chats/{chat['id']}").json()["turns"][0]
    assert saved["status"] == "complete" and saved["answer"]


def test_live_summary_inputs_and_unrehearsed_book_question(client):
    book = next(b for b in client.get("/api/books").json() if b.get("gutenberg_id") == 11)
    chat = client.post("/api/chats", json={}).json()
    response = client.post(
        "/api/chat",
        json={
            "query": "Summarize the opening chapter, then explain how Alice's attention shifts from ordinary surroundings to something unexpected. Separate observation from interpretation.",
            "session_id": chat["id"],
            "turn_id": str(uuid.uuid4()),
            "book_id": book["id"],
            "spoiler_limit": 1,
            "depth": "brief",
        },
    )
    response.raise_for_status()
    events = list(read_events(io.BytesIO(response.content)))
    assert events[-1][0] == "done" and events[-1][1]["success"] is True
    summary = next(data for _, data in events if data.get("type") == "summary_input")
    assert summary["book_id"] == book["id"] and summary["maps"]
    assert all(row["chapter"] <= 1 for row in summary["maps"])
    routes = [data for _, data in events if data.get("type") == "agent_route" and "state" in data]
    assert routes[-1]["agent"] == "synthesis"
    assert "summary" in routes[-1]["state"]["completed"]
    for row in summary["maps"]:
        for identifier in row["chunk_ids"]:
            source = client.get(f"/api/books/{book['id']}/sources/{identifier}")
            assert source.status_code == 200 and source.json()["text"]
    assert not any(data.get("type") == "mcp_tool_call" for _, data in events)


@pytest.mark.parametrize(
    "gutenberg_id,query",
    [
        (
            41445,
            "Why does Walton want a friend in his opening letters, despite having a crew? Distinguish his words from your interpretation.",
        ),
        (
            205,
            "Why does Thoreau say he went to the woods, and what did he want to learn there? Support your explanation with passages.",
        ),
        (
            148,
            "How did Franklin use his notebook and weekly routine to work on his virtues? Explain the method rather than just listing the virtues.",
        ),
    ],
)
def test_live_additional_books(client, record_testsuite_property, gutenberg_id, query):
    book = next(b for b in client.get("/api/books").json() if b.get("gutenberg_id") == gutenberg_id)
    chat = client.post("/api/chats", json={}).json()
    started = time.monotonic()
    response = client.post(
        "/api/chat",
        json={
            "query": query,
            "session_id": chat["id"],
            "turn_id": str(uuid.uuid4()),
            "book_id": book["id"],
            "depth": "brief",
            "spoiler_limit": None,
        },
    )
    total = time.monotonic() - started
    response.raise_for_status()
    events = list(read_events(io.BytesIO(response.content)))
    assert events[-1][0] == "done" and events[-1][1]["success"] is True
    traces = [data for event, data in events if event == "trace"]
    assert not any(t.get("type") == "worker_failure" for t in traces)
    assert any(t.get("type") == "agent_route" and t.get("state") for t in traces)
    assert len({t["provider"] for t in traces if t.get("type") == "llm_route"}) >= 2
    answer = "".join(data["text"] for event, data in events if event == "token")
    assert answer.strip()
    citations = [data for event, data in events if event == "citation" and data.get("chunk_id")]
    assert citations
    cited_ids = set(re.findall(r"(?<![\w-])[\w-]+-s\d+-t\d+(?![\w-])", answer))
    assert cited_ids
    assert cited_ids <= {citation["chunk_id"] for citation in citations}
    passages = []
    for citation in citations:
        source = client.get(f"/api/books/{book['id']}/sources/{citation['chunk_id']}")
        source.raise_for_status()
        assert source.json()["text"].strip()
        passages.append({"chunk_id": citation["chunk_id"], "text": source.json()["text"]})
    saved = client.get(f"/api/chats/{chat['id']}").json()["turns"][0]
    assert saved["status"] == "complete" and saved["answer"] == answer
    record_testsuite_property(
        f"additional_book_{gutenberg_id}",
        json.dumps(
            {
                "question": query,
                "answer": answer,
                "total_seconds": total,
                "traces": traces,
                "passages": passages,
            }
        ),
    )
