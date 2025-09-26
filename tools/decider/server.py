#!/usr/bin/env python3
"""Local Decider stub server.

This module exposes a minimal HTTP server that mimics the future LLM-powered
"Decider" microservice.  For Milestone M1-01 we only implement deterministic
stub responses and a `/healthz` endpoint; later milestones will extend this file
with schema validation, caching, and timeouts.

Usage (from the repo root):

    python3 tools/decider/server.py --stub

Optional flags:
    --host / --port   Bind address (defaults to 127.0.0.1:8000)
    --log-level       Python logging level (defaults to INFO)
    --check           Boot the server, hit /healthz once, print the status, exit
"""

from __future__ import annotations

import argparse
import http.client
import json
import logging
import signal
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import jsonschema

LOGGER = logging.getLogger("decider.server")

STUB_RESPONSES: Dict[str, Dict[str, Any]] = {
    "/decide/firm": {
        "direction": "hold",
        "price_step": 0.0,
        "expectation_bias": 0.0,
        "explanation": "stub: hold price; baseline heuristic"
    },
    "/decide/bank": {
        "approve": True,
        "credit_limit_ratio": 1.0,
        "spread_bps": 150,
        "explanation": "stub: approve with default spread"
    },
    "/decide/wage": {
        "direction": "hold",
        "wage_step": 0.0,
        "explanation": "stub: no wage adjustment"
    },
}

SCHEMA_DIR = Path(__file__).with_name("schemas")
SCHEMA_FILES = {
    "/decide/firm": "firm_request.schema.json",
    "/decide/bank": "bank_request.schema.json",
    "/decide/wage": "wage_request.schema.json",
}


def _load_validators() -> Dict[str, jsonschema.Draft7Validator]:
    validators: Dict[str, jsonschema.Draft7Validator] = {}
    for endpoint, filename in SCHEMA_FILES.items():
        schema_path = SCHEMA_DIR / filename
        with open(schema_path, "r") as handle:
            schema = json.load(handle)
        validators[endpoint] = jsonschema.Draft7Validator(schema)
    return validators


VALIDATORS = _load_validators()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local Decider stub server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity"
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Serve deterministic stub responses (default behaviour)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run a one-shot health check and exit."
    )
    args = parser.parse_args()

    # `--stub` is the only supported mode today; default to True so users do not
    # have to pass the flag explicitly once the CLI stabilises.
    if not args.stub:
        LOGGER.debug("--stub not provided; enabling stub mode by default")
        args.stub = True
    return args


def make_handler(stub_mode: bool):
    """Factory that builds a request handler bound to the configuration."""

    class DeciderRequestHandler(BaseHTTPRequestHandler):
        server_version = "DeciderStub/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - delegated to logging
            LOGGER.info("%s - %s", self.address_string(), fmt % args)

        def _read_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return {}, None
            try:
                data = self.rfile.read(length)
            except Exception as exc:  # pragma: no cover - rare I/O failure
                return None, f"failed to read request body: {exc}"
            try:
                return json.loads(data.decode("utf-8")), None
            except json.JSONDecodeError as exc:
                return None, f"invalid JSON payload: {exc}"

        def _send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 (HTTP verb name)
            if self.path == "/healthz":
                LOGGER.debug("health check hit")
                self._send_json(HTTPStatus.OK, {"status": "ok"})
            else:
                LOGGER.debug("unknown GET path %s", self.path)
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})

        def do_POST(self) -> None:  # noqa: N802 (HTTP verb name)
            LOGGER.debug("POST %s", self.path)
            payload, error = self._read_json()
            if error:
                LOGGER.warning("invalid payload: %s", error)
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json", "detail": error})
                return

            validator = VALIDATORS.get(self.path)
            if validator is not None:
                errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
                if errors:
                    detail = [
                        {
                            "path": list(err.path),
                            "message": err.message,
                        }
                        for err in errors[:5]
                    ]
                    LOGGER.warning("schema validation failed: %s", detail)
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "invalid_request", "detail": detail}
                    )
                    return

            if not stub_mode:
                LOGGER.error("non-stub mode requested but not implemented")
                self._send_json(
                    HTTPStatus.NOT_IMPLEMENTED,
                    {"error": "not_implemented", "detail": "only stub mode is available"}
                )
                return

            response = STUB_RESPONSES.get(self.path)
            if response is None:
                LOGGER.warning("unknown path: %s", self.path)
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown_endpoint", "path": self.path})
                return

            LOGGER.info("stub response for %s", self.path)
            # Return a copy so callers cannot mutate the global template.
            self._send_json(HTTPStatus.OK, json.loads(json.dumps(response)))

    return DeciderRequestHandler


def run_server(host: str, port: int, stub_mode: bool, check_only: bool) -> int:
    server = ThreadingHTTPServer((host, port), make_handler(stub_mode))
    LOGGER.info("Decider stub listening on http://%s:%s", host, port)

    # Graceful shutdown support for Ctrl+C / SIGTERM.
    def _handle_stop(signum: int, _frame: Any) -> None:  # pragma: no cover - signal path
        LOGGER.info("Received signal %s, shutting down", signum)
        server.shutdown()

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    if check_only:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            conn = http.client.HTTPConnection(host, port, timeout=3)
            conn.request("GET", "/healthz")
            resp = conn.getresponse()
            status = resp.status
            body = resp.read().decode("utf-8")
            LOGGER.info("Health check status=%s body=%s", status, body)
            ok = status == HTTPStatus.OK
        except Exception as exc:  # pragma: no cover - network failures
            LOGGER.error("Health check failed: %s", exc)
            ok = False
        finally:
            server.shutdown()
            thread.join(timeout=2)
        return 0 if ok else 1

    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - handled by signal
        LOGGER.info("Interrupted by user")
    finally:
        server.server_close()
    return 0


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s %(levelname)s %(message)s")
    exit_code = run_server(args.host, args.port, stub_mode=args.stub, check_only=args.check)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
