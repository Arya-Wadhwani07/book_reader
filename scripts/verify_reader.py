"""I exercise all specialists and preserve a private probe for cross-revision recovery."""

import argparse
import io
import json
import time
import uuid

import httpx

from scripts.verify_release import read_events
from src.config import ROOT


def verify(url, restore=False):
    private = ROOT / ".cache/recovery_probe.json"
    with httpx.Client(base_url=url, timeout=300, headers={"Origin": url.rstrip("/")}) as client:
        if restore:
            probe = json.loads(private.read_text())
            client.cookies.update(probe["cookies"])
            result = client.get(f"/api/chats/{probe['chat_id']}")
            result.raise_for_status()
            assert result.json()["turns"][0]["answer"] == probe["answer"]
            assert result.json()["turns"][0]["status"] == "complete"
            (ROOT / "reports/recovery.json").write_text(
                json.dumps(
                    {
                        "passed": True,
                        "from_url": probe["url"],
                        "to_url": url,
                        "turn_id": probe["turn_id"],
                    },
                    indent=2,
                )
            )
            print("Saved answer recovered through another revision URL.", flush=True)
            return
        client.get("/api/bootstrap").raise_for_status()
        book = next(b for b in client.get("/api/books").json() if b.get("gutenberg_id") == 11)
        chat = client.post("/api/chats", json={}).json()
        turn_id = str(uuid.uuid4())
        started, first, raw = time.monotonic(), None, bytearray()
        with client.stream(
            "POST",
            "/api/chat",
            json={
                "session_id": chat["id"],
                "turn_id": turn_id,
                "book_id": book["id"],
                "query": "Summarize this book's chronological story, explain Alice's character development, and use semantic retrieval to support why she follows the White Rabbit. Use Summary, Data, and Research specialists.",
                "depth": "deep",
                "spoiler_limit": None,
            },
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line == "event: token" and first is None:
                    first = time.monotonic() - started
                raw.extend((line + "\n").encode())
        events = list(read_events(io.BytesIO(raw)))
        assert events[-1][0] == "done" and events[-1][1]["success"]
        traces = [data for event, data in events if event == "trace"]
        assert not any(t.get("type") == "worker_failure" for t in traces)
        assert {"research", "summary", "data"} <= {
            t.get("agent") for t in traces if t.get("type") == "agent_route"
        }
        assert {"openai", "anthropic"} <= {
            t.get("provider") for t in traces if t.get("type") == "llm_route"
        }
        answer = "".join(data["text"] for event, data in events if event == "token")
        assert answer.strip()
        private.write_text(
            json.dumps(
                {
                    "url": url,
                    "cookies": dict(client.cookies),
                    "chat_id": chat["id"],
                    "turn_id": turn_id,
                    "answer": answer,
                }
            )
        )
        (ROOT / "reports/reader.json").write_text(
            json.dumps(
                {
                    "passed": True,
                    "ttft_seconds": first,
                    "total_seconds": time.monotonic() - started,
                    "answer": answer,
                    "traces": traces,
                },
                indent=2,
            )
        )
        print("Three specialists and Sonnet deep synthesis passed.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    verify(args.url, args.restore)
