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
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger("decider.server")

SCHEMA_FILES = {
    "/decide/firm": "schemas_firm.json",
    "/decide/bank": "schemas_bank.json",
    "/decide/wage": "schemas_wage.json",
}


def _load_schema(filename: str) -> Dict[str, Any]:
    schema_path = Path(__file__).with_name(filename)
    try:
        with schema_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - configuration error
        raise RuntimeError(f"Missing schema file: {schema_path}") from exc


SCHEMAS = {endpoint: _load_schema(file) for endpoint, file in SCHEMA_FILES.items()}

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


def _validate_payload(instance: Any, schema: Dict[str, Any], path: str = "payload") -> List[str]:
    errors: List[str] = []

    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(instance, dict):
            errors.append(f"{path} must be an object")
            return errors

        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}.{key} is required")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(_validate_payload(instance[key], properties[key], f"{path}.{key}"))
            else:
                if additional is False:
                    errors.append(f"{path}.{key} is not allowed")
                elif isinstance(additional, dict):
                    errors.extend(_validate_payload(instance[key], additional, f"{path}.{key}"))
        return errors

    if schema_type == "array":
        if not isinstance(instance, list):
            errors.append(f"{path} must be an array")
            return errors
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(f"{path} must contain at least {min_items} items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(instance):
                errors.extend(_validate_payload(item, item_schema, f"{path}[{index}]"))
        return errors

    if schema_type == "string":
        if not isinstance(instance, str):
            errors.append(f"{path} must be a string")
            return errors
        min_len = schema.get("minLength")
        if min_len is not None and len(instance) < min_len:
            errors.append(f"{path} must be at least {min_len} characters long")
        enum = schema.get("enum")
        if enum is not None and instance not in enum:
            errors.append(f"{path} must be one of {enum}")
        return errors

    if schema_type == "integer":
        if not (isinstance(instance, int) and not isinstance(instance, bool)):
            errors.append(f"{path} must be an integer")
            return errors
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and instance < minimum:
            errors.append(f"{path} must be >= {minimum}")
        if maximum is not None and instance > maximum:
            errors.append(f"{path} must be <= {maximum}")
        return errors

    if schema_type == "number":
        if not ((isinstance(instance, (int, float))) and not isinstance(instance, bool)):
            errors.append(f"{path} must be a number")
            return errors
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and instance < minimum:
            errors.append(f"{path} must be >= {minimum}")
        if maximum is not None and instance > maximum:
            errors.append(f"{path} must be <= {maximum}")
        return errors

    if schema_type == "boolean":
        if not isinstance(instance, bool):
            errors.append(f"{path} must be a boolean")
        return errors

    # If the schema does not specify a known type, accept the value.
    return errors


def make_handler(stub_mode: bool, schemas: Dict[str, Dict[str, Any]]):
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

            if not stub_mode:
                LOGGER.error("non-stub mode requested but not implemented")
                self._send_json(
                    HTTPStatus.NOT_IMPLEMENTED,
                    {"error": "not_implemented", "detail": "only stub mode is available"}
                )
                return

            schema = schemas.get(self.path)
            if schema is not None:
                errors = _validate_payload(payload, schema)
                if errors:
                    LOGGER.warning("payload failed validation: %s", errors)
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "invalid_payload", "messages": errors}
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
    server = ThreadingHTTPServer((host, port), make_handler(stub_mode, SCHEMAS))
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
