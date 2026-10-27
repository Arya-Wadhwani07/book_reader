import asyncio
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient
from test_app import EngineFixture, LibraryFixture, turn

from src.app import ChatRequest, create_app
from src.artifacts import Artifacts
from src.budget import Budget, BudgetExceeded
from src.chats import Chats
from src.config import Settings
from src.store import SQLiteStore


@pytest.fixture
def components(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    return settings, SQLiteStore(tmp_path / "state.sqlite3")


@pytest.mark.parametrize("query", [" ", "\n\t", "\u2003"])
def test_blank_queries_rejected(query):
    with pytest.raises(ValueError):
        ChatRequest(**(turn("00000000-0000-0000-0000-000000000001") | {"query": query}))


@pytest.mark.parametrize("mode", ["empty", "error_event", "transport_error"])
def test_failed_stream_never_reports_success(components, mode):
    settings, store = components

    class BrokenEngine(EngineFixture):
        async def stream(self, owner, body, history):
            if mode == "error_event":
                yield "error", {"message": "Worker failed"}
            if mode == "transport_error":
                raise httpx.ReadError("fake transport failure")

    app = create_app(settings, store, BrokenEngine(), LibraryFixture())
    with TestClient(app) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        response = client.post("/api/chat", json=turn(chat_id))
        assert '"success": true' not in response.text
        assert '"success": false' in response.text
        stored = client.get(f"/api/chats/{chat_id}").json()
        assert stored["turns"][0]["status"] == "failed"
        assert stored["chat"]["active_turn"] is None


def test_history_excludes_current_and_failed_turns(components):
    settings, store = components
    engine = EngineFixture()
    app = create_app(settings, store, engine, LibraryFixture())
    with TestClient(app) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        first = turn(chat_id)
        client.post("/api/chat", json=first)
        saved = store.get("turns", f"{chat_id}:{first['turn_id']}")
        saved["status"] = "failed"
        store.put("turns", saved["id"], saved)
        client.post("/api/chat", json=turn(chat_id))
        assert engine.histories[-1] == []


def test_artifact_symlink_cannot_escape_its_storage(components, tmp_path):
    settings, _ = components
    artifacts = Artifacts(settings)
    artifacts.directory.mkdir(parents=True)
    destination = tmp_path / "unrelated"
    destination.mkdir()
    (artifacts.directory / "escape").symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="path"):
        artifacts.put("escape/modified.txt", b"must not be written")
    assert not (destination / "modified.txt").exists()


def test_cancellation_flag_survives_finish(components):
    _, store = components
    chats = Chats(store)
    chat = chats.create("owner")
    current = chats.begin("owner", ChatRequest(**turn(chat["id"])))
    chats.cancel("owner", chat["id"])
    chats.finish(current, "cancelled")
    assert store.get("turns", current["id"])["cancel_requested"] is True


def test_cancellation_interrupts_silent_engine(components):
    from src.app import TurnCancelled, interruptible_stream

    _, store = components
    store.put("turns", "silent", {"cancel_requested": False})
    closed = []

    async def silent():
        try:
            await asyncio.sleep(60)
            yield "token", {"text": "Too late"}
        finally:
            closed.append(True)

    async def run():
        stream = interruptible_stream(silent(), store, "silent")
        pending = asyncio.create_task(anext(stream))
        await asyncio.sleep(0.05)
        store.put("turns", "silent", {"cancel_requested": True})
        with pytest.raises(TurnCancelled):
            await asyncio.wait_for(pending, timeout=2)

    asyncio.run(run())
    assert closed == [True]


def test_storage_failure_never_emits_success(components, monkeypatch):
    settings, store = components
    original = Chats.finish

    def fail_completion(self, current, status):
        if status == "complete":
            raise RuntimeError("private storage details")
        return original(self, current, status)

    monkeypatch.setattr(Chats, "finish", fail_completion)
    with TestClient(create_app(settings, store, EngineFixture(), LibraryFixture())) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        response = client.post("/api/chat", json=turn(chat_id))
        assert '"success": true' not in response.text
        assert '"success": false' in response.text
        assert "private storage" not in response.text
        assert client.get(f"/api/chats/{chat_id}").json()["turns"][0]["status"] == "failed"


def test_expired_process_lease_recovers_on_restart(components):
    _, store = components
    chats = Chats(store)
    chat = chats.create("reader")
    current = chats.begin("reader", ChatRequest(**turn(chat["id"])))
    store.mutate("chats", chat["id"], lambda c: c | {"lease_until": 0})
    restarted = Chats(SQLiteStore(store.path))
    assert restarted.messages("reader", chat["id"])[0]["status"] == "interrupted"
    assert restarted.owned("reader", chat["id"])["active_turn"] is None
    with pytest.raises(Exception, match="already exists"):
        restarted.begin(
            "reader", ChatRequest(**(turn(chat["id"]) | {"turn_id": current["turn_id"]}))
        )


def test_stress_atomic_store_updates(components):
    _, store = components
    store.put("stress", "counter", {"value": 0})

    def increment(_):
        store.mutate("stress", "counter", lambda value: {"value": value["value"] + 1})

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(increment, range(1000)))
    assert store.get("stress", "counter")["value"] == 1000


def test_stress_100_isolated_conversations(components):
    _, store = components
    chats = Chats(store)

    def conversation(index):
        owner = f"owner-{index}"
        chat = chats.create(owner)
        for _ in range(3):
            current = chats.begin(owner, ChatRequest(**turn(chat["id"])))
            current["answer"] = owner
            chats.finish(current, "complete")
        assert [c["id"] for c in chats.list(owner)] == [chat["id"]]
        assert len(chats.messages(owner, chat["id"])) == 3
        assert all(t["answer"] == owner for t in chats.messages(owner, chat["id"]))
        return chat["id"]

    with ThreadPoolExecutor(max_workers=16) as pool:
        ids = list(pool.map(conversation, range(100)))
    assert len(set(ids)) == 100


def test_stress_paid_request_reservations(components):
    settings, store = components
    budget = Budget(store, settings)

    def reserve(_):
        try:
            return budget.reserve("anthropic", "0.025")
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=16) as pool:
        reservations = list(pool.map(reserve, range(300)))
    assert sum(value is not None for value in reservations) == 100
    assert sum(store.get("budgets", "anthropic")["reservations"].values()) == 2_500_000


def test_partial_answer_survives_expected_failure(components):
    settings, store = components

    class PartialEngine(EngineFixture):
        async def stream(self, owner, body, history):
            yield "token", {"text": "A partial answer"}
            await asyncio.sleep(0)
            raise RuntimeError("simulated worker failure")

    with TestClient(create_app(settings, store, PartialEngine(), LibraryFixture())) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        response = client.post("/api/chat", json=turn(chat_id))
        assert '"success": false' in response.text
        result = client.get(f"/api/chats/{chat_id}").json()
        assert result["turns"][0]["answer"] == "A partial answer"
        assert result["turns"][0]["status"] == "failed"


def test_stress_50_concurrent_api_sessions(components, record_testsuite_property):
    import statistics
    import time

    settings, store = components
    engine = EngineFixture()
    app = create_app(settings, store, engine, LibraryFixture())
    durations = []

    async def browser(index):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/bootstrap")
            assert response.status_code == 200
            chat = (await client.post("/api/chats", json={"title": f"Browser {index}"})).json()
            for _ in range(3):
                started = time.perf_counter()
                response = await client.post("/api/chat", json=turn(chat["id"]))
                durations.append(time.perf_counter() - started)
                assert response.status_code == 200
                assert '"success": true' in response.text
            chats = (await client.get("/api/chats")).json()
            assert [c["id"] for c in chats] == [chat["id"]]
            result = (await client.get(f"/api/chats/{chat['id']}")).json()
            assert len(result["turns"]) == 3
            assert all(t["status"] == "complete" for t in result["turns"])

    async def run():
        await asyncio.gather(*(browser(index) for index in range(50)))

    asyncio.run(run())
    record_testsuite_property("fixture_stream_requests", len(durations))
    record_testsuite_property(
        "fixture_stream_median_seconds", round(statistics.median(durations), 4)
    )
    record_testsuite_property("fixture_stream_p95_seconds", round(sorted(durations)[142], 4))
    assert len(engine.histories) == 150


@pytest.mark.parametrize(
    "method,path", [("get", "/api/chats"), ("post", "/api/chats"), ("get", "/api/books")]
)
def test_tampered_cookie_denied(components, method, path):
    settings, store = components
    with TestClient(create_app(settings, store, EngineFixture(), LibraryFixture())) as client:
        client.cookies.set("book_owner", "forged.owner.signature")
        response = getattr(client, method)(path, **({"json": {}} if method == "post" else {}))
        assert response.status_code == 401


@pytest.mark.parametrize(
    "changes",
    [
        {"query": "x" * 6001},
        {"depth": "unlimited"},
        {"spoiler_limit": 0},
        {"spoiler_limit": 2001},
        {"book_id": "../another-book"},
        {"turn_id": "invalid"},
    ],
)
def test_invalid_request_never_invokes_model(components, changes):
    settings, store = components
    engine = EngineFixture()
    with TestClient(create_app(settings, store, engine, LibraryFixture())) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        response = client.post("/api/chat", json=turn(chat_id) | changes)
        assert response.status_code == 422
        assert engine.histories == []
        assert store.query("turns", chat_id=chat_id) == []


def test_oversized_upload_rejected_before_ingestion(components):
    settings, store = components
    settings.max_upload_bytes = 100
    with TestClient(create_app(settings, store, EngineFixture(), LibraryFixture())) as client:
        client.get("/api/bootstrap")
        response = client.post("/api/books", content=b"x" * 101, headers={"X-Filename": "book.txt"})
        assert response.status_code == 413


def test_hourly_admission_rejects_before_model_execution(components):
    settings, store = components
    engine = EngineFixture()
    with TestClient(create_app(settings, store, engine, LibraryFixture())) as client:
        client.get("/api/bootstrap")
        chat_id = client.post("/api/chats", json={}).json()["id"]
        for _ in range(30):
            assert '"success": true' in client.post("/api/chat", json=turn(chat_id)).text
        histories = len(engine.histories)
        assert client.post("/api/chat", json=turn(chat_id)).status_code == 429
        assert len(engine.histories) == histories
        assert len(client.get(f"/api/chats/{chat_id}").json()["turns"]) == 30
