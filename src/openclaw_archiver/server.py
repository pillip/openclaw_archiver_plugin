"""HTTP bridge server for JS/TS OpenClaw integration."""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

from openclaw_archiver import __version__
from openclaw_archiver.plugin import handle_message

_DEFAULT_PORT = 8201
_BIND_HOST = "127.0.0.1"
_MAX_BODY_BYTES = 1_048_576  # 1 MiB


class _Handler(BaseHTTPRequestHandler):
    """Request handler for the archiver HTTP bridge."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {
                "ok": True,
                "plugin": "archiver",
                "version": __version__,
            })
        else:
            self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/message":
            self._handle_message()
        else:
            self._send_json(404, {"ok": False, "error": "not found"})

    def _handle_message(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            self._send_json(400, {
                "ok": False,
                "error": "invalid Content-Length",
            })
            return

        if length > _MAX_BODY_BYTES:
            self._send_json(413, {
                "ok": False,
                "error": f"body too large (max {_MAX_BODY_BYTES} bytes)",
            })
            return

        try:
            body = self.rfile.read(length)
            data = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {
                "ok": False,
                "error": "invalid JSON body",
            })
            return

        message = data.get("message")
        user_id = data.get("user_id")

        if not message or not user_id:
            self._send_json(400, {
                "ok": False,
                "error": "message and user_id are required",
            })
            return

        try:
            response = handle_message(message, user_id)
            self._send_json(200, {
                "ok": True,
                "response": response,
            })
        except Exception:
            logger.exception("handle_message failed")
            self._send_json(500, {
                "ok": False,
                "error": "internal server error",
            })

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Suppress default stderr logging."""


def run() -> None:
    """Start the HTTP bridge server."""
    port = int(os.environ.get("OPENCLAW_ARCHIVER_PORT", _DEFAULT_PORT))
    try:
        server = HTTPServer((_BIND_HOST, port), _Handler)
    except OSError as e:
        print(f"Error: cannot bind to {_BIND_HOST}:{port} — {e}")
        print("Hint: another process may be using this port. "
              "Set OPENCLAW_ARCHIVER_PORT to use a different port.")
        raise SystemExit(1) from None
    print(f"Archiver server listening on {_BIND_HOST}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
