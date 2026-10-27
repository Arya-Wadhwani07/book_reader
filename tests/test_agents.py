import asyncio
import json
import uuid

import pytest

from src.agents import BookGraph
from src.app import ChatRequest, create_app
from src.config import Settings
from src.library import Library
from src.store import SQLiteStore


class ProviderFixture:
    async def complete(self, system, prompt, task="extract", depth="brief", emit=None):
        if emit:
            emit(
                "trace",
                {"type": "llm_route", "provider": "fixture", "model": "fixture", "reason": task},
            )
        if task == "plan":
            return json.dumps(
                {"workers": ["research", "summary", "data"], "reason": "Mixed request"}
            )
        return "Evidence-supported result [book-s1-t0]."

    async def stream(self, system, prompt, **kwargs):
        yield "A grounded "
        yield "answer [book-s1-t0]."


class LibraryFixture:
    def book(self, owner, book_id):
        return {"id": "book", "title": "A book", "author": "An author", "status": "ready"}

    def retrieve(self, owner, book_id, query, spoiler_limit):
        return [
            {
                "id": "book-s1-t0",
                "source_id": "book",
                "chunk_id": "book-s1-t0",
                "title": "Chapter 1",
                "text": "Evidence",
                "chapter": 1,
            }
        ]

    def facts(self, owner, book_id, spoiler_limit):
        return [
            {
                "chapter": 1,
                "summary": "Opening [book-s1-t0]",
                "chunk_ids": ["book-s1-t0"],
                "characters": ["Alice"],
                "events": ["An arrival"],
                "concepts": ["Curiosity"],
            }
        ]


def test_graph_executes_three_specialists_and_persists(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)
    store = SQLiteStore(tmp_path / "state.sqlite3")
    request = ChatRequest(
        query="Summarize characters, author adaptations and buy hardcover editions",
        session_id=uuid.uuid4(),
        turn_id=uuid.uuid4(),
        book_id="book",
        spoiler_limit=None,
    )
    calls = []

    async def search(query, role):
        calls.append((query, role))
        return {
            "results": [
                {"title": "Source", "url": "https://example.test/book", "content": "Book details"}
            ]
        }

    graph = BookGraph(settings, store, LibraryFixture(), ProviderFixture(), search)

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    events = asyncio.run(run())
    assert "".join(data["text"] for event, data in events if event == "token").startswith(
        "A grounded"
    )
    assert {role for _, role in calls} == {"research", "data"}
    assert len({query for query, _ in calls}) == 2
    restored = BookGraph(
        settings, SQLiteStore(store.path), LibraryFixture(), ProviderFixture(), search
    )
    snapshot = restored.graph.get_state(
        {"configurable": {"thread_id": f"owner:{request.session_id}"}}
    )
    assert set(snapshot.values["completed"]) == {"research", "summary", "data"}
    assert snapshot.values["answer"].startswith("A grounded")
    restored.delete_thread("owner", str(request.session_id))
    assert store.query("checkpoints") == []
    assert store.query("checkpoint_writes") == []


def test_worker_failure_does_not_collapse_graph(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)

    class BrokenRetrieval(LibraryFixture):
        def retrieve(self, *args):
            raise RuntimeError("simulated unavailable vector service")

    graph = BookGraph(
        settings, SQLiteStore(tmp_path / "state.sqlite3"), BrokenRetrieval(), ProviderFixture()
    )
    request = ChatRequest(
        query="Summarize characters", session_id=uuid.uuid4(), turn_id=uuid.uuid4(), book_id="book"
    )

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    events = asyncio.run(run())
    assert any(event == "trace" and data.get("type") == "worker_failure" for event, data in events)
    assert any(event == "token" for event, _ in events)
    routes = [data for event, data in events if data.get("type") == "agent_route"]
    assert [r["agent"] for r in routes] == [
        "supervisor",
        "research",
        "summary",
        "data",
        "synthesis",
    ]
    assert routes[2]["state"]["completed"] == ["research"]
    assert routes[2]["state"]["errors"]
    assert routes[2]["state"]["available_results"] == []


@pytest.mark.parametrize("query", ["What is the weather in LA?", "Write an unrelated poem."])
def test_off_topic_redirect_has_no_workers_and_persists(tmp_path, query):
    class OffTopic(ProviderFixture):
        async def complete(self, system, prompt, task="extract", **kwargs):
            assert task == "plan"
            assert query in prompt and "workers: []" in system
            return json.dumps({"workers": [], "reason": "Unrelated to books"})

        async def stream(self, *args, **kwargs):
            raise AssertionError("Off-topic responses must not call synthesis models")
            yield

    settings = Settings(_env_file=None, data_dir=tmp_path)
    store = SQLiteStore(tmp_path / "state.sqlite3")
    graph = BookGraph(settings, store, LibraryFixture(), OffTopic())
    request = ChatRequest(
        query=query, session_id=uuid.uuid4(), turn_id=uuid.uuid4(), book_id="book"
    )

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    events = asyncio.run(run())
    assert any("book reading companion" in data.get("text", "") for _, data in events)
    assert not any(data.get("type") in {"agent_input", "mcp_tool_call"} for _, data in events)
    assert any("Off-topic, no worker" in data.get("reason", "") for _, data in events)
    snapshot = graph.graph.get_state({"configurable": {"thread_id": f"owner:{request.session_id}"}})
    assert snapshot.values["completed"] == []
    assert snapshot.values["answer"]


def test_summary_input_is_traced_before_generation_failure(tmp_path):
    class FailedSummary(ProviderFixture):
        async def complete(self, system, prompt, task="extract", **kwargs):
            if task == "plan":
                return json.dumps({"workers": ["summary", "research"], "reason": "Summary first"})
            if task == "summary":
                raise RuntimeError("private provider error")
            return await super().complete(system, prompt, task=task, **kwargs)

    settings = Settings(_env_file=None, data_dir=tmp_path)
    graph = BookGraph(
        settings, SQLiteStore(tmp_path / "state.sqlite3"), LibraryFixture(), FailedSummary()
    )
    request = ChatRequest(
        query="Summarize this chapter",
        session_id=uuid.uuid4(),
        turn_id=uuid.uuid4(),
        book_id="book",
    )

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    events = asyncio.run(run())
    inputs = [d for _, d in events if d.get("type") == "summary_input"]
    assert inputs[0]["maps"] == [{"chapter": 1, "chunk_ids": ["book-s1-t0"]}]
    assert inputs[0]["question"] == request.query
    assert inputs[0]["spoiler_limit"] == 1
    assert "private provider error" not in json.dumps(events)
    assert [d["agent"] for _, d in events if d.get("type") == "agent_route"] == [
        "supervisor",
        "summary",
        "research",
        "synthesis",
    ]


def test_default_application_constructs_without_network(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)
    app = create_app(settings)
    assert isinstance(app.state.library, Library)
    assert isinstance(app.state.engine, BookGraph)


def test_large_evidence_reduction_includes_every_record(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)
    calls = []

    class Reducer(ProviderFixture):
        async def complete(self, system, prompt, **kwargs):
            calls.append(prompt)
            assert len(prompt.encode()) < 60000
            assert kwargs["task"] == "reduce"
            return "Concise evidence [book-s1-t0]."

    graph = BookGraph(
        settings, SQLiteStore(tmp_path / "state.sqlite3"), LibraryFixture(), Reducer()
    )
    records = [f"RECORD-{index}:" + "evidence " * 2000 for index in range(8)]
    result = asyncio.run(graph.reduce_evidence(records, "Explain the characters"))
    assert len(result.encode()) < 60000
    for index in range(8):
        assert sum(f"RECORD-{index}:" in call for call in calls) == 1


def test_explicit_retrieval_cannot_be_omitted_by_planner(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)

    class IncompletePlanner(ProviderFixture):
        async def complete(self, system, prompt, task="extract", **kwargs):
            if task == "plan":
                return json.dumps({"workers": ["data"], "reason": "Concept query"})
            return await super().complete(system, prompt, task=task, **kwargs)

    graph = BookGraph(
        settings, SQLiteStore(tmp_path / "state.sqlite3"), LibraryFixture(), IncompletePlanner()
    )
    request = ChatRequest(
        query="Use semantic retrieval to explain this idea",
        session_id=uuid.uuid4(),
        turn_id=uuid.uuid4(),
        book_id="book",
    )

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    events = asyncio.run(run())
    assert any(event == "trace" and data.get("type") == "rag_retrieval" for event, data in events)


def test_chapter_scope_suppresses_research_and_edition_web_search(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, session_secret="test-" * 10)
    calls = []

    async def search(query, role):
        calls.append(role)
        return {"results": []}

    graph = BookGraph(
        settings,
        SQLiteStore(tmp_path / "state.sqlite3"),
        LibraryFixture(),
        ProviderFixture(),
        search,
    )
    request = ChatRequest(
        query="Research the author, adaptations, and buy hardcover editions",
        session_id=uuid.uuid4(),
        turn_id=uuid.uuid4(),
        book_id="book",
        spoiler_limit=1,
    )

    async def run():
        return [event async for event in graph.stream("owner", request, [])]

    asyncio.run(run())
    assert calls == []
