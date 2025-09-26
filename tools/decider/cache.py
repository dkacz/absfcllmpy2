# -*- coding: utf-8 -*-
"""Deterministic decision cache for the Decider service."""

from __future__ import absolute_import

import hashlib
import json
import threading
from typing import Any, Dict, Optional, Tuple


def _normalise_payload(payload):
    """Return a JSON string with stable ordering for hashing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class DecisionCache(object):
    """Thread-safe cache keyed by endpoint + payload hash."""

    def __init__(self):
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key_material(endpoint: str, payload: Dict[str, Any], temperature: float) -> str:
        if temperature != 0.0:
            raise ValueError("temperature must be 0.0 for deterministic cache")
        base = {
            "endpoint": endpoint,
            "payload": payload,
            "temperature": 0.0,
        }
        return _normalise_payload(base)

    def make_key(self, endpoint: str, payload: Dict[str, Any], temperature: float = 0.0) -> str:
        raw = self._key_material(endpoint, payload, temperature)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        temperature: float = 0.0,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        key = self.make_key(endpoint, payload, temperature)
        with self._lock:
            value = self._entries.get(key)
        if value is None:
            return key, None
        return key, json.loads(json.dumps(value))

    def set(self, key: str, response: Dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = json.loads(json.dumps(response))

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


__all__ = ["DecisionCache"]
