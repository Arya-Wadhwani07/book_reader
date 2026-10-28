import asyncio
import hashlib
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import unquote

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, ConfigDict, Field

from src.chats import Chats
from src.config import ROOT, Settings
from src.store import Conflict, make_store

logger = logging.getLogger(__name__)


class TurnCancelled(Exception):
    pass


async def interruptible_stream(stream, store, turn_id):
    pending = None
    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(anext(stream))
            done, _ = await asyncio.wait({pending}, timeout=0.5)
            current = await asyncio.to_thread(store.get, "turns", turn_id)
            if current is None or current.get("cancel_requested"):
                raise TurnCancelled
            if done:
                try:
                    event = pending.result()
                except StopAsyncIteration:
                    return
                pending = None
                yield event
    finally:
        if pending is not None:
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
        await stream.aclose()


class ChatCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(default="New chat", min_length=1, max_length=100)


class BookCategory(BaseModel):
    kind: Literal["Book", "Fiction", "Nonfiction"]


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=6000)
    session_id: uuid.UUID
    turn_id: uuid.UUID
    book_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    depth: Literal["brief", "detailed", "deep"] = "brief"
    spoiler_limit: int | None = Field(default=1, ge=1, le=2000)


def encode_event(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app(settings=None, store=None, engine=None, library=None):
    settings = settings or Settings()
    store = store or make_store(settings)
    chats = Chats(store)
    if library is None:
        from src.library import Library

        library = Library(settings, store)
    if engine is None:
        from src.agents import BookGraph

        engine = BookGraph(settings, store, library)
    signer = URLSafeTimedSerializer(settings.session_secret.get_secret_value(), salt="book-owner")
    index_html = (ROOT / "static/index.html").read_text()
    for asset in ("style.css", "app.js", "stream.js", "markdown.js"):
        version = hashlib.sha256((ROOT / "static" / asset).read_bytes()).hexdigest()[:12]
        index_html = index_html.replace(f"/static/{asset}", f"/static/{asset}?v={version}")
    app = FastAPI(title="Book Companion", docs_url=None, redoc_url=None)
    app.state.store = store
    app.state.engine = engine
    app.state.library = library

    def admit(identity, action, owner_limit, global_limit):
        window = int(time.time() // 3600)
        keys = [("admission", f"{action}:{window}:{scope}") for scope in (identity, "global")]

        def reserve(documents):
            for key, limit in zip(keys, (owner_limit, global_limit), strict=True):
                count = (documents[key] or {}).get("count", 0)
                if count >= limit:
                    raise HTTPException(429, "Hourly usage limit reached. Please try again later.")
                documents[key] = {"count": count + 1, "window": window}
            return documents

        store.mutate_many(keys, reserve)

    @app.middleware("http")
    async def safe_requests(request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            scheme = "https" if settings.app_env == "cloud" else request.url.scheme
            expected = f"{scheme}://{request.url.netloc}"
            if origin and origin != expected:
                return Response("Cross-origin request rejected.", status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def owner(request: Request):
        cookie = request.cookies.get("book_owner", "")
        try:
            value = signer.loads(cookie, max_age=settings.session_days * 86400)
            return str(uuid.UUID(value))
        except (BadSignature, ValueError, TypeError) as error:
            raise HTTPException(
                401, "Open the application to initialize your browser session."
            ) from error

    @app.exception_handler(KeyError)
    async def missing_handler(request, error):
        return Response(
            json.dumps({"detail": "Resource not found."}),
            status_code=404,
            media_type="application/json",
        )

    @app.exception_handler(Conflict)
    async def conflict_handler(request, error):
        return Response(
            json.dumps({"detail": str(error)}), status_code=409, media_type="application/json"
        )

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    @app.get("/readyz")
    def ready(response: Response):
        reasons = engine.readiness()
        response.status_code = 503 if reasons else 200
        return {"ready": not reasons, "reasons": reasons}

    @app.get("/api/bootstrap")
    def bootstrap(request: Request, response: Response):
        try:
            identity = owner(request)
        except HTTPException:
            identity = str(uuid.uuid4())
        response.set_cookie(
            "book_owner",
            signer.dumps(identity),
            httponly=True,
            secure=settings.app_env == "cloud",
            samesite="strict",
            max_age=settings.session_days * 86400,
        )
        return {
            "chats": chats.list(identity),
            "books": library.list(identity),
            "limits": {
                "bytes": settings.max_upload_bytes,
                "pdf_pages": settings.max_pdf_pages,
                "words": settings.max_words,
                "tokens": settings.max_tokens,
            },
            "readiness": engine.readiness(),
        }

    @app.post("/api/chats", status_code=201)
    def new_chat(body: ChatCreate, identity: Annotated[str, Depends(owner)]):
        return chats.create(identity, body.title)

    @app.get("/api/chats")
    def list_chats(identity: Annotated[str, Depends(owner)]):
        return chats.list(identity)

    @app.get("/api/chats/{chat_id}")
    def get_chat(chat_id: uuid.UUID, identity: Annotated[str, Depends(owner)]):
        return {
            "chat": chats.owned(identity, str(chat_id)),
            "turns": chats.messages(identity, str(chat_id)),
        }

    @app.delete("/api/chats/{chat_id}", status_code=204)
    def delete_chat(chat_id: uuid.UUID, identity: Annotated[str, Depends(owner)]):
        chats.delete(identity, str(chat_id))
        engine.delete_thread(identity, str(chat_id))

    @app.post("/api/chats/{chat_id}/cancel")
    def cancel_chat(chat_id: uuid.UUID, identity: Annotated[str, Depends(owner)]):
        chats.cancel(identity, str(chat_id))
        return {"status": "cancellation_requested"}

    @app.get("/api/books")
    def list_books(identity: Annotated[str, Depends(owner)]):
        return library.list(identity)

    @app.get("/api/books/{book_id}")
    def get_book(book_id: str, identity: Annotated[str, Depends(owner)]):
        return library.book(identity, book_id)

    @app.patch("/api/books/{book_id}")
    def set_category(book_id: str, body: BookCategory, identity: Annotated[str, Depends(owner)]):
        return library.set_kind(identity, book_id, body.kind)

    @app.get("/api/books/{book_id}/sources/{chunk_id}")
    def source(book_id: str, chunk_id: str, identity: Annotated[str, Depends(owner)]):
        library.book(identity, book_id)
        return library.chunk(book_id, chunk_id)

    @app.post("/api/books", status_code=202)
    async def upload(request: Request, identity: Annotated[str, Depends(owner)]):
        content = bytearray()
        async for part in request.stream():
            content.extend(part)
            if len(content) > settings.max_upload_bytes:
                raise HTTPException(413, "The file exceeds the 25 MB upload limit.")
        filename = Path(unquote(request.headers.get("x-filename", "book.txt"))).name
        digest = library.content_id(identity, content)
        if await asyncio.to_thread(store.get, "books", digest):
            raise Conflict("This book is already uploaded; use its existing library entry.")
        await asyncio.to_thread(admit, identity, "upload", 10, 80)
        try:
            return await library.upload(identity, filename, bytes(content))
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except RuntimeError:
            raise HTTPException(503, "Ingestion could not start. Retry from the library.") from None

    @app.post("/api/books/{book_id}/retry", status_code=202)
    async def retry_book(book_id: str, identity: Annotated[str, Depends(owner)]):
        await asyncio.to_thread(library.book, identity, book_id)
        await asyncio.to_thread(admit, identity, "upload", 10, 80)
        try:
            return await library.retry(identity, book_id)
        except RuntimeError:
            raise HTTPException(503, "Ingestion could not restart. Please retry later.") from None

    @app.post("/api/chat")
    async def chat(body: ChatRequest, identity: Annotated[str, Depends(owner)]):
        book = await asyncio.to_thread(library.book, identity, body.book_id)
        if book["status"] != "ready":
            raise HTTPException(409, "This book is still processing.")
        if engine.readiness():
            raise HTTPException(503, "Provider and retrieval configuration is not ready.")
        await asyncio.to_thread(chats.owned, identity, str(body.session_id))
        await asyncio.to_thread(admit, identity, "chat", 30, 600)
        turn = await asyncio.to_thread(chats.begin, identity, body)
        history = await asyncio.to_thread(chats.messages, identity, str(body.session_id))
        history = [message for message in history if message["status"] == "complete"]

        async def response_stream():
            started = time.monotonic()
            status = "interrupted"
            saved = False
            try:
                async with asyncio.timeout(settings.response_timeout_seconds):
                    async for event, payload in interruptible_stream(
                        engine.stream(identity, body, history), store, turn["id"]
                    ):
                        if event == "token":
                            turn["answer"] += payload["text"]
                            turn.setdefault("ttft_seconds", time.monotonic() - started)
                        else:
                            turn["events"].append({"event": event, "data": payload})
                        yield encode_event(event, payload)
                        if event == "error":
                            raise RuntimeError("The agent returned a terminal error.")
                if not turn["answer"].strip():
                    raise RuntimeError("The agent returned no answer.")
                status = "complete"
                turn["total_seconds"] = time.monotonic() - started
                status = await asyncio.to_thread(chats.finish, turn, status)
                saved = True
                yield encode_event(
                    "done",
                    {
                        "success": status == "complete",
                        "status": status,
                        "total_seconds": turn["total_seconds"],
                    },
                )
            except TurnCancelled:
                status = "cancelled"
                yield encode_event("done", {"success": False, "status": status})
            except Exception as error:
                status = "failed"
                logger.warning("Turn failed: %s", type(error).__name__)
                yield encode_event(
                    "error", {"message": "The response could not complete. Please retry."}
                )
                yield encode_event("done", {"success": False, "status": status})
            finally:
                if not saved:
                    try:
                        await asyncio.shield(asyncio.to_thread(chats.finish, turn, status))
                    except Exception as error:
                        logger.warning("Turn persistence failed: %s", type(error).__name__)

        return StreamingResponse(
            response_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @app.get("/")
    def index():
        return HTMLResponse(index_html, headers={"Cache-Control": "no-cache"})

    return app
