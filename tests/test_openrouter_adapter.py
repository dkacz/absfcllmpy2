import json
import os
import socket
import unittest
from unittest import mock

from tools.decider.providers.openrouter_adapter import (
    OpenRouterAdapter,
    OpenRouterError,
)


class StubResponse(object):
    def __init__(self, status=200, body=b""):
        self.status = status
        self.code = status
        if isinstance(body, bytes):
            self._body = body
        else:
            self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class RecordingTransport(object):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request_obj, timeout=None):
        self.calls.append({
            "request": request_obj,
            "timeout": timeout,
        })
        if not self.responses:
            raise AssertionError("no responses configured")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class OpenRouterAdapterTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_model_exists_true(self):
        payload = json.dumps({"data": [{"id": "meta/example"}]})
        transport = RecordingTransport([StubResponse(200, payload)])
        adapter = OpenRouterAdapter(transport=transport)

        self.assertTrue(adapter.model_exists("meta/example"))
        self.assertFalse(transport.responses)
        call = transport.calls[0]
        self.assertEqual(call["request"].get_header("Authorization"), "Bearer test-key")

    def test_model_exists_timeout(self):
        transport = RecordingTransport([socket.timeout("deadline exceeded")])
        adapter = OpenRouterAdapter(transport=transport)

        with self.assertRaises(OpenRouterError) as ctx:
            adapter.model_exists("meta/example", deadline_ms=100)
        self.assertEqual(ctx.exception.reason, "timeout")
        self.assertLessEqual(transport.calls[0]["timeout"], 0.1)

    def test_call_returns_parsed_decision(self):
        payload = {
            "model": "openrouter/test",
            "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
            "choices": [
                {
                    "message": {"content": json.dumps({"direction": "hold"})},
                    "finish_reason": "stop",
                }
            ],
        }
        transport = RecordingTransport([StubResponse(200, json.dumps(payload))])
        adapter = OpenRouterAdapter(transport=transport)

        decision, meta = adapter.call(
            "openrouter/test",
            system_message="sys",
            user_message="user",
            deadline_ms=200,
        )

        self.assertEqual(decision, {"direction": "hold"})
        self.assertEqual(meta["model"], "openrouter/test")
        self.assertEqual(meta["usage"]["total_tokens"], 12)
        self.assertIn("elapsed_ms", meta)
        self.assertEqual(meta["finish_reason"], "stop")
        self.assertLess(transport.calls[0]["timeout"], 0.2)

    def test_call_invalid_json_content_raises_decode_error(self):
        payload = {
            "model": "openrouter/test",
            "usage": {},
            "choices": [
                {
                    "message": {"content": "not-json"},
                    "finish_reason": "stop",
                }
            ],
        }
        transport = RecordingTransport([StubResponse(200, json.dumps(payload))])
        adapter = OpenRouterAdapter(transport=transport)

        with self.assertRaises(OpenRouterError) as ctx:
            adapter.call("openrouter/test", "sys", "user", expect_json=True)
        self.assertEqual(ctx.exception.reason, "decode_error")

    def test_call_http_error_maps_reason(self):
        payload = json.dumps({"error": "bad"})
        transport = RecordingTransport([StubResponse(500, payload)])
        adapter = OpenRouterAdapter(transport=transport)

        with self.assertRaises(OpenRouterError) as ctx:
            adapter.call("openrouter/test", "sys", "user")
        self.assertEqual(ctx.exception.reason, "http_error")
        self.assertEqual(ctx.exception.status, 500)


if __name__ == "__main__":
    unittest.main()
