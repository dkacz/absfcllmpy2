"""Integration tests for OpenRouter adapter with real API calls.

These tests make actual API calls to OpenRouter and are not run by default.
Run with: python -m pytest tests/test_openrouter_integration.py -v

Environment variables required:
- OPENROUTER_API_KEY: Your OpenRouter API key

The tests use a fast, inexpensive model to minimize costs.
Expected total API calls: 4-5 (key_info + 3 decision types + model check)
"""

import os
import unittest
from tools.decider.providers.openrouter_adapter import OpenRouterAdapter, OpenRouterError


# Use Google Gemini 2.5 Flash Lite - fast and efficient
# https://openrouter.ai/google/gemini-2.5-flash-lite
TEST_MODEL = "google/gemini-2.5-flash-lite"

# Alternative models to try if primary is unavailable
FALLBACK_MODELS = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct:free",
]


def build_test_firm_payload():
    """Build a minimal firm pricing decision payload."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 5,
        "country_id": 0,
        "firm_id": "F0n0",
        "price": 1.0,
        "unit_cost": 0.8,
        "inventory": 10.0,
        "inventory_value": 10.0,
        "production_effective": 12.0,
        "baseline": {
            "price": 1.0,
            "expected_demand": 10.0,
        },
        "guards": {
            "max_price_step": 0.04,
            "max_expectation_bias": 0.04,
            "price_floor": 0.8,
        },
    }


def build_test_bank_payload():
    """Build a minimal bank credit decision payload."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 5,
        "bank_id": "B0n0",
        "country_id": 0,
        "capital": 100.0,
        "loan_supply": 200.0,
        "reserves": 50.0,
        "loan_book_value": 150.0,
        "deposits": 250.0,
        "non_allocated_money": 20.0,
        "borrower": {
            "firm_id": "F0n0",
            "country_id": 0,
            "loan_request": 40.0,
            "leverage": 1.5,
            "relative_productivity": 1.0,
            "profit_rate": 0.05,
        },
        "guards": {
            "spread_min_bps": 50.0,
            "spread_max_bps": 500.0,
        },
    }


def build_test_wage_payload():
    """Build a minimal wage decision payload."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 5,
        "context": "firm_offer",
        "agent_id": "F0n0",
        "country_id": 0,
        "current_wage": 1.0,
        "wage_floor": 0.8,
        "wage_ceiling": 1.2,
        "guards": {
            "max_wage_step": 0.04,
        },
        "vacancies": 3,
        "recent_fill_rate": 0.6,
    }


@unittest.skipUnless(
    os.getenv("OPENROUTER_API_KEY"),
    "OPENROUTER_API_KEY not set - skipping integration tests"
)
class OpenRouterIntegrationTests(unittest.TestCase):
    """Integration tests with real OpenRouter API calls.

    These tests verify end-to-end functionality with actual API responses.
    They are designed to minimize API usage while testing critical paths.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize OpenRouter adapter once for all tests."""
        cls.adapter = OpenRouterAdapter(
            user_agent="absfcllmpy2-integration-tests",
            default_timeout=30.0,
        )
        cls.model = TEST_MODEL

        # Try to verify model exists and supports structured outputs
        # If this fails, we'll still proceed and let individual tests handle errors
        cls.supports_structured = True  # Assume true by default
        try:
            cls.supports_structured = cls.adapter.supports_structured_outputs(
                cls.model, deadline_ms=30000
            )
            if not cls.supports_structured:
                print(f"\nNote: {cls.model} doesn't support structured outputs, "
                      f"will use json_object mode")
        except OpenRouterError as e:
            print(f"\nWarning: Could not verify structured outputs support: {e.reason}")
            print("Proceeding with tests anyway...")

    def test_01_key_info(self):
        """Test fetching API key information and credit status."""
        try:
            data, elapsed_ms = self.adapter.key_info(deadline_ms=10000)

            # Verify response structure
            self.assertIsInstance(data, dict)
            self.assertGreater(elapsed_ms, 0)

            # Log credit info if available
            if "data" in data:
                attrs = data.get("data", {}).get("attributes", {})
                usage = attrs.get("usage", {})
                credit = attrs.get("credit_balance")

                print(f"\n  Credit balance: ${credit}")
                print(f"  Usage: {usage.get('remaining', 'N/A')}/{usage.get('total', 'N/A')}")

        except OpenRouterError as e:
            self.fail(f"key_info failed: {e.reason} - {e.detail}")

    def test_02_firm_pricing_decision(self):
        """Test a real firm pricing decision with structured outputs."""
        payload = build_test_firm_payload()

        system_msg = (
            "You are a pricing officer making pricing decisions. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a pricing decision with: direction (raise/hold/cut), "
            "price_step (number), expectation_bias (number), "
            "why (array of strings), confidence (0-1)."
        )

        response_format = {
            "type": "json_schema" if self.supports_structured else "json_object",
            "json_schema": {
                "name": "firm_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["raise", "hold", "cut"]},
                        "price_step": {"type": "number"},
                        "expectation_bias": {"type": "number"},
                        "why": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["direction", "price_step", "expectation_bias", "why", "confidence"],
                    "additionalProperties": False,
                },
            } if self.supports_structured else None,
        }

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=42,
            )

            # Verify response structure
            self.assertIsInstance(decision, dict)
            self.assertIn("direction", decision)
            self.assertIn(decision["direction"], ["raise", "hold", "cut"])
            self.assertIn("price_step", decision)
            self.assertIsInstance(decision["price_step"], (int, float))
            self.assertIn("confidence", decision)
            self.assertGreaterEqual(decision["confidence"], 0.0)
            self.assertLessEqual(decision["confidence"], 1.0)

            # Verify metadata
            self.assertIn("model", meta)
            self.assertIn("usage", meta)
            self.assertGreater(meta["elapsed_ms"], 0)

            print(f"\n  Decision: {decision['direction']}, "
                  f"step: {decision['price_step']:.3f}, "
                  f"confidence: {decision['confidence']:.2f}")
            print(f"  Tokens: {meta['usage'].get('prompt_tokens', 0)} prompt, "
                  f"{meta['usage'].get('completion_tokens', 0)} completion")
            print(f"  Elapsed: {meta['elapsed_ms']:.1f}ms")

        except OpenRouterError as e:
            error_msg = f"Firm decision failed: {e.reason} - {e.detail}"
            if e.body:
                error_msg += f"\nResponse body: {e.body}"
            self.fail(error_msg)

    def test_03_bank_credit_decision(self):
        """Test a real bank credit decision with structured outputs."""
        payload = build_test_bank_payload()

        system_msg = (
            "You are a bank credit officer making lending decisions. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a credit decision with: approve (boolean), "
            "credit_limit_ratio (0-1), spread_bps (number), "
            "why (array of strings), confidence (0-1)."
        )

        response_format = {
            "type": "json_schema" if self.supports_structured else "json_object",
            "json_schema": {
                "name": "bank_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "approve": {"type": "boolean"},
                        "credit_limit_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                        "spread_bps": {"type": "number"},
                        "why": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["approve", "credit_limit_ratio", "spread_bps", "why", "confidence"],
                    "additionalProperties": False,
                },
            } if self.supports_structured else None,
        }

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=42,
            )

            # Verify response structure
            self.assertIsInstance(decision, dict)
            self.assertIn("approve", decision)
            self.assertIsInstance(decision["approve"], bool)
            self.assertIn("credit_limit_ratio", decision)
            self.assertGreaterEqual(decision["credit_limit_ratio"], 0.0)
            self.assertLessEqual(decision["credit_limit_ratio"], 1.0)
            self.assertIn("spread_bps", decision)

            print(f"\n  Approve: {decision['approve']}, "
                  f"limit: {decision['credit_limit_ratio']:.2f}, "
                  f"spread: {decision['spread_bps']:.0f}bps")
            print(f"  Tokens: {meta['usage'].get('prompt_tokens', 0)} prompt, "
                  f"{meta['usage'].get('completion_tokens', 0)} completion")

        except OpenRouterError as e:
            error_msg = f"Bank decision failed: {e.reason} - {e.detail}"
            if e.body:
                error_msg += f"\nResponse body: {e.body}"
            self.fail(error_msg)

    def test_04_wage_decision(self):
        """Test a real wage adjustment decision with structured outputs."""
        payload = build_test_wage_payload()

        system_msg = (
            "You are a human resources officer making wage decisions. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a wage decision with: direction (raise/hold/cut), "
            "wage_step (number), why (array of strings), confidence (0-1)."
        )

        response_format = {
            "type": "json_schema" if self.supports_structured else "json_object",
            "json_schema": {
                "name": "wage_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["raise", "hold", "cut"]},
                        "wage_step": {"type": "number"},
                        "why": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["direction", "wage_step", "why", "confidence"],
                    "additionalProperties": False,
                },
            } if self.supports_structured else None,
        }

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=42,
            )

            # Verify response structure
            self.assertIsInstance(decision, dict)
            self.assertIn("direction", decision)
            self.assertIn(decision["direction"], ["raise", "hold", "cut"])
            self.assertIn("wage_step", decision)
            self.assertIsInstance(decision["wage_step"], (int, float))

            print(f"\n  Direction: {decision['direction']}, "
                  f"step: {decision['wage_step']:.3f}")
            print(f"  Tokens: {meta['usage'].get('prompt_tokens', 0)} prompt, "
                  f"{meta['usage'].get('completion_tokens', 0)} completion")

        except OpenRouterError as e:
            error_msg = f"Wage decision failed: {e.reason} - {e.detail}"
            if e.body:
                error_msg += f"\nResponse body: {e.body}"
            self.fail(error_msg)


if __name__ == "__main__":
    # Run with verbose output to see API call details
    unittest.main(verbosity=2)
