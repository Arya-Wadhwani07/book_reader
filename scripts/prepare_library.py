import argparse
import asyncio
import gzip
import hashlib
import json

import httpx

from src.config import ROOT, Settings
from src.library import Library
from src.store import make_store


async def prepare(limit):
    settings = Settings()
    library = Library(settings, make_store(settings))
    manifest = json.loads((ROOT / "corpus/manifest.json").read_text())
    snapshot_path = ROOT / "corpus/snapshot.json.gz"
    snapshot = {}
    if snapshot_path.exists():
        snapshot = {
            b["gutenberg_id"]: b
            for b in json.loads(gzip.decompress(snapshot_path.read_bytes()))["books"]
        }
    for item in manifest[:limit]:
        existing = next(
            (b for b in library.list("public") if b.get("gutenberg_id") == item["gutenberg_id"]),
            None,
        )
        if existing:
            print(item["title"], existing["status"], flush=True)
            if existing.get("pipeline_version", 1) < 2:
                existing["status"] = "queued"
                library.store.put("books", existing["id"], existing)
                chunks = library.chunks(existing["id"])
                await asyncio.to_thread(
                    library.vector_store(existing).delete, ids=[c["id"] for c in chunks]
                )
                for fact in library.store.query("book_facts", book_id=existing["id"]):
                    library.store.delete("book_facts", fact["id"])
                await library.ingest(existing["id"])
            elif existing["status"] != "ready":
                await library.ingest(existing["id"])
            continue
        identifier = str(item["gutenberg_id"])
        path = "/".join(identifier[:-1]) + "/" + identifier
        url = f"https://gutenberg.pglaf.org/{path}/{identifier}-0.txt"
        pinned = snapshot.get(item["gutenberg_id"])
        if pinned:
            content = pinned["original"].encode("utf-8")
            if hashlib.sha256(content).hexdigest() != pinned["original_sha256"]:
                raise ValueError("My pinned corpus source checksum does not match.")
        else:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            content = response.content
        book = await library.upload("public", f"{identifier}.txt", content)
        book.update(
            gutenberg_id=item["gutenberg_id"],
            curated_title=item["title"],
            curated_author=item["author"],
            kind=item["kind"],
            source_url=url,
            rights="Project Gutenberg public-domain edition in the United States; original license retained.",
        )
        library.store.put("books", book["id"], book)
        print("Processing", item["title"], flush=True)
        await asyncio.gather(*list(library.tasks))
        print(item["title"], library.store.get("books", book["id"])["status"], flush=True)
        await asyncio.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    asyncio.run(prepare(parser.parse_args().limit))
