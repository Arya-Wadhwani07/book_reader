import json
import sqlite3
from contextlib import contextmanager


class Conflict(Exception):
    pass


class SQLiteStore:
    """I use a transactional local store for development and isolated tests."""

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS documents "
                "(collection TEXT, id TEXT, body TEXT, PRIMARY KEY(collection,id))"
            )

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, collection, key):
        with self.connection() as db:
            row = db.execute(
                "SELECT body FROM documents WHERE collection=? AND id=?", (collection, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def query(self, collection, **filters):
        with self.connection() as db:
            rows = db.execute(
                "SELECT body FROM documents WHERE collection=?", (collection,)
            ).fetchall()
        documents = [json.loads(row[0]) for row in rows]
        return [d for d in documents if all(d.get(k) == v for k, v in filters.items())]

    def put(self, collection, key, document):
        self.mutate(collection, key, lambda _: document)

    def mutate(self, collection, key, update):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT body FROM documents WHERE collection=? AND id=?", (collection, key)
            ).fetchone()
            result = update(json.loads(row[0]) if row else None)
            if result is None:
                db.execute("DELETE FROM documents WHERE collection=? AND id=?", (collection, key))
            else:
                db.execute(
                    "INSERT INTO documents VALUES(?,?,?) "
                    "ON CONFLICT(collection,id) DO UPDATE SET body=excluded.body",
                    (collection, key, json.dumps(result)),
                )
        return result

    def delete(self, collection, key):
        self.mutate(collection, key, lambda _: None)

    def mutate_many(self, keys, update):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            documents = {}
            for key in keys:
                row = db.execute(
                    "SELECT body FROM documents WHERE collection=? AND id=?", key
                ).fetchone()
                documents[key] = json.loads(row[0]) if row else None
            result = update(documents)
            for (collection, key), document in result.items():
                if document is None:
                    db.execute(
                        "DELETE FROM documents WHERE collection=? AND id=?", (collection, key)
                    )
                else:
                    db.execute(
                        "INSERT INTO documents VALUES(?,?,?) ON CONFLICT(collection,id) DO UPDATE SET body=excluded.body",
                        (collection, key, json.dumps(document)),
                    )
        return result


class FirestoreStore:
    """I keep cloud state external and apply changes inside Firestore transactions."""

    def __init__(self, project):
        from google.cloud import firestore

        self.client = firestore.Client(project=project)

    def get(self, collection, key):
        return self.client.collection(f"book_companion_{collection}").document(key).get().to_dict()

    def query(self, collection, **filters):
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = self.client.collection(f"book_companion_{collection}")
        for field, value in filters.items():
            query = query.where(filter=FieldFilter(field, "==", value))
        return [document.to_dict() for document in query.stream()]

    def put(self, collection, key, document):
        self.client.collection(f"book_companion_{collection}").document(key).set(document)

    def mutate(self, collection, key, update):
        from google.cloud import firestore

        reference = self.client.collection(f"book_companion_{collection}").document(key)

        @firestore.transactional
        def apply(transaction):
            result = update(reference.get(transaction=transaction).to_dict())
            if result is None:
                transaction.delete(reference)
            else:
                transaction.set(reference, result)
            return result

        return apply(self.client.transaction())

    def delete(self, collection, key):
        self.client.collection(f"book_companion_{collection}").document(key).delete()

    def mutate_many(self, keys, update):
        from google.cloud import firestore

        references = {
            key: self.client.collection(f"book_companion_{key[0]}").document(key[1]) for key in keys
        }

        @firestore.transactional
        def apply(transaction):
            documents = {
                key: ref.get(transaction=transaction).to_dict() for key, ref in references.items()
            }
            result = update(documents)
            for key, document in result.items():
                if document is None:
                    transaction.delete(references[key])
                else:
                    transaction.set(references[key], document)
            return result

        return apply(self.client.transaction())


def make_store(settings):
    if settings.state_backend == "firestore":
        return FirestoreStore(settings.gcp_project_id)
    return SQLiteStore(settings.data_dir / "state.sqlite3")
