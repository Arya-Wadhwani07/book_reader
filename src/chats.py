import time
import uuid

from src.store import Conflict


class Chats:
    def __init__(self, store):
        self.store = store

    def owned(self, owner, chat_id):
        chat = self.store.get("chats", chat_id)
        if not chat or chat["owner_id"] != owner or chat.get("deleting"):
            raise KeyError("Chat not found.")
        return chat

    def create(self, owner, title="New chat"):
        chat = {
            "id": str(uuid.uuid4()),
            "owner_id": owner,
            "title": title[:100],
            "created_at": time.time(),
            "updated_at": time.time(),
            "book_id": None,
            "depth": "brief",
            "spoiler_limit": 1,
            "active_turn": None,
            "lease_until": 0,
        }
        self.store.put("chats", chat["id"], chat)
        return chat

    def list(self, owner):
        return sorted(
            self.store.query("chats", owner_id=owner),
            key=lambda c: c["updated_at"],
            reverse=True,
        )

    def messages(self, owner, chat_id):
        self.owned(owner, chat_id)
        self.recover_expired(owner, chat_id)
        return sorted(self.store.query("turns", chat_id=chat_id), key=lambda t: t["started_at"])

    def recover_expired(self, owner, chat_id):
        chat = self.owned(owner, chat_id)
        if not chat["active_turn"] or chat["lease_until"] > time.time():
            return
        chat_key = ("chats", chat_id)
        turn_key = ("turns", f"{chat_id}:{chat['active_turn']}")

        def recover(documents):
            current, turn = documents[chat_key], documents[turn_key]
            if (
                current
                and current["owner_id"] == owner
                and current["active_turn"] == chat["active_turn"]
                and current["lease_until"] <= time.time()
            ):
                if turn and turn["status"] == "running":
                    turn.update(status="interrupted", finished_at=time.time())
                current.update(active_turn=None, lease_until=0)
            return documents

        self.store.mutate_many([chat_key, turn_key], recover)

    def begin(self, owner, request):
        chat_id, turn_id = str(request.session_id), str(request.turn_id)
        key = f"{chat_id}:{turn_id}"
        self.owned(owner, chat_id)
        self.recover_expired(owner, chat_id)
        if self.store.get("turns", key):
            raise Conflict("This turn already exists; reload the chat instead of paying twice.")

        def reserve(chat):
            if not chat or chat["owner_id"] != owner or chat.get("deleting"):
                raise KeyError("Chat not found.")
            if chat["active_turn"] and chat["lease_until"] > time.time():
                raise Conflict("A response is already running in this chat.")
            if chat["book_id"] and chat["book_id"] != request.book_id:
                raise Conflict("Start a new chat for a different book to keep contexts separate.")
            chat.update(
                active_turn=turn_id,
                lease_until=time.time() + 330,
                book_id=request.book_id,
                depth=request.depth,
                spoiler_limit=request.spoiler_limit,
                updated_at=time.time(),
            )
            if chat["title"] == "New chat":
                chat["title"] = request.query[:70]
            return chat

        turn = {
            "id": key,
            "turn_id": turn_id,
            "chat_id": chat_id,
            "owner_id": owner,
            "query": request.query,
            "book_id": request.book_id,
            "spoiler_limit": request.spoiler_limit,
            "answer": "",
            "events": [],
            "status": "running",
            "started_at": time.time(),
            "cancel_requested": False,
        }
        chat_key, turn_key = ("chats", chat_id), ("turns", key)

        def reserve_both(documents):
            if documents[turn_key] is not None:
                raise Conflict("This turn already exists; reload the chat instead of paying twice.")
            documents[chat_key] = reserve(documents[chat_key])
            documents[turn_key] = turn
            return documents

        self.store.mutate_many([chat_key, turn_key], reserve_both)
        return turn

    def finish(self, turn, status):
        chat_key, turn_key = ("chats", turn["chat_id"]), ("turns", turn["id"])

        def complete(documents):
            current, chat = documents[turn_key], documents[chat_key]
            if current is None:
                raise KeyError("Turn no longer exists.")
            cancelled = current.get("cancel_requested", False)
            final_status = (
                "cancelled" if status in {"complete", "interrupted"} and cancelled else status
            )
            documents[turn_key] = turn | {
                "cancel_requested": cancelled,
                "status": final_status,
                "finished_at": time.time(),
            }
            if chat and chat["active_turn"] == turn["turn_id"]:
                chat.update(active_turn=None, lease_until=0, updated_at=time.time())
            return documents

        result = self.store.mutate_many([chat_key, turn_key], complete)
        turn.update(result[turn_key])
        return turn["status"]

    def cancel(self, owner, chat_id):
        chat = self.owned(owner, chat_id)
        if chat["active_turn"]:
            key = f"{chat_id}:{chat['active_turn']}"

            def mark(turn):
                if turn:
                    turn["cancel_requested"] = True
                return turn

            self.store.mutate("turns", key, mark)

    def delete(self, owner, chat_id):
        def reserve_delete(chat):
            if not chat or chat["owner_id"] != owner:
                raise KeyError("Chat not found.")
            if chat["active_turn"] and chat["lease_until"] > time.time():
                raise Conflict("Stop the active response before deleting this chat.")
            chat["deleting"] = True
            return chat

        self.store.mutate("chats", chat_id, reserve_delete)
        for turn in self.store.query("turns", chat_id=chat_id):
            self.store.delete("turns", turn["id"])
        self.store.delete("chats", chat_id)
