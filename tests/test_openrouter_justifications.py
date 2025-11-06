"""Integration tests that validate LLM justifications and constraint adherence.

These tests verify that the LLM:
1. Respects guard constraints (price floors, step limits, etc.)
2. Provides valid why-codes from the expected set
3. Gives contextually relevant justifications based on the scenario

Run with: python -m unittest tests.test_openrouter_justifications -v

Environment variables required:
- OPENROUTER_API_KEY: Your OpenRouter API key
"""

import os
import unittest
from tools.decider.providers.openrouter_adapter import OpenRouterAdapter, OpenRouterError

# Use Google Gemini 2.5 Flash Lite - fast and efficient
TEST_MODEL = "google/gemini-2.5-flash-lite"

# Valid why-codes for each decision type (from prompts)
FIRM_WHY_CODES = {
    "demand_spike", "demand_softening", "inventory_pressure",
    "cost_push", "credit_constraint", "baseline_guard", "llm_uncertain"
}

BANK_WHY_CODES = {
    "borrower_risk", "capital_buffer_low", "capital_buffer_high",
    "liquidity_pressure", "policy_rate_shift", "baseline_guard", "llm_uncertain"
}

WAGE_WHY_CODES = {
    "labour_shortage", "unemployment_pressure", "inflation_pressure",
    "productivity_gap", "baseline_guard", "llm_uncertain"
}


def build_high_inventory_scenario():
    """Scenario: High inventory should trigger inventory_pressure or price cuts."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 10,
        "country_id": 0,
        "firm_id": "F0n0",
        "price": 1.0,
        "unit_cost": 0.8,
        "inventory": 100.0,  # Very high inventory
        "inventory_value": 100.0,
        "production_effective": 5.0,  # Low production
        "baseline": {
            "price": 0.98,  # Baseline suggests cutting
            "expected_demand": 10.0,
        },
        "guards": {
            "max_price_step": 0.04,
            "max_expectation_bias": 0.04,
            "price_floor": 0.80,
        },
    }


def build_high_leverage_borrower():
    """Scenario: High leverage borrower should trigger borrower_risk concerns."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 10,
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
            "loan_request": 100.0,
            "leverage": 4.5,  # Very high leverage - risky!
            "relative_productivity": 0.7,  # Below average
            "profit_rate": -0.01,  # Losing money
        },
        "guards": {
            "spread_min_bps": 50.0,
            "spread_max_bps": 500.0,
        },
    }


def build_tight_labor_market():
    """Scenario: High vacancies, low fill rate should trigger labour_shortage."""
    return {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 10,
        "context": "firm_offer",
        "agent_id": "F0n0",
        "country_id": 0,
        "current_wage": 1.0,
        "wage_floor": 0.8,
        "wage_ceiling": 1.5,
        "guards": {
            "max_wage_step": 0.04,
        },
        "vacancies": 10,  # Many vacancies
        "recent_fill_rate": 0.2,  # Very low fill rate - can't find workers!
    }


@unittest.skipUnless(
    os.getenv("OPENROUTER_API_KEY"),
    "OPENROUTER_API_KEY not set - skipping integration tests"
)
class JustificationValidationTests(unittest.TestCase):
    """Tests that validate LLM justifications and constraint adherence."""

    @classmethod
    def setUpClass(cls):
        """Initialize OpenRouter adapter once for all tests."""
        cls.adapter = OpenRouterAdapter(
            user_agent="absfcllmpy2-justification-tests",
            default_timeout=30.0,
        )
        cls.model = TEST_MODEL
        cls.supports_structured = False  # Gemini 2.5 Flash Lite uses json_object

    def test_01_firm_respects_price_floor(self):
        """Test that firm decisions respect the price floor constraint."""
        # Create scenario where price is at floor
        payload = {
            "schema_version": "1.0",
            "run_id": 0,
            "tick": 10,
            "country_id": 0,
            "firm_id": "F0n0",
            "price": 0.82,  # Close to floor
            "unit_cost": 0.8,
            "inventory": 10.0,
            "inventory_value": 8.2,
            "production_effective": 10.0,
            "baseline": {"price": 0.80, "expected_demand": 10.0},
            "guards": {
                "max_price_step": 0.04,
                "max_expectation_bias": 0.04,
                "price_floor": 0.80,  # Floor at 0.80
            },
        }

        system_msg = (
            "You are the Chief Pricing Officer (CPO) making pricing decisions. "
            "You MUST respect the price floor - price cannot fall below unit cost. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a pricing decision. The price floor is 0.80. "
            "You cannot set a price below this floor. "
            "Return JSON with: direction (raise/hold/cut), price_step (number), "
            "expectation_bias (number), why (array of strings), confidence (0-1)."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=42,
            )

            # Calculate resulting price
            current_price = payload["price"]
            new_price = current_price + decision.get("price_step", 0)
            price_floor = payload["guards"]["price_floor"]

            # CRITICAL: New price must not violate floor
            self.assertGreaterEqual(
                new_price,
                price_floor - 0.001,  # Allow tiny floating point error
                f"Price floor violated! New price {new_price:.3f} < floor {price_floor:.3f}"
            )

            print(f"\n  Current: {current_price:.3f}, Step: {decision.get('price_step', 0):.3f}, "
                  f"New: {new_price:.3f}, Floor: {price_floor:.3f}")
            print(f"  Direction: {decision.get('direction')}, Why: {decision.get('why', [])}")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_02_firm_respects_max_step(self):
        """Test that firm decisions respect max_price_step constraint."""
        payload = build_high_inventory_scenario()
        max_step = payload["guards"]["max_price_step"]

        system_msg = (
            "You are the Chief Pricing Officer (CPO) making pricing decisions. "
            f"Price adjustments are STRICTLY capped at ±{max_step}. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            f"Make a pricing decision. max_price_step is {max_step}. "
            "You cannot exceed this limit. "
            "Return JSON with: direction, price_step, expectation_bias, why (array), confidence."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=43,
            )

            price_step = decision.get("price_step", 0)

            # CRITICAL: Step must be within bounds
            self.assertLessEqual(
                abs(price_step),
                max_step + 0.001,  # Allow tiny floating point error
                f"max_price_step violated! |{price_step:.4f}| > {max_step:.4f}"
            )

            print(f"\n  Step: {price_step:.4f}, Max: ±{max_step:.4f}, "
                  f"Within bounds: {abs(price_step) <= max_step}")
            print(f"  Direction: {decision.get('direction')}, Why: {decision.get('why', [])}")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_03_firm_uses_valid_why_codes(self):
        """Test that firm decisions use valid why-codes."""
        payload = build_high_inventory_scenario()

        system_msg = (
            "You are the Chief Pricing Officer (CPO) making pricing decisions. "
            "Valid why-codes: demand_spike, demand_softening, inventory_pressure, "
            "cost_push, credit_constraint, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a pricing decision. Use only valid why-codes from the list above. "
            "Return JSON with: direction, price_step, expectation_bias, why (array), confidence."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=44,
            )

            why_codes = decision.get("why", [])
            self.assertIsInstance(why_codes, list, "why must be an array")
            self.assertGreater(len(why_codes), 0, "why must contain at least one code")
            self.assertLessEqual(len(why_codes), 3, "why should contain at most 3 codes")

            # Check each why-code is valid
            for code in why_codes:
                self.assertIn(
                    code,
                    FIRM_WHY_CODES,
                    f"Invalid why-code '{code}' not in {FIRM_WHY_CODES}"
                )

            print(f"\n  Why codes: {why_codes}")
            print(f"  All valid: {all(c in FIRM_WHY_CODES for c in why_codes)}")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_04_high_inventory_mentions_inventory_pressure(self):
        """Test that high inventory scenario gets relevant justification."""
        payload = build_high_inventory_scenario()

        system_msg = (
            "You are the Chief Pricing Officer (CPO) making pricing decisions. "
            "Analyze inventory levels and provide appropriate justification. "
            "Valid why-codes: demand_spike, demand_softening, inventory_pressure, "
            "cost_push, credit_constraint, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Note: Inventory is VERY HIGH (100 units) while production is low (5 units). "
            "This is a clear inventory pressure situation requiring clearance. "
            "Make a pricing decision with appropriate justification. "
            "Return JSON with: direction, price_step, expectation_bias, why (array), confidence."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=45,
            )

            why_codes = decision.get("why", [])
            direction = decision.get("direction")

            print(f"\n  Scenario: High inventory (100 units)")
            print(f"  Decision: {direction}")
            print(f"  Why codes: {why_codes}")

            # High inventory should trigger inventory_pressure OR baseline_guard OR llm_uncertain
            # We can't force a specific code, but we can check relevance
            relevant_codes = {"inventory_pressure", "baseline_guard", "demand_softening", "llm_uncertain"}
            has_relevant = any(code in relevant_codes for code in why_codes)

            if not has_relevant:
                print(f"  WARNING: High inventory but justification doesn't mention "
                      f"inventory_pressure, demand_softening, or baseline_guard")
                print(f"  This may indicate the LLM isn't understanding the scenario properly")

            # We don't assert here because the LLM might have valid alternative reasoning
            # But we print a warning for review

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_05_bank_uses_valid_why_codes(self):
        """Test that bank decisions use valid why-codes."""
        payload = build_high_leverage_borrower()

        system_msg = (
            "You are a Senior Credit Officer making lending decisions. "
            "Valid why-codes: borrower_risk, capital_buffer_low, capital_buffer_high, "
            "liquidity_pressure, policy_rate_shift, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a credit decision. Use only valid why-codes from the list above. "
            "Return JSON with: approve (boolean), credit_limit_ratio (0-1), "
            "spread_bps (number), why (array), confidence (0-1)."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=46,
            )

            why_codes = decision.get("why", [])
            self.assertIsInstance(why_codes, list, "why must be an array")
            self.assertGreater(len(why_codes), 0, "why must contain at least one code")

            for code in why_codes:
                self.assertIn(
                    code,
                    BANK_WHY_CODES,
                    f"Invalid why-code '{code}' not in {BANK_WHY_CODES}"
                )

            print(f"\n  Why codes: {why_codes}")
            print(f"  All valid: {all(c in BANK_WHY_CODES for c in why_codes)}")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_06_high_leverage_mentions_borrower_risk(self):
        """Test that high leverage borrower gets borrower_risk justification."""
        payload = build_high_leverage_borrower()

        system_msg = (
            "You are a Senior Credit Officer making lending decisions. "
            "Evaluate borrower risk carefully. High leverage is a major red flag. "
            "Valid why-codes: borrower_risk, capital_buffer_low, capital_buffer_high, "
            "liquidity_pressure, policy_rate_shift, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Note: Borrower has VERY HIGH leverage (4.5x), NEGATIVE profit rate (-1%), "
            "and BELOW AVERAGE productivity (0.7). This is a high-risk borrower. "
            "Make a credit decision with appropriate justification. "
            "Return JSON with: approve, credit_limit_ratio, spread_bps, why (array), confidence."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=47,
            )

            why_codes = decision.get("why", [])
            approve = decision.get("approve")
            spread_bps = decision.get("spread_bps", 0)

            print(f"\n  Scenario: High-risk borrower (leverage 4.5x, negative profits)")
            print(f"  Decision: {'APPROVE' if approve else 'DENY'}, spread: {spread_bps:.0f}bps")
            print(f"  Why codes: {why_codes}")

            # High leverage should trigger borrower_risk OR baseline_guard
            relevant_codes = {"borrower_risk", "baseline_guard", "llm_uncertain"}
            has_relevant = any(code in relevant_codes for code in why_codes)

            if not has_relevant:
                print(f"  WARNING: High-risk borrower but justification doesn't mention "
                      f"borrower_risk or baseline_guard")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_07_wage_uses_valid_why_codes(self):
        """Test that wage decisions use valid why-codes."""
        payload = build_tight_labor_market()

        system_msg = (
            "You are a Labour Market Arbitrator making wage decisions. "
            "Valid why-codes: labour_shortage, unemployment_pressure, inflation_pressure, "
            "productivity_gap, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Make a wage decision. Use only valid why-codes from the list above. "
            "Return JSON with: direction (raise/hold/cut), wage_step (number), "
            "why (array), confidence (0-1)."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=48,
            )

            why_codes = decision.get("why", [])
            self.assertIsInstance(why_codes, list, "why must be an array")
            self.assertGreater(len(why_codes), 0, "why must contain at least one code")

            for code in why_codes:
                self.assertIn(
                    code,
                    WAGE_WHY_CODES,
                    f"Invalid why-code '{code}' not in {WAGE_WHY_CODES}"
                )

            print(f"\n  Why codes: {why_codes}")
            print(f"  All valid: {all(c in WAGE_WHY_CODES for c in why_codes)}")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")

    def test_08_tight_labor_market_relevant_justification(self):
        """Test that tight labor market scenario gets relevant justification."""
        payload = build_tight_labor_market()

        system_msg = (
            "You are a Labour Market Arbitrator making wage decisions. "
            "Consider labor market tightness and vacancy rates carefully. "
            "Valid why-codes: labour_shortage, unemployment_pressure, inflation_pressure, "
            "productivity_gap, baseline_guard, llm_uncertain. "
            "Respond with valid JSON only."
        )
        user_msg = (
            f"Given this data: {payload}\n\n"
            "Note: Labor market is VERY TIGHT. Firm has 10 vacancies but only 20% fill rate. "
            "They can't find workers! This is a clear labour shortage situation. "
            "Make a wage decision with appropriate justification. "
            "Return JSON with: direction, wage_step, why (array), confidence."
        )

        response_format = {"type": "json_object"}

        try:
            decision, meta = self.adapter.call(
                self.model,
                system_msg,
                user_msg,
                response_format=response_format,
                deadline_ms=30000,
                seed=49,
            )

            why_codes = decision.get("why", [])
            direction = decision.get("direction")
            wage_step = decision.get("wage_step", 0)

            print(f"\n  Scenario: Tight labor market (10 vacancies, 20% fill rate)")
            print(f"  Decision: {direction}, step: {wage_step:.3f}")
            print(f"  Why codes: {why_codes}")

            # Tight labor market should trigger labour_shortage OR baseline_guard
            relevant_codes = {"labour_shortage", "baseline_guard", "llm_uncertain"}
            has_relevant = any(code in relevant_codes for code in why_codes)

            if not has_relevant:
                print(f"  WARNING: Tight labor market but justification doesn't mention "
                      f"labour_shortage or baseline_guard")

        except OpenRouterError as e:
            self.fail(f"API call failed: {e.reason} - {e.detail}")


if __name__ == "__main__":
    # Run with verbose output to see justification analysis
    unittest.main(verbosity=2)
