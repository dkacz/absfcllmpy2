import time
import unittest
from http import HTTPStatus

from tools.decider import server
from tools.decider.providers.openrouter_adapter import OpenRouterError


def build_firm_payload():
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 0,
        "country_id": 0,
        "firm_id": "F0n0",
        "price": 1.0,
        "unit_cost": 0.8,
        "inventory": 0.0,
        "inventory_value": 0.0,
        "production_effective": 0.0,
        "baseline": {
            "price": 1.0,
            "expected_demand": 1.0,
        },
        "guards": {
            "max_price_step": 0.04,
            "max_expectation_bias": 0.04,
            "price_floor": 0.6,
        },
    }


class DummyAdapter(object):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(
        self,
        model_slug,
        system_message,
        user_message,
        *,
        response_format=None,
        seed=None,
        deadline_ms=None,
        expect_json=True,
        extra_params=None,
    ):
        self.calls.append(
            {
                "model": model_slug,
                "system": system_message,
                "user": user_message,
                "deadline_ms": deadline_ms,
            }
        )
        if not self.responses:
            raise AssertionError("no adapter responses configured")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        decision, meta = item
        return decision, meta

    def model_exists(self, slug, deadline_ms=None):
        return True


class DeciderServerLiveTests(unittest.TestCase):
    def setUp(self):
        server.CACHE.clear()

    def _make_handler(self, mode="stub", deadline_ms=200, adapter=None, primary="primary-model", fallback=None):
        live_router = None
        if mode == "live":
            live_router = server.LiveModeRouter(
                adapter=adapter,
                primary_model=primary,
                fallback_model=fallback,
                server_deadline_ms=deadline_ms,
                prompts=server._default_live_prompts(),
                validators=server.LIVE_RESPONSE_VALIDATORS,
            )
        handler_cls = server.make_handler(mode, deadline_ms, tick_budget=0, stub_delay_ms=0, live_router=live_router)
        handler = handler_cls.__new__(handler_cls)
        return handler

    def test_stub_mode_returns_stub_response(self):
        handler = self._make_handler(mode="stub")
        payload = build_firm_payload()
        status, body = handler._handle_single("/decide/firm", payload, time.monotonic())
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(body, server.STUB_RESPONSES["/decide/firm"])

    def test_live_mode_primary_success(self):
        decision = {
            "direction": "hold",
            "price_step": 0.0,
            "expectation_bias": 0.0,
            "why": ["baseline_guard"],
            "confidence": 0.8,
        }
        meta = {
            "model": "primary-model",
            "usage": {"prompt_tokens": 12, "completion_tokens": 5},
            "elapsed_ms": 15.0,
        }
        adapter = DummyAdapter([(decision, meta)])
        handler = self._make_handler(mode="live", adapter=adapter)
        payload = build_firm_payload()
        status, body = handler._handle_single("/decide/firm", payload, time.monotonic())
        self.assertEqual(status, HTTPStatus.OK)
        self.assertAlmostEqual(body["price_step"], 0.0)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(adapter.calls[0]["model"], "primary-model")

    def test_live_mode_fallback_on_primary_failure(self):
        decision = {
            "direction": "cut",
            "price_step": -0.01,
            "expectation_bias": -0.02,
            "why": ["inventory_pressure", "cost_push"],
            "confidence": 0.6,
        }
        meta = {
            "model": "fallback-model",
            "usage": {"prompt_tokens": 8, "completion_tokens": 4},
            "elapsed_ms": 12.0,
        }
        adapter = DummyAdapter([
            OpenRouterError("timeout", detail="deadline exceeded"),
            (decision, meta),
        ])
        handler = self._make_handler(mode="live", adapter=adapter, fallback="fallback-model")
        payload = build_firm_payload()
        status, body = handler._handle_single("/decide/firm", payload, time.monotonic())
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(body["why"], ["inventory_pressure", "cost_push"])
        self.assertEqual(body["why_code"], "inventory_pressure")
        self.assertEqual(len(adapter.calls), 2)
        self.assertEqual(adapter.calls[0]["model"], "primary-model")
        self.assertEqual(adapter.calls[1]["model"], "fallback-model")

    def test_live_mode_failure_returns_error(self):
        adapter = DummyAdapter([
            OpenRouterError("timeout", detail="deadline exceeded"),
            OpenRouterError("http_error", detail="bad gateway", status=502),
        ])
        handler = self._make_handler(mode="live", adapter=adapter, fallback="fallback-model")
        payload = build_firm_payload()
        status, body = handler._handle_single("/decide/firm", payload, time.monotonic())
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(body["error"], "llm_live_failed")
        self.assertEqual(len(body["detail"]["attempts"]), 2)

    def test_live_mode_schema_violation_returns_error(self):
        decision = {
            "direction": "raise",
            "price_step": 0.1,
            "expectation_bias": 0.0,
            "why": ["baseline_guard"],
            "confidence": 0.5,
        }
        meta = {"model": "primary-model", "usage": {}}
        adapter = DummyAdapter([(decision, meta)])
        handler = self._make_handler(mode="live", adapter=adapter)
        payload = build_firm_payload()
        status, body = handler._handle_single("/decide/firm", payload, time.monotonic())
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(body["error"], "llm_live_failed")
        attempts = body["detail"]["attempts"]
        self.assertEqual(attempts[0]["reason"], "schema_error")


if __name__ == "__main__":
    unittest.main()
