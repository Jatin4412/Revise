from __future__ import annotations

import hmac
import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from .service import EngineService, create_default_service


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
ENGINE_PATH = "/v1/engine"
TRACE_PATH = "/v1/engine/trace"
HEALTH_PATH = "/health"
TRACE_TOKEN_HEADER = "X-Revise-Trace-Token"


class EngineHTTPHandler(BaseHTTPRequestHandler):
    """Small stdlib HTTP adapter around EngineService.

    The adapter deliberately knows only the application request/response boundary;
    engine internals remain behind EngineService.
    """

    service_factory: Callable[[], EngineService] = create_default_service
    _service: EngineService | None = None

    def _get_service(self) -> EngineService:
        if self._service is None:
            # Access through the class so a plain function stored as a class
            # attribute is not turned into a bound method.
            self.__class__._service = self.__class__.service_factory()
        return self.__class__._service

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(0 if status == 204 else len(body)))
        self.send_header("Access-Control-Allow-Origin", os.environ.get("REVISE_CORS_ORIGIN", "http://localhost:3000"))
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if status != 204:
            self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler API
        self._send_json(204, {})

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == HEALTH_PATH:
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": {"code": "not_found", "message": "endpoint not found"}})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path not in (ENGINE_PATH, TRACE_PATH):
            self._send_json(404, {"error": {"code": "not_found", "message": "endpoint not found"}})
            return
        if self.path == TRACE_PATH and not _trace_access_allowed(self.headers.get(TRACE_TOKEN_HEADER)):
            self._send_json(403, {"error": {"code": "trace_forbidden", "message": "development trace access is not enabled"}})
            return

        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if length < 0:
                raise ValueError("missing Content-Length")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            service = self._get_service()
            response = service.handle_trace_payload(payload) if self.path == TRACE_PATH else service.handle_payload(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send_json(400, {"error": {"code": "invalid_request", "message": str(exc)}})
            return
        except Exception:
            # Keep the public response generic, but expose the real traceback in
            # the local developer console so runtime failures are diagnosable.
            traceback.print_exc()
            self._send_json(500, {"error": {"code": "engine_error", "message": "Revise could not process the request"}})
            return

        self._send_json(200, response)

    def log_message(self, format: str, *args: object) -> None:
        # Keep the adapter quiet by default; callers can run it behind their own logger.
        return


def _trace_access_allowed(token: str | None) -> bool:
    """Allow local development trace by default, but protect non-local exposure.

    Setting ``REVISE_TRACE_TOKEN`` always requires the matching header. If no token
    is configured, the trace endpoint remains available only when the configured
    host is loopback/local. This preserves the current local developer workflow
    while preventing accidental trace exposure when the engine is bound publicly.
    """
    configured_token = os.environ.get("REVISE_TRACE_TOKEN")
    if configured_token:
        return token is not None and hmac.compare_digest(token, configured_token)

    configured_host = os.environ.get("REVISE_HOST", DEFAULT_HOST).strip().lower()
    return configured_host in {"127.0.0.1", "localhost", "::1"}


def serve(*, host: str | None = None, port: int | None = None) -> None:
    """Run the Revise HTTP application on the configured local interface."""
    resolved_host = host or os.environ.get("REVISE_HOST", DEFAULT_HOST)
    resolved_port = port or int(os.environ.get("REVISE_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((resolved_host, resolved_port), EngineHTTPHandler)
    print(f"Revise engine listening on http://{resolved_host}:{resolved_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
