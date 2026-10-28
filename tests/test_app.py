import json
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import ChatRequest, create_app
from src.chats import Chats
from src.config import Settings
from src.store import Conflict, SQLiteStore


class LibraryFixture:
    def list(self, owner):
        return [{"id": "public-book", "status": "ready"}]

    def book(self, owner, book_id):
        if book_id != "public-book":
            raise KeyError(book_id)
        return self.list(owner)[0]


class EngineFixture:
    def __init__(self):
        self.histories = []
        self.deleted = []

    def readiness(self):
        return []

    def delete_thread(self, owner, chat_id):
        self.deleted.append((owner, chat_id))

    async def stream(self, owner, body, history):
        self.histories.append(history)
        yield "token", {"text": "A test response."}


@pytest.fixture
def setup(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    store = SQLiteStore(tmp_path / "state.sqlite3")
    engine = EngineFixture()
    app = create_app(settings, store, engine, LibraryFixture())
    with TestClient(app) as client:
        client.get("/api/bootstrap")
        yield client, store, engine, settings


def turn(chat_id, **updates):
    return dict(
        query="Describe the opening",
        session_id=chat_id,
        turn_id=str(uuid.uuid4()),
        book_id="public-book",
        **updates,
    )


def test_stream_persists_and_restores_after_application_restart(setup):
    client, store, engine, settings = setup
    chat = client.post("/api/chats", json={}).json()
    response = client.post("/api/chat", json=turn(chat["id"]))
    assert response.status_code == 200
    assert '"success": true' in response.text
    restarted = create_app(settings, SQLiteStore(store.path), engine, LibraryFixture())
    with TestClient(restarted) as restored:
        restored.cookies.update(client.cookies)
        result = restored.get(f"/api/chats/{chat['id']}").json()
    assert result["turns"][0]["answer"] == "A test response."
    assert result["turns"][0]["status"] == "complete"


def test_another_browser_cannot_read_or_delete_chat(setup):
    client, _, _, _ = setup
    chat = client.post("/api/chats", json={}).json()
    client.cookies.clear()
    client.get("/api/bootstrap")
    assert client.get(f"/api/chats/{chat['id']}").status_code == 404
    assert client.delete(f"/api/chats/{chat['id']}").status_code == 404
    assert client.get("/api/chats").json() == []


def test_chats_do_not_share_history_or_duplicate_turns(setup):
    client, _, engine, _ = setup
    first = client.post("/api/chats", json={}).json()["id"]
    second = client.post("/api/chats", json={}).json()["id"]
    body = turn(first)
    assert client.post("/api/chat", json=body).status_code == 200
    assert client.post("/api/chat", json=body).status_code == 409
    assert client.post("/api/chat", json=turn(second)).status_code == 200
    assert all(t["chat_id"] == second for t in engine.histories[-1])
    assert len(client.get("/api/chats").json()) == 2


def test_missing_cookie_cross_origin_and_invalid_input(setup):
    client, _, _, _ = setup
    assert (
        client.post("/api/chats", json={}, headers={"Origin": "https://evil.test"}).status_code
        == 403
    )
    assert client.post("/api/chat", json={}).status_code == 422
    client.cookies.clear()
    assert client.get("/api/chats").status_code == 401


def test_concurrent_chat_requests_have_one_winner(setup):
    _, store, _, _ = setup
    chats = Chats(store)
    chat = chats.create("owner")

    def reserve(_):
        try:
            chats.begin("owner", ChatRequest(**turn(chat["id"])))
            return True
        except Conflict:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(reserve, range(4))) == 1


def test_transaction_rolls_back_on_failure(setup):
    _, store, _, _ = setup
    store.put("counter", "one", {"value": 1})

    def fail(document):
        document["value"] = 2
        raise ValueError("intentional")

    with pytest.raises(ValueError, match="intentional"):
        store.mutate("counter", "one", fail)
    assert store.get("counter", "one") == {"value": 1}


def test_offline_network_is_blocked():
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match="blocked"):
            connection.connect(("127.0.0.1", 443))


def test_offline_filesystem_blocks_outside_writes():
    with pytest.raises(PermissionError, match="outside Assignment 2"):
        Path("/tmp/book-companion-forbidden-test.txt").write_text("blocked")


@pytest.mark.parametrize("budget", [2.51, 5, -1, 0])
def test_anthropic_budget_cannot_exceed_authorization(budget):
    with pytest.raises(ValueError):
        Settings(_env_file=None, generation_budget_usd=budget)


def test_configuration_rejects_outside_storage():
    with pytest.raises(ValueError, match="inside"):
        Settings(_env_file=None, data_dir="/tmp/book-companion")


def test_health_and_static_assets(setup):
    client, _, _, _ = setup
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json()["ready"]
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert "Content-Security-Policy" in client.get("/").headers
    assert json.loads(client.get("/api/bootstrap").text)["limits"]["pdf_pages"] == 500


def test_cloud_https_origin_behind_terminating_proxy(tmp_path):
    settings = Settings(
        _env_file=None,
        app_env="cloud",
        state_backend="firestore",
        gcs_bucket="test",
        data_dir=tmp_path,
    )
    app = create_app(
        settings, SQLiteStore(tmp_path / "state.sqlite3"), EngineFixture(), LibraryFixture()
    )
    with TestClient(app, base_url="http://cloud.example") as client:
        # I check the origin gate before authentication; a permitted request reaches 401.
        assert (
            client.post(
                "/api/chats", json={}, headers={"Origin": "https://cloud.example"}
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/chats", json={}, headers={"Origin": "https://attacker.example"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/chats", json={}, headers={"Origin": "http://cloud.example"}
            ).status_code
            == 403
        )


def test_html_versions_assets_to_prevent_mixed_revisions(setup):
    import hashlib

    from src.config import ROOT

    client, _, _, _ = setup
    response = client.get("/")
    assert response.headers["cache-control"] == "no-cache"
    for asset in ("style.css", "app.js", "stream.js", "markdown.js"):
        digest = hashlib.sha256((ROOT / "static" / asset).read_bytes()).hexdigest()[:12]
        assert f"/static/{asset}?v={digest}" in response.text
