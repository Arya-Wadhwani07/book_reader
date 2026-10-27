"""I measure first-hit and warm end-to-end latency on an idle tagged revision."""

import argparse
import io
import json
import time
import uuid

import httpx

from scripts.verify_release import read_events, verify_stream
from src.config import ROOT


def measure(url):
    records = []
    for label in ("first_hit_after_idle", "warm"):
        started = time.monotonic()
        with httpx.Client(base_url=url, timeout=300, headers={"Origin": url.rstrip("/")}) as client:
            client.get("/api/bootstrap").raise_for_status()
            bootstrap_seconds = time.monotonic() - started
            book = next(b for b in client.get("/api/books").json() if b.get("gutenberg_id") == 11)
            chat = client.post("/api/chats", json={}).json()
            raw, first = bytearray(), None
            query_started = time.monotonic()
            with client.stream(
                "POST",
                "/api/chat",
                json={
                    "query": "Use semantic retrieval: why does Alice follow the White Rabbit? Answer in two sentences with citations.",
                    "session_id": chat["id"],
                    "turn_id": str(uuid.uuid4()),
                    "book_id": book["id"],
                    "depth": "brief",
                    "spoiler_limit": 1,
                },
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line == "event: token" and first is None:
                        first = time.monotonic()
                    raw.extend((line + "\n").encode())
            verify_stream(io.BytesIO(raw))
            events = list(read_events(io.BytesIO(raw)))
            records.append(
                {
                    "label": label,
                    "bootstrap_seconds": bootstrap_seconds,
                    "end_to_end_ttft_seconds": first - started,
                    "query_ttft_seconds": first - query_started,
                    "query_total_seconds": time.monotonic() - query_started,
                    "traces": [data for event, data in events if event == "trace"],
                }
            )
            print(label, records[-1]["end_to_end_ttft_seconds"], flush=True)
    (ROOT / "reports/cold_warm.json").write_text(
        json.dumps({"url": url, "measurements": records}, indent=2)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    measure(parser.parse_args().url)
