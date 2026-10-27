"""I test my release gates with passing evidence and deliberately broken evidence."""

import io
import json
import subprocess
import sys
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from scripts.verify_release import read_events, verify_live, verify_report, verify_stream


def frame(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


def valid_events():
    return [
        ("trace", {"type": "agent_route", "agent": "summary", "reason": "summarize"}),
        ("trace", {"type": "llm_route", "provider": "a", "model": "b", "reason": "cost"}),
        ("trace", {"type": "rag_retrieval", "chunk_ids": ["chapter-1"]}),
        ("citation", {"source_id": "book", "chunk_id": "chapter-1"}),
        ("token", {"text": "First "}),
        ("token", {"text": "sentence."}),
        ("done", {"success": True}),
    ]


def stream(events):
    return io.BytesIO(b"".join(frame(event, data) for event, data in events))


@pytest.mark.parametrize("wrapper", ["testsuite", "testsuites"])
def test_report_accepts_passing_cases(tmp_path, wrapper):
    report = tmp_path / "report.xml"
    report.write_text(f'<{wrapper}><testcase name="one"/><testcase name="two"/></{wrapper}>')
    assert verify_report(report) == 2


@pytest.mark.parametrize("tag", ["failure", "error", "skipped"])
def test_report_rejects_nonpassing_cases(tmp_path, tag):
    report = tmp_path / "report.xml"
    report.write_text(f"<testsuite><testcase><{tag}/></testcase></testsuite>")
    with pytest.raises(ValueError, match=tag):
        verify_report(report)


def test_report_rejects_empty_suite(tmp_path):
    report = tmp_path / "report.xml"
    report.write_text("<testsuite/>")
    with pytest.raises(ValueError, match="no executed"):
        verify_report(report)


def test_report_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_report(tmp_path / "absent.xml")


@pytest.mark.parametrize(
    "body,accepted",
    [
        ("def test_case(): assert True", True),
        ("def test_case(): assert False", False),
        ("def test_case(): pytest.skip('unavailable')", False),
        ("@pytest.mark.xfail\ndef test_case(): assert False", False),
        ("@pytest.mark.xfail\ndef test_case(): assert True", False),
    ],
)
def test_gate_with_real_pytest_reports(tmp_path, body, accepted):
    case = tmp_path / "test_case.py"
    case.write_text("import pytest\n" + body)
    report = tmp_path / "actual.xml"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(case),
            "-o",
            "xfail_strict=true",
            "-p",
            "no:cacheprovider",
            f"--junitxml={report}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if accepted:
        assert result.returncode == 0, result.stdout
        assert verify_report(report) == 1
    else:
        with pytest.raises(ValueError):
            verify_report(report)


def test_stream_accepts_complete_evidence():
    verify_stream(stream(valid_events()))


@pytest.mark.parametrize("removed", range(7))
def test_stream_rejects_each_missing_required_piece(removed):
    events = valid_events()
    events.pop(removed)
    with pytest.raises(ValueError):
        verify_stream(stream(events))


def test_stream_rejects_error_even_after_valid_tokens():
    events = valid_events()
    events.insert(-1, ("error", {"message": "provider failed"}))
    with pytest.raises(ValueError, match="error event"):
        verify_stream(stream(events))


def test_stream_rejects_unsuccessful_done():
    events = valid_events()[:-1] + [("done", {"success": False})]
    with pytest.raises(ValueError, match="did not report success"):
        verify_stream(stream(events))


def test_stream_rejects_events_after_done():
    events = valid_events() + [("token", {"text": "late"})]
    with pytest.raises(ValueError, match="after done"):
        verify_stream(stream(events))


def test_stream_rejects_nonobject_payload():
    with pytest.raises(ValueError, match="JSON object"):
        verify_stream(stream([("token", "plain string")]))


def test_events_parse_crlf_comments_unicode_and_multiline_json():
    raw = ': heartbeat\r\nevent: token\r\ndata: {\r\ndata: "text": "café"}\r\n\r\n'
    assert list(read_events(io.BytesIO(raw.encode()))) == [("token", {"text": "café"})]


def test_events_reject_truncated_frame():
    with pytest.raises(ValueError, match="incomplete frame"):
        list(read_events(io.BytesIO(b'event: token\ndata: {"text":"a"}\n')))


def test_events_reject_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        list(read_events(io.BytesIO(b"event: token\ndata: invalid\n\n")))


class Response(io.BytesIO):
    def __init__(self, body, content_type, status=200):
        super().__init__(body)
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type


def responses():
    return [
        Response(b'{"ready": true}', "application/json"),
        Response(b"<!doctype html><html></html>", "text/html"),
        Response(stream(valid_events()).read(), "text/event-stream"),
    ]


def test_live_uses_post_and_a_unique_session():
    with patch("scripts.verify_release.urlopen", side_effect=responses()) as opener:
        verify_live("https://example.test", "Summarize chapter one")
    request = opener.call_args_list[2].args[0]
    assert request.get_method() == "POST"
    assert request.full_url == "https://example.test/api/chat"
    payload = json.loads(request.data)
    assert payload["query"] == "Summarize chapter one"
    assert payload["session_id"].startswith("ci-")


@pytest.mark.parametrize(
    "url",
    ["http://example.test", "file:///etc/passwd", "https://a:b@example.test", "https://x/?key=x"],
)
def test_live_rejects_unsafe_base_url(url):
    with patch("scripts.verify_release.urlopen") as opener:
        with pytest.raises(ValueError):
            verify_live(url, "query")
    opener.assert_not_called()


@pytest.mark.parametrize(
    "index,body,content_type",
    [
        (0, b'{"ready": false}', "application/json"),
        (1, b"<html></html>", "application/json"),
        (1, b"not a page", "text/html"),
        (2, b"answer", "application/json"),
    ],
)
def test_live_rejects_broken_http_contract(index, body, content_type):
    replies = responses()
    replies[index] = Response(body, content_type)
    with patch("scripts.verify_release.urlopen", side_effect=replies):
        with pytest.raises(ValueError):
            verify_live("https://example.test", "query")


def test_live_does_not_swallow_http_failure():
    error = HTTPError("https://example.test", 503, "unavailable", {}, None)
    with patch("scripts.verify_release.urlopen", side_effect=error):
        with pytest.raises(HTTPError):
            verify_live("https://example.test", "query")
