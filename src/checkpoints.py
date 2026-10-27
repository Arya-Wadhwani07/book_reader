import asyncio
import base64
import hashlib
import json

from langgraph.checkpoint.base import WRITES_IDX_MAP, BaseCheckpointSaver, CheckpointTuple


class DurableSaver(BaseCheckpointSaver):
    def __init__(self, store):
        super().__init__()
        self.store = store

    def encode(self, value):
        kind, data = self.serde.dumps_typed(value)
        return [kind, base64.b64encode(data).decode()]

    def decode(self, value):
        return self.serde.loads_typed((value[0], base64.b64decode(value[1])))

    @staticmethod
    def key(config):
        return hashlib.sha256(
            json.dumps(
                {
                    key: config["configurable"].get(key, "")
                    for key in ("thread_id", "checkpoint_ns", "checkpoint_id")
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

    def put(self, config, checkpoint, metadata, new_versions):
        values = config["configurable"]
        updated = {
            "configurable": {
                "thread_id": values["thread_id"],
                "checkpoint_ns": values.get("checkpoint_ns", ""),
                "checkpoint_id": checkpoint["id"],
            }
        }
        self.store.put(
            "checkpoints",
            self.key(updated),
            {
                "id": self.key(updated),
                "thread_id": values["thread_id"],
                "config": updated,
                "checkpoint": self.encode(checkpoint),
                "metadata": self.encode(metadata),
                "parent": {
                    "configurable": {
                        key: values.get(key, "")
                        for key in ("thread_id", "checkpoint_ns", "checkpoint_id")
                    }
                }
                if values.get("checkpoint_id")
                else None,
            },
        )
        return updated

    def get_tuple(self, config):
        values = config["configurable"]
        records = self.store.query("checkpoints", thread_id=values["thread_id"])
        records = [
            r
            for r in records
            if r["config"]["configurable"]["checkpoint_ns"] == values.get("checkpoint_ns", "")
            and (
                not values.get("checkpoint_id")
                or r["config"]["configurable"]["checkpoint_id"] == values["checkpoint_id"]
            )
        ]
        if not records:
            return None
        record = max(records, key=lambda r: r["config"]["configurable"]["checkpoint_id"])
        writes = self.store.query("checkpoint_writes", checkpoint_key=record["id"])
        writes.sort(key=lambda w: (w["task_path"], w["task_id"], w["index"]))
        return CheckpointTuple(
            record["config"],
            self.decode(record["checkpoint"]),
            self.decode(record["metadata"]),
            record["parent"],
            [(w["task_id"], w["channel"], self.decode(w["value"])) for w in writes],
        )

    def put_writes(self, config, writes, task_id, task_path=""):
        key = self.key(config)
        for index, (channel, value) in enumerate(writes):
            index = WRITES_IDX_MAP.get(channel, index)
            identifier = hashlib.sha256(f"{key}:{task_id}:{index}".encode()).hexdigest()
            document = {
                "id": identifier,
                "thread_id": config["configurable"]["thread_id"],
                "checkpoint_key": key,
                "task_id": task_id,
                "task_path": task_path,
                "index": index,
                "channel": channel,
                "value": self.encode(value),
            }
            self.store.mutate(
                "checkpoint_writes",
                identifier,
                lambda old, document=document, index=index: old if old and index >= 0 else document,
            )

    def list(self, config, *, filter=None, before=None, limit=None):
        records = self.store.query(
            "checkpoints", **({"thread_id": config["configurable"]["thread_id"]} if config else {})
        )
        records.sort(key=lambda r: r["config"]["configurable"]["checkpoint_id"], reverse=True)
        count = 0
        for record in records:
            if config and record["config"]["configurable"]["checkpoint_ns"] != config[
                "configurable"
            ].get("checkpoint_ns", ""):
                continue
            if (
                before
                and record["config"]["configurable"]["checkpoint_id"]
                >= before["configurable"]["checkpoint_id"]
            ):
                continue
            metadata = self.decode(record["metadata"])
            if filter and any(metadata.get(k) != v for k, v in filter.items()):
                continue
            if limit is not None and count >= limit:
                break
            yield self.get_tuple(record["config"])
            count += 1

    def delete_thread(self, thread_id):
        for collection in ("checkpoints", "checkpoint_writes"):
            for record in self.store.query(collection, thread_id=thread_id):
                self.store.delete(collection, record["id"])

    async def aget_tuple(self, config):
        return await asyncio.to_thread(self.get_tuple, config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config, writes, task_id, task_path=""):
        await asyncio.to_thread(self.put_writes, config, writes, task_id, task_path)

    async def alist(self, config, *, filter=None, before=None, limit=None):
        records = await asyncio.to_thread(
            lambda: list(self.list(config, filter=filter, before=before, limit=limit))
        )
        for record in records:
            yield record

    async def adelete_thread(self, thread_id):
        await asyncio.to_thread(self.delete_thread, thread_id)
