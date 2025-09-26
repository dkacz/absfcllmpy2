# -*- coding: utf-8 -*-
"""HTTP client for the local Decider service (Python 2).

This module provides a minimal wrapper around ``urllib2`` so the legacy Caiani
simulation (Python 2) can talk to the Python 3 Decider server.  The client
exposes helper methods for the three decision endpoints and surfaces a tuple of
``(response_dict, error_info)`` to the caller.  ``response_dict`` is returned on
HTTP 200 with valid JSON; otherwise ``None`` is returned together with a short
error descriptor that the simulation can log before falling back to the baseline
heuristic.
"""

from __future__ import absolute_import

import json
import logging
import socket
import urllib2

LOGGER = logging.getLogger(__name__)

try:  # Python 2 only
    text_type = unicode  # type: ignore  # noqa: F821 - defined at runtime
except NameError:  # pragma: no cover - Python 3 fallback for tooling
    text_type = str

try:
    bytes_type = bytes
except NameError:  # pragma: no cover - legacy Python fallback
    bytes_type = str

_DECISION_ENDPOINTS = {
    'firm': '/decide/firm',
    'bank': '/decide/bank',
    'wage': '/decide/wage',
}


class LLMBridgeClient(object):
    """Minimal HTTP client for the Decider stub/live service."""

    def __init__(self, base_url, timeout=0.2, headers=None):
        if not base_url:
            raise ValueError('base_url is required')
        # Normalise whitespace and trailing slashes so path joins are predictable.
        base_url = base_url.strip()
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.timeout = float(timeout) if timeout is not None else None
        self.headers = {'Content-Type': 'application/json'}
        if headers:
            self.headers.update(headers)

    def decide_firm(self, payload):
        """Call the firm endpoint.

        Returns ``(response_dict, error_info)``.
        """

        return self._post_json(_DECISION_ENDPOINTS['firm'], payload)

    def decide_bank(self, payload):
        """Call the bank endpoint (loan approval & spread)."""

        return self._post_json(_DECISION_ENDPOINTS['bank'], payload)

    def decide_wage(self, payload):
        """Call the wage endpoint (worker reservation / firm offer)."""

        return self._post_json(_DECISION_ENDPOINTS['wage'], payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post_json(self, path, payload):
        """POST ``payload`` (dict) to ``path`` and return ``(data, error)``.

        ``data`` is a Python object parsed from JSON when the response is 200
        and well-formed.  Otherwise ``None`` is returned along with ``error``, a
        dict containing at least a ``reason`` key.  The caller can log this and
        fall back to the baseline decision logic.
        """

        if not isinstance(payload, dict):
            raise TypeError('payload must be a dict (got %r)' % type(payload))

        url = self._build_url(path)
        data = json.dumps(payload)
        request = urllib2.Request(url, data=data, headers=self.headers)

        try:
            response = urllib2.urlopen(request, timeout=self.timeout)
        except urllib2.HTTPError as exc:
            error_body = exc.read()
            parsed = self._safe_json(error_body)
            return None, {
                'reason': 'http_error',
                'status': exc.code,
                'body': parsed,
            }
        except urllib2.URLError as exc:
            # ``URLError`` wraps a variety of socket issues.  Timeouts may be
            # surfaced either as ``socket.timeout`` or via ``str(reason)``.
            if isinstance(exc.reason, socket.timeout):
                return None, self._timeout_error(url)
            return None, {
                'reason': 'connection_error',
                'detail': str(exc.reason),
            }
        except socket.timeout:
            return None, self._timeout_error(url)
        except Exception as exc:  # pragma: no cover - defensive catch-all
            return None, {
                'reason': 'unexpected_error',
                'detail': str(exc),
            }

        status = getattr(response, 'code', None) or response.getcode()
        body = response.read()
        if status != 200:
            parsed = self._safe_json(body)
            return None, {
                'reason': 'http_error',
                'status': status,
                'body': parsed,
            }

        try:
            text = self._ensure_text(body)
            return json.loads(text), None
        except ValueError as exc:
            return None, {
                'reason': 'decode_error',
                'detail': 'invalid JSON response: %s' % exc,
            }

    def _build_url(self, path):
        if not path:
            raise ValueError('path is required')
        if not path.startswith('/'):
            path = '/' + path
        return self.base_url + path

    @staticmethod
    def _safe_json(raw_body):
        if raw_body is None:
            return None
        try:
            text = LLMBridgeClient._ensure_text(raw_body)
            return json.loads(text)
        except (TypeError, ValueError):
            return raw_body

    @staticmethod
    def _ensure_text(raw):
        if isinstance(raw, text_type):
            return raw
        if isinstance(raw, bytes_type):
            try:
                return raw.decode('utf-8')
            except AttributeError:
                return raw
        return raw

    @staticmethod
    def _timeout_error(url):
        return {
            'reason': 'timeout',
            'detail': 'request to %s exceeded the configured timeout' % url,
        }


__all__ = ['LLMBridgeClient']
