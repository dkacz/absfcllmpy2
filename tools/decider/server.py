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
import os
import signal
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

try:  # pragma: no cover - import style depends on execution context
    from cache import DecisionCache
except ImportError:  # pragma: no cover
    from .cache import DecisionCache  # type: ignore

try:  # pragma: no cover - import style depends on execution context
    from providers import OpenRouterAdapter, OpenRouterError
except ImportError:  # pragma: no cover
    from .providers import OpenRouterAdapter, OpenRouterError  # type: ignore

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

BATCH_ENDPOINTS: Dict[str, str] = {
    "/firm.decide.batch": "/decide/firm",
    "/bank.decide.batch": "/decide/bank",
    "/wage.decide.batch": "/decide/wage",
}

BATCH_MAX_ITEMS = 16

SCHEMA_DIR = Path(__file__).with_name("schemas")
SCHEMA_FILES = {
    "/decide/firm": "firm_request.schema.json",
    "/decide/bank": "bank_request.schema.json",
    "/decide/wage": "wage_request.schema.json",
}


DEFAULT_MODE = "stub"
LIVE_BUFFER_MS = 20


class LivePrompt(object):
    """Simple prompt template for the OpenRouter adapter."""

    def __init__(self, system: str, user_template: str, response_format: Optional[Dict[str, Any]] = None) -> None:
        self.system = system
        self.user_template = user_template
        self.response_format = response_format or {"type": "json_object"}

    def build_user(self, payload: Dict[str, Any]) -> str:
        payload_json = json.dumps(payload, sort_keys=True, indent=2)
        return self.user_template.format(payload_json=payload_json)


def _default_live_prompts() -> Dict[str, LivePrompt]:
    """Return default prompt definitions for live mode."""

    return {
        "/decide/firm": LivePrompt(
            system=(
                "You are the firm pricing decision service for the Caiani AB-SFC model. "
                "Return a compact JSON object with keys: direction (string), price_step (number), "
                "expectation_bias (number), and why_code (string describing the rationale)."
            ),
            user_template=(
                "Given the following firm state, guards, and baseline decision (JSON):\n"
                "{payload_json}\n\nRespond with JSON only."
            ),
        ),
        "/decide/bank": LivePrompt(
            system=(
                "You are the bank credit decision service for the Caiani AB-SFC model. "
                "Respond with JSON containing approve (boolean), credit_limit_ratio (number), "
                "spread_bps (number), and why_code (string summarising the choice)."
            ),
            user_template=(
                "Bank state, applicant metrics, and guard rails (JSON):\n{payload_json}\n\n"
                "Return JSON only."
            ),
        ),
        "/decide/wage": LivePrompt(
            system=(
                "You are the wage negotiation decision service for the Caiani AB-SFC model. "
                "Return JSON with direction (string), wage_step (number), and why_code (string)."
            ),
            user_template=(
                "Worker and firm wage context (JSON):\n{payload_json}\n\nReturn JSON only."
            ),
        ),
    }


def _validate_firm_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(decision, dict):
        raise ValueError("firm decision must be a JSON object")
    result = dict(decision)
    direction = result.get("direction")
    if not isinstance(direction, str) or not direction:
        raise ValueError("firm decision missing 'direction' string")
    for field in ("price_step", "expectation_bias"):
        value = result.get(field)
        if value is None:
            raise ValueError("firm decision missing '%s'" % field)
        try:
            result[field] = float(value)
        except (TypeError, ValueError):
            raise ValueError("firm decision field '%s' must be numeric" % field)
    why_code = result.get("why_code")
    if why_code is not None and not isinstance(why_code, str):
        raise ValueError("firm decision 'why_code' must be a string when provided")
    return result


def _validate_bank_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(decision, dict):
        raise ValueError("bank decision must be a JSON object")
    result = dict(decision)
    approve = result.get("approve")
    if not isinstance(approve, bool):
        raise ValueError("bank decision requires boolean 'approve'")
    for field in ("credit_limit_ratio", "spread_bps"):
        value = result.get(field)
        if value is None:
            raise ValueError("bank decision missing '%s'" % field)
        try:
            result[field] = float(value)
        except (TypeError, ValueError):
            raise ValueError("bank decision field '%s' must be numeric" % field)
    why_code = result.get("why_code")
    if why_code is not None and not isinstance(why_code, str):
        raise ValueError("bank decision 'why_code' must be a string when provided")
    return result


def _validate_wage_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(decision, dict):
        raise ValueError("wage decision must be a JSON object")
    result = dict(decision)
    direction = result.get("direction")
    if not isinstance(direction, str) or not direction:
        raise ValueError("wage decision missing 'direction' string")
    wage_step = result.get("wage_step")
    if wage_step is None:
        raise ValueError("wage decision missing 'wage_step'")
    try:
        result["wage_step"] = float(wage_step)
    except (TypeError, ValueError):
        raise ValueError("wage decision field 'wage_step' must be numeric")
    why_code = result.get("why_code")
    if why_code is not None and not isinstance(why_code, str):
        raise ValueError("wage decision 'why_code' must be a string when provided")
    return result


LIVE_RESPONSE_VALIDATORS = {
    "/decide/firm": _validate_firm_decision,
    "/decide/bank": _validate_bank_decision,
    "/decide/wage": _validate_wage_decision,
}


def _prepare_live_router(args: argparse.Namespace, deadline_ms: int) -> LiveModeRouter:
    primary_model = args.openrouter_model_primary
    if not primary_model:
        raise ValueError("live mode requires --openrouter-model-primary or OPENROUTER_MODEL_PRIMARY env")
    fallback_model = args.openrouter_model_fallback or None

    try:
        adapter = OpenRouterAdapter(
            base_url=args.openrouter_base_url,
            referer=args.openrouter_referer,
            title=args.openrouter_title,
        )
    except ValueError as exc:
        raise ValueError("live mode requires OPENROUTER_API_KEY") from exc

    check_deadline = None
    if deadline_ms and deadline_ms > 0:
        check_deadline = max(50, deadline_ms - LIVE_BUFFER_MS)

    slugs = [primary_model]
    if fallback_model:
        slugs.append(fallback_model)

    for slug in slugs:
        try:
            if not adapter.model_exists(slug, deadline_ms=check_deadline):
                raise OpenRouterError("model_not_found", detail="model '%s' unavailable" % slug)
        except OpenRouterError as exc:
            LOGGER.error(
                "OpenRouter model check failed model=%s reason=%s detail=%s status=%s",
                slug,
                exc.reason,
                exc.detail,
                exc.status,
            )
            raise

    LOGGER.info(
        "OpenRouter live mode initialised primary=%s fallback=%s", primary_model, fallback_model or "none"
    )

    router_deadline = deadline_ms if deadline_ms > 0 else None
    return LiveModeRouter(
        adapter=adapter,
        primary_model=primary_model,
        fallback_model=fallback_model,
        server_deadline_ms=router_deadline,
    )


class LiveModeRouter(object):
    """Dispatch helper for live mode requests."""

    def __init__(
        self,
        adapter: OpenRouterAdapter,
        primary_model: str,
        fallback_model: Optional[str],
        server_deadline_ms: Optional[int],
        prompts: Optional[Dict[str, LivePrompt]] = None,
        validators: Optional[Dict[str, Any]] = None,
        buffer_ms: int = LIVE_BUFFER_MS,
    ) -> None:
        if not primary_model:
            raise ValueError("primary model slug is required for live mode")
        self.adapter = adapter
        self.primary_model = primary_model
        self.fallback_model = fallback_model if fallback_model and fallback_model != primary_model else None
        self.server_deadline_ms = server_deadline_ms
        self.prompts = prompts or _default_live_prompts()
        self.validators = validators or LIVE_RESPONSE_VALIDATORS
        self.buffer_ms = max(0, buffer_ms)

    def decide(self, endpoint: str, payload: Dict[str, Any], start_time: float) -> Tuple[HTTPStatus, Dict[str, Any]]:
        prompt = self.prompts.get(endpoint)
        if prompt is None:
            LOGGER.error("live prompt missing for endpoint %s", endpoint)
            return HTTPStatus.NOT_IMPLEMENTED, {
                "error": "live_prompt_missing",
                "detail": {"endpoint": endpoint},
            }

        validator = self.validators.get(endpoint)
        if validator is None:
            LOGGER.error("live validator missing for endpoint %s", endpoint)
            return HTTPStatus.NOT_IMPLEMENTED, {
                "error": "live_validator_missing",
                "detail": {"endpoint": endpoint},
            }

        attempts: List[Dict[str, Any]] = []
        for attempt_index, model in enumerate(self._models()):
            attempt_label = "primary" if attempt_index == 0 else "fallback"
            try:
                deadline_ms = self._remaining_deadline_ms(start_time)
                decision, meta = self.adapter.call(
                    model,
                    prompt.system,
                    prompt.build_user(payload),
                    response_format=prompt.response_format,
                    deadline_ms=deadline_ms,
                )
                if not isinstance(decision, dict):
                    raise ValueError("model response must be JSON object")
                normalised = validator(decision)
                usage = meta.get("usage", {}) if isinstance(meta, dict) else {}
                why_code = normalised.get("why_code")
                LOGGER.info(
                    "live decision endpoint=%s model=%s attempt=%s why=%s prompt_tokens=%s completion_tokens=%s elapsed_ms=%.1f",
                    endpoint,
                    meta.get("model", model) if isinstance(meta, dict) else model,
                    attempt_label,
                    why_code or "n/a",
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    meta.get("elapsed_ms", 0.0) if isinstance(meta, dict) else 0.0,
                )
                return HTTPStatus.OK, normalised
            except OpenRouterError as exc:
                details = {
                    "model": model,
                    "attempt": attempt_label,
                    "reason": exc.reason,
                }
                if exc.status is not None:
                    details["status"] = exc.status
                if exc.detail is not None:
                    details["detail"] = exc.detail
                attempts.append(details)
                LOGGER.warning(
                    "live decision failed endpoint=%s model=%s reason=%s detail=%s status=%s",
                    endpoint,
                    model,
                    exc.reason,
                    exc.detail,
                    exc.status,
                )
            except ValueError as exc:
                attempts.append(
                    {
                        "model": model,
                        "attempt": attempt_label,
                        "reason": "schema_error",
                        "detail": str(exc),
                    }
                )
                LOGGER.warning(
                    "live decision validation error endpoint=%s model=%s detail=%s",
                    endpoint,
                    model,
                    exc,
                )

        return HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": "llm_live_failed",
            "detail": {
                "attempts": attempts,
            },
        }

    def _models(self) -> List[str]:
        models = [self.primary_model]
        if self.fallback_model:
            models.append(self.fallback_model)
        return models

    def _remaining_deadline_ms(self, start_time: float) -> Optional[int]:
        if self.server_deadline_ms is None or self.server_deadline_ms <= 0:
            return None
        elapsed_ms = (time.monotonic() - start_time) * 1000.0
        remaining = self.server_deadline_ms - elapsed_ms - self.buffer_ms
        if remaining <= 0:
            return 1
        return int(remaining)


def _load_validators() -> Dict[str, jsonschema.Draft7Validator]:
    validators: Dict[str, jsonschema.Draft7Validator] = {}
    for endpoint, filename in SCHEMA_FILES.items():
        schema_path = SCHEMA_DIR / filename
        with open(schema_path, "r") as handle:
            schema = json.load(handle)
        validators[endpoint] = jsonschema.Draft7Validator(schema)
    return validators


VALIDATORS = _load_validators()
CACHE = DecisionCache()


class TickBudgetTracker:
    """Track per-tick call budgets in a thread-safe manner."""

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self._counts: Dict[Tuple[int, int], int] = {}
        self._lock = threading.Lock()

    def register(self, run_id: int, tick: int) -> Tuple[bool, int]:
        """Record a call for ``(run_id, tick)`` and return allowance status.

        Returns a tuple ``(allowed, count)`` where ``count`` is the recorded
        number of calls for the pair *after* the increment. When the budget is
        disabled (``max_calls <= 0``) the method short-circuits and reports
        success.
        """

        if self.max_calls <= 0:
            return True, 0

        key = (run_id, tick)
        with self._lock:
            count = self._counts.get(key, 0)
            if count >= self.max_calls:
                return False, count
            count += 1
            self._counts[key] = count
            return True, count


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
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--mode",
        choices=["stub", "live"],
        default=DEFAULT_MODE,
        help="Run mode: stub (default) or live (OpenRouter-backed)."
    )
    parser.add_argument(
        "--deadline-ms",
        type=int,
        default=200,
        help="Per-request deadline in milliseconds (<=0 disables the check)."
    )
    parser.add_argument(
        "--tick-budget",
        type=int,
        default=0,
        help="Maximum calls allowed per run/tick pair (0 disables the budget)."
    )
    parser.add_argument(
        "--stub-delay-ms",
        type=int,
        default=0,
        help="Testing helper: add artificial latency to stub replies (milliseconds)."
    )
    parser.add_argument(
        "--openrouter-model-primary",
        default=os.getenv("OPENROUTER_MODEL_PRIMARY"),
        help="Primary OpenRouter model slug (requires live mode)."
    )
    parser.add_argument(
        "--openrouter-model-fallback",
        default=os.getenv("OPENROUTER_MODEL_FALLBACK"),
        help="Optional fallback OpenRouter model slug."
    )
    parser.add_argument(
        "--openrouter-base-url",
        default=os.getenv("OPENROUTER_BASE_URL", API_BASE_URL),
        help="Override OpenRouter API base URL (advanced)."
    )
    parser.add_argument(
        "--openrouter-title",
        default=os.getenv("OPENROUTER_TITLE"),
        help="Optional X-Title header for OpenRouter requests."
    )
    parser.add_argument(
        "--openrouter-referer",
        default=os.getenv("OPENROUTER_HTTP_REFERER"),
        help="Optional HTTP-Referer header for OpenRouter requests."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run a one-shot health check and exit."
    )
    args = parser.parse_args()

    if args.mode != "live":
        args.mode = "stub"
    return args


def make_handler(
    mode: str,
    deadline_ms: int,
    tick_budget: int,
    stub_delay_ms: int,
    live_router: Optional[LiveModeRouter] = None,
):
    """Factory that builds a request handler bound to the configuration."""

    stub_mode = mode != "live"
    if mode == "live" and live_router is None:
        raise ValueError("live mode requires live_router configuration")

    deadline_seconds: Optional[float]
    if deadline_ms <= 0:
        deadline_seconds = None
    else:
        deadline_seconds = deadline_ms / 1000.0

    stub_delay_seconds: float = max(stub_delay_ms, 0) / 1000.0
    budget_tracker = TickBudgetTracker(tick_budget)

    class DeciderRequestHandler(BaseHTTPRequestHandler):
        server_version = "DeciderStub/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - delegated to logging
            LOGGER.info("%s - %s", self.address_string(), fmt % args)

        def _deadline_exceeded(self, start_time: float) -> bool:
            if deadline_seconds is None:
                return False
            elapsed = time.monotonic() - start_time
            return elapsed > deadline_seconds

        def _deadline_payload(self, start_time: float, endpoint: str) -> Dict[str, Any]:
            elapsed = time.monotonic() - start_time
            LOGGER.warning(
                "deadline exceeded for %s (elapsed=%.1fms, limit=%dms)",
                endpoint,
                elapsed * 1000.0,
                deadline_ms,
            )
            return {
                "error": "deadline_exceeded",
                "detail": {
                    "elapsed_ms": int(elapsed * 1000.0),
                    "deadline_ms": deadline_ms,
                },
            }

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

        def _handle_single(self, endpoint: str, payload: Dict[str, Any], start_time: float) -> Tuple[HTTPStatus, Dict[str, Any]]:
            if deadline_seconds is not None and self._deadline_exceeded(start_time):
                return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)

            validator = VALIDATORS.get(endpoint)
            if validator is None:
                LOGGER.warning("unknown path: %s", endpoint)
                return HTTPStatus.NOT_FOUND, {"error": "unknown_endpoint", "path": endpoint}

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
                return HTTPStatus.BAD_REQUEST, {"error": "invalid_request", "detail": detail}

            run_id = payload.get("run_id")
            tick = payload.get("tick")
            if isinstance(run_id, int) and isinstance(tick, int):
                allowed, count = budget_tracker.register(run_id, tick)
                if not allowed:
                    LOGGER.warning(
                        "tick budget exceeded run_id=%s tick=%s limit=%s count=%s", run_id, tick, tick_budget, count
                    )
                    return HTTPStatus.TOO_MANY_REQUESTS, {
                        "error": "tick_budget_exceeded",
                        "detail": {
                            "run_id": run_id,
                            "tick": tick,
                            "limit": tick_budget,
                            "observed": count,
                        },
                    }

            if deadline_seconds is not None and self._deadline_exceeded(start_time):
                return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)

            cache_key, cached_response = CACHE.get(endpoint, payload)
            if cached_response is not None:
                LOGGER.info("cache hit %s key=%s", endpoint, cache_key[:8])
                return HTTPStatus.OK, cached_response
            LOGGER.debug("cache miss %s key=%s", endpoint, cache_key[:8])

            if not stub_mode:
                assert live_router is not None  # for type checkers
                status, live_body = live_router.decide(endpoint, payload, start_time)
                if status == HTTPStatus.OK:
                    response_copy = json.loads(json.dumps(live_body))
                    CACHE.set(cache_key, response_copy)
                    if deadline_seconds is not None and self._deadline_exceeded(start_time):
                        return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)
                    return HTTPStatus.OK, response_copy
                return status, live_body

            if stub_delay_seconds > 0:
                time.sleep(stub_delay_seconds)
                if deadline_seconds is not None and self._deadline_exceeded(start_time):
                    return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)

            response = STUB_RESPONSES.get(endpoint)
            if response is None:
                LOGGER.warning("unknown path: %s", endpoint)
                return HTTPStatus.NOT_FOUND, {"error": "unknown_endpoint", "path": endpoint}

            LOGGER.info("stub response for %s", endpoint)
            response_copy = json.loads(json.dumps(response))
            CACHE.set(cache_key, response_copy)

            if deadline_seconds is not None and self._deadline_exceeded(start_time):
                return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)

            return HTTPStatus.OK, response_copy

        def _handle_batch(
            self,
            endpoint: str,
            payload: Dict[str, Any],
            start_time: float,
        ) -> Tuple[HTTPStatus, Dict[str, Any]]:
            if not isinstance(payload, dict):
                LOGGER.warning("batch payload must be an object for %s", endpoint)
                return HTTPStatus.BAD_REQUEST, {
                    "error": "invalid_batch",
                    "detail": "request body must be an object with a 'requests' list",
                }

            requests = payload.get("requests")
            if not isinstance(requests, list):
                LOGGER.warning("batch payload missing 'requests' list for %s", endpoint)
                return HTTPStatus.BAD_REQUEST, {
                    "error": "invalid_batch",
                    "detail": "'requests' must be a list of decision payloads",
                }

            if len(requests) > BATCH_MAX_ITEMS:
                LOGGER.warning(
                    "batch payload too large for %s: %s items (limit %s)",
                    endpoint,
                    len(requests),
                    BATCH_MAX_ITEMS,
                )
                return HTTPStatus.BAD_REQUEST, {
                    "error": "batch_limit_exceeded",
                    "detail": {
                        "limit": BATCH_MAX_ITEMS,
                        "observed": len(requests),
                    },
                }

            results = []
            for idx, item in enumerate(requests):
                if deadline_seconds is not None and self._deadline_exceeded(start_time):
                    return HTTPStatus.GATEWAY_TIMEOUT, self._deadline_payload(start_time, endpoint)
                if not isinstance(item, dict):
                    LOGGER.warning("batch entry %s is not an object for %s", idx, endpoint)
                    return HTTPStatus.BAD_REQUEST, {
                        "error": "invalid_batch_entry",
                        "detail": {
                            "index": idx,
                            "message": "each entry must be an object",
                        },
                    }

                status, body = self._handle_single(endpoint, item, start_time)
                if status != HTTPStatus.OK:
                    return status, {
                        "error": "batch_item_failed",
                        "detail": {
                            "index": idx,
                            "item_error": body,
                        },
                    }
                results.append(json.loads(json.dumps(body)))

            return HTTPStatus.OK, {"results": results, "count": len(results)}

        def do_POST(self) -> None:  # noqa: N802 (HTTP verb name)
            LOGGER.debug("POST %s", self.path)
            start_time = time.monotonic()
            payload, error = self._read_json()

            if error:
                LOGGER.warning("invalid payload: %s", error)
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json", "detail": error})
                return

            if self.path in BATCH_ENDPOINTS:
                base_endpoint = BATCH_ENDPOINTS[self.path]
                status, body = self._handle_batch(base_endpoint, payload, start_time)
            else:
                status, body = self._handle_single(self.path, payload, start_time)

            if status == HTTPStatus.GATEWAY_TIMEOUT and deadline_seconds is None:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                body = {"error": "internal_error", "detail": "deadline handling misconfigured"}

            self._send_json(status, body)

    return DeciderRequestHandler


def run_server(
    host: str,
    port: int,
    mode: str,
    check_only: bool,
    deadline_ms: int,
    tick_budget: int,
    stub_delay_ms: int,
    live_router: Optional[LiveModeRouter] = None,
) -> int:
    handler = make_handler(mode, deadline_ms, tick_budget, stub_delay_ms, live_router=live_router)
    server = ThreadingHTTPServer((host, port), handler)
    LOGGER.info("Decider server (%s mode) listening on http://%s:%s", mode, host, port)

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
    live_router: Optional[LiveModeRouter] = None
    if args.mode == "live":
        try:
            live_router = _prepare_live_router(args, args.deadline_ms)
        except ValueError as exc:
            LOGGER.error("%s", exc)
            raise SystemExit(2)
        except OpenRouterError:
            raise SystemExit(2)
    exit_code = run_server(
        args.host,
        args.port,
        mode=args.mode,
        check_only=args.check,
        deadline_ms=args.deadline_ms,
        tick_budget=args.tick_budget,
        stub_delay_ms=args.stub_delay_ms,
        live_router=live_router,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
