import os
import socket
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def project_write_guard(event, arguments):
    paths = []
    if event == "open":
        path, mode, flags = arguments
        if isinstance(path, int):
            return
        writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writing:
            paths.append(path)
    elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate"}:
        paths.append(arguments[0])
    elif event in {"os.rename", "os.link", "os.symlink"}:
        paths.extend(arguments[:2])
    for path in paths:
        if isinstance(path, int):
            continue
        if not Path(os.fsdecode(path)).resolve().is_relative_to(ROOT):
            raise PermissionError("My test sandbox blocks writes outside Assignment 2.")


def pytest_configure(config):
    if Path(sys.prefix).resolve() != ROOT / ".venv":
        raise pytest.UsageError("I run tests through this project's .venv.")
    temporary = ROOT / ".cache" / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    config.option.log_file = str(temporary / "pytest.log")
    os.environ["TMPDIR"] = str(temporary)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    tempfile.tempdir = str(temporary)
    base = Path(config.option.basetemp).resolve()
    if not base.is_relative_to(ROOT / ".cache"):
        raise pytest.UsageError("My test temporary directory must be inside .cache.")
    sys.addaudithook(project_write_guard)


@pytest.fixture(autouse=True)
def offline_isolation(monkeypatch, request):
    if "live" in request.path.relative_to(ROOT / "tests").parts:
        return
    for key in tuple(os.environ):
        if key.endswith("_API_KEY") or key == "GOOGLE_APPLICATION_CREDENTIALS":
            monkeypatch.delenv(key)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SESSION_SECRET", "offline-test-secret-" * 3)
    original = socket.socket.connect

    def blocked_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise AssertionError("External networking is blocked in my offline tests.")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_connect)
