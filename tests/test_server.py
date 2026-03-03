"""Tests for server — HTTP bridge."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer

import pytest

from openclaw_archiver.server import _Handler


def _find_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def server(tmp_path, monkeypatch):
    """Start a test HTTP server on a random port."""
    import os

    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

    port = _find_free_port()
    httpd = HTTPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def _post_json(url: str, data: dict) -> tuple[int, dict]:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _get_json(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class TestHealth:
    """Verify GET /health endpoint."""

    def test_health_ok(self, server: str) -> None:
        status, data = _get_json(f"{server}/health")

        assert status == 200
        assert data["ok"] is True
        assert data["plugin"] == "archiver"
        assert data["version"] == "0.1.0"


class TestMessage:
    """Verify POST /message endpoint."""

    def test_message_help(self, server: str) -> None:
        status, data = _post_json(f"{server}/message", {
            "message": "/archive help",
            "user_id": "U_TEST",
        })

        assert status == 200
        assert data["ok"] is True
        assert "/archive 사용법" in data["response"]

    def test_message_non_archive(self, server: str) -> None:
        status, data = _post_json(f"{server}/message", {
            "message": "hello world",
            "user_id": "U_TEST",
        })

        assert status == 200
        assert data["ok"] is True
        assert data["response"] is None

    def test_message_save_and_list(self, server: str) -> None:
        # Save
        status, data = _post_json(f"{server}/message", {
            "message": "/archive save 테스트 메시지 https://example.com/1",
            "user_id": "U_INTEG",
        })
        assert status == 200
        assert data["ok"] is True
        assert "저장했습니다" in data["response"]

        # List
        status, data = _post_json(f"{server}/message", {
            "message": "/archive list",
            "user_id": "U_INTEG",
        })
        assert status == 200
        assert "테스트 메시지" in data["response"]


class TestMessageErrors:
    """Verify POST /message error handling."""

    def test_missing_message(self, server: str) -> None:
        status, data = _post_json(f"{server}/message", {
            "user_id": "U_TEST",
        })

        assert status == 400
        assert data["ok"] is False
        assert "message and user_id are required" in data["error"]

    def test_missing_user_id(self, server: str) -> None:
        status, data = _post_json(f"{server}/message", {
            "message": "/archive help",
        })

        assert status == 400
        assert data["ok"] is False
        assert "message and user_id are required" in data["error"]

    def test_empty_body(self, server: str) -> None:
        status, data = _post_json(f"{server}/message", {})

        assert status == 400
        assert data["ok"] is False

    def test_invalid_json(self, server: str) -> None:
        body = b"not json"
        req = urllib.request.Request(
            f"{server}/message",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status, data = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            status, data = e.code, json.loads(e.read())

        assert status == 400
        assert data["ok"] is False
        assert "invalid JSON" in data["error"]


class TestNotFound:
    """Verify 404 for unknown paths."""

    def test_get_unknown_path(self, server: str) -> None:
        status, data = _get_json(f"{server}/unknown")

        assert status == 404
        assert data["ok"] is False

    def test_post_unknown_path(self, server: str) -> None:
        status, data = _post_json(f"{server}/unknown", {"foo": "bar"})

        assert status == 404
        assert data["ok"] is False
