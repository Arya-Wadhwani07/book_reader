"""I reject incomplete test reports and verify a deployed streaming RAG response."""

import argparse
import json
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


def verify_report(path):
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    if not cases:
        raise ValueError("My test report contains no executed test cases.")
    for tag in ("failure", "error", "skipped"):
        if any(True for _ in root.iter(tag)):
            raise ValueError(f"My test report contains {tag} results.")
    return len(cases)


def read_events(lines):
    event, data = "message", []
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n")
        if not line:
            if data:
                yield event, json.loads("\n".join(data))
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
    if data:
        raise ValueError("My SSE stream ended with an incomplete frame.")


def verify_stream(lines):
    tokens, citations, routes, done = 0, 0, set(), False
    for event, data in read_events(lines):
        if done:
            raise ValueError("My stream sent an event after done.")
        if not isinstance(data, dict):
            raise ValueError("My SSE event payload must be a JSON object.")
        if event == "error":
            raise ValueError("My live query returned an error event.")
        if event == "token" and isinstance(data.get("text"), str) and data["text"].strip():
            tokens += 1
        elif event == "citation" and data.get("source_id") and data.get("chunk_id"):
            citations += 1
        elif event == "trace":
            kind = data.get("type")
            if kind == "agent_route" and data.get("agent") and data.get("reason"):
                routes.add(kind)
            elif kind == "llm_route" and all(data.get(k) for k in ("provider", "model", "reason")):
                routes.add(kind)
            elif kind == "rag_retrieval" and data.get("chunk_ids"):
                routes.add(kind)
        elif event == "done":
            done = data.get("success") is True
            if not done:
                raise ValueError("My done event did not report success.")
    if not done or tokens < 2 or citations < 1:
        raise ValueError(
            "My live answer lacks successful completion, streamed tokens, or citations."
        )
    if routes != {"agent_route", "llm_route", "rag_retrieval"}:
        raise ValueError("My live answer lacks required routing/retrieval evidence.")


def verify_live(base_url, query):
    parsed = urlparse(base_url)
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ValueError("My cloud URL must use HTTPS; HTTP is allowed only for local tests.")
    if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            "My base URL must not contain credentials, query parameters, or fragments."
        )
    base_url = base_url.rstrip("/")
    session = build_opener(HTTPCookieProcessor())
    with session.open(f"{base_url}/readyz", timeout=60) as response:
        if response.status != 200 or json.load(response).get("ready") is not True:
            raise ValueError("My application is not ready.")
    with session.open(base_url, timeout=60) as response:
        if response.status != 200 or response.headers.get_content_type() != "text/html":
            raise ValueError("My frontend is not served as HTML.")
        if b"<html" not in response.read().lower():
            raise ValueError("My frontend response is not an HTML document.")
    with session.open(f"{base_url}/api/bootstrap", timeout=60) as response:
        books = json.load(response)["books"]
    book = next((book for book in books if book["status"] == "ready"), None)
    if book is None:
        raise ValueError("My library has no ready book.")
    create = Request(
        f"{base_url}/api/chats",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with session.open(create, timeout=60) as response:
        chat = json.load(response)
    payload = json.dumps(
        {
            "query": query,
            "session_id": chat["id"],
            "turn_id": str(uuid.uuid4()),
            "book_id": book["id"],
            "spoiler_limit": None,
            "depth": "brief",
        }
    ).encode()
    request = Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    with session.open(request, timeout=300) as response:
        if response.status != 200 or response.headers.get_content_type() != "text/event-stream":
            raise ValueError("My chat response is not an SSE stream.")
        verify_stream(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report")
    report.add_argument("path")
    live = commands.add_parser("live")
    live.add_argument("url")
    live.add_argument("--query", required=True)
    args = parser.parse_args()
    if args.command == "report":
        print(f"PASS: {verify_report(args.path)} test cases; no failures, errors, or skips.")
    else:
        verify_live(args.url, args.query)
        print("PASS: readiness, HTML frontend, streamed answer, routing, retrieval, and citations.")


if __name__ == "__main__":
    main()
