"""OpenRouter client adapter for the Decider live mode."""

from __future__ import annotations

import json
import os
import socket
import time
from contextlib import closing
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple

try:
    from urllib import request, error  # type: ignore
except ImportError:  # pragma: no cover
    raise

Transport = Callable[[request.Request, Optional[float]], Any]

API_BASE_URL = "https://openrouter.ai/api/v1"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MODELS_PATH = "/models"
DEFAULT_USER_AGENT = "absfcllmpy2-decider"

_MIN_TIMEOUT_SECONDS = 0.05
_DEFAULT_TIMEOUT_SECONDS = 10.0
_DEADLINE_BUFFER_SECONDS = 0.05


class OpenRouterError(Exception):
    """Raised when the OpenRouter adapter cannot serve a request."""

    def __init__(self, reason: str, detail: Optional[str] = None,
                 status: Optional[int] = None, body: Any = None) -> None:
        super(OpenRouterError, self).__init__(detail or reason)
        self.reason = reason
        self.detail = detail
        self.status = status
        self.body = body


class OpenRouterAdapter:
    """Lightweight adapter around the OpenRouter Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = API_BASE_URL,
        transport: Optional[Transport] = None,
        default_timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        deadline_buffer: float = _DEADLINE_BUFFER_SECONDS,
        min_timeout: float = _MIN_TIMEOUT_SECONDS,
        referer: Optional[str] = None,
        title: Optional[str] = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        self.transport = transport or request.urlopen
        self.default_timeout = float(default_timeout)
        self.deadline_buffer = max(0.0, float(deadline_buffer))
        self.min_timeout = max(0.0, float(min_timeout)) or _MIN_TIMEOUT_SECONDS
        self.referer = referer if referer is not None else os.getenv("OPENROUTER_HTTP_REFERER")
        self.title = title if title is not None else os.getenv("OPENROUTER_TITLE")
        self.user_agent = user_agent
        self._model_cache: Optional[Set[str]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def call(
        self,
        model_slug: str,
        system_message: str,
        user_message: str,
        *,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        deadline_ms: Optional[int] = None,
        expect_json: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Invoke the chat/completions endpoint and return ``(decision, meta)``.

        ``meta`` always contains ``model`` (string), ``usage`` (dict) and
        ``elapsed_ms`` (float).  When ``expect_json`` is ``True`` the returned
        decision is parsed as JSON.
        """

        if not model_slug:
            raise ValueError("model_slug is required")

        payload: Dict[str, Any] = {
            "model": model_slug,
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": system_message or ""},
                {"role": "user", "content": user_message or ""},
            ],
        }
        if seed is not None:
            payload["seed"] = int(seed)
        if response_format:
            payload["response_format"] = response_format
        if extra_params:
            payload.update(extra_params)

        data, elapsed_ms = self._request_json(
            "POST",
            CHAT_COMPLETIONS_PATH,
            payload=payload,
            deadline_ms=deadline_ms,
        )

        try:
            choices = data["choices"]
            if not choices:
                raise KeyError("choices")
            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content")
        except (KeyError, TypeError, IndexError) as exc:
            raise OpenRouterError(
                "decode_error",
                detail="malformed OpenRouter response: missing choices/message",
                body=data,
            ) from exc

        decision: Any = content
        if expect_json:
            try:
                decision = json.loads(content)
            except (TypeError, ValueError) as exc:
                raise OpenRouterError(
                    "decode_error",
                    detail="invalid JSON content from OpenRouter",
                    body=content,
                ) from exc

        meta = {
            "model": data.get("model", model_slug),
            "usage": data.get("usage", {}),
            "elapsed_ms": elapsed_ms,
            "finish_reason": first_choice.get("finish_reason"),
        }

        return decision, meta

    def model_exists(self, slug: str, *, deadline_ms: Optional[int] = None) -> bool:
        """Return ``True`` if ``slug`` is present in ``/models`` response."""

        if not slug:
            return False

        if self._model_cache is not None:
            return slug in self._model_cache

        data, _ = self._request_json("GET", MODELS_PATH, deadline_ms=deadline_ms)
        models = set(self._extract_model_ids(data))
        self._model_cache = models
        return slug in models

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        deadline_ms: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], float]:
        response_bytes, elapsed_ms = self._request(
            method,
            path,
            payload=payload,
            deadline_ms=deadline_ms,
        )
        text = self._ensure_text(response_bytes)
        try:
            return json.loads(text), elapsed_ms
        except ValueError as exc:
            raise OpenRouterError(
                "decode_error",
                detail="invalid JSON body from OpenRouter",
                body=text,
            ) from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        deadline_ms: Optional[int] = None,
    ) -> Tuple[bytes, float]:
        url = self._build_url(path)
        headers = self._build_headers()
        data_bytes: Optional[bytes] = None
        if payload is not None:
            data_bytes = json.dumps(payload).encode("utf-8")

        req = request.Request(url, data=data_bytes, headers=headers, method=method)
        timeout = self._resolve_timeout(deadline_ms)
        start = time.monotonic()

        try:
            with closing(self.transport(req, timeout=timeout)) as resp:
                status = getattr(resp, "status", None) or getattr(resp, "code", None)
                body = resp.read()
                if status and status >= 400:
                    parsed = self._safe_json(body)
                    raise OpenRouterError(
                        "http_error",
                        detail="HTTP %d from %s" % (status, url),
                        status=status,
                        body=parsed,
                    )
        except error.HTTPError as exc:
            body = exc.read()
            parsed = self._safe_json(body)
            raise OpenRouterError(
                "http_error",
                detail="HTTP %d from %s" % (exc.code, url),
                status=exc.code,
                body=parsed,
            ) from exc
        except socket.timeout as exc:
            raise OpenRouterError(
                "timeout",
                detail="request to %s exceeded timeout" % url,
            ) from exc
        except error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise OpenRouterError(
                    "timeout",
                    detail="request to %s exceeded timeout" % url,
                ) from exc
            raise OpenRouterError(
                "connection_error",
                detail=str(exc.reason),
            ) from exc
        except OpenRouterError:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch-all
            raise OpenRouterError("unexpected_error", detail=str(exc)) from exc
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000.0

        return body, elapsed_ms

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer %s" % self.api_key,
            "User-Agent": self.user_agent,
        }
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-Title"] = self.title
        return headers

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _resolve_timeout(self, deadline_ms: Optional[int]) -> float:
        if deadline_ms is None or deadline_ms <= 0:
            timeout = self.default_timeout
        else:
            deadline_seconds = deadline_ms / 1000.0
            timeout = max(deadline_seconds - self.deadline_buffer, 0.0)
            if timeout <= 0.0:
                timeout = self.min_timeout
        if timeout < self.min_timeout:
            timeout = self.min_timeout
        return timeout

    @staticmethod
    def _ensure_text(raw: Any) -> str:
        if isinstance(raw, str):
            return raw
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)

    @staticmethod
    def _safe_json(raw: Any) -> Any:
        try:
            text = OpenRouterAdapter._ensure_text(raw)
            return json.loads(text)
        except (TypeError, ValueError):
            return raw

    @staticmethod
    def _extract_model_ids(payload: Dict[str, Any]) -> Iterable[str]:
        models: Iterable[str] = []
        if isinstance(payload.get("data"), list):
            models = [OpenRouterAdapter._model_identifier(item) for item in payload["data"]]
        elif isinstance(payload.get("models"), list):
            models = [OpenRouterAdapter._model_identifier(item) for item in payload["models"]]
        return [m for m in models if m]

    @staticmethod
    def _model_identifier(entry: Any) -> Optional[str]:
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            for key in ("id", "slug", "name"):
                value = entry.get(key)
                if isinstance(value, str) and value:
                    return value
        return None


__all__ = ["OpenRouterAdapter", "OpenRouterError"]
