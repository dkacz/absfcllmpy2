"""Test only firm decision to review justifications."""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

# Load actual prompts
with open("tools/decider/prompts/firm_live.json") as f:
    firm_prompt = json.load(f)

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-manual-review", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

# Test 3 scenarios
scenarios = [
    {
        "name": "Normal scenario - price at baseline",
        "payload": {
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
            "baseline": {"price": 1.0, "expected_demand": 10.0},
            "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.8},
        }
    },
    {
        "name": "High inventory - should suggest inventory_pressure",
        "payload": {
            "schema_version": "1.0",
            "run_id": 0,
            "tick": 10,
            "country_id": 0,
            "firm_id": "F0n0",
            "price": 1.0,
            "unit_cost": 0.8,
            "inventory": 100.0,  # Very high!
            "inventory_value": 100.0,
            "production_effective": 5.0,
            "baseline": {"price": 0.96, "expected_demand": 10.0},  # Baseline suggests cutting
            "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.8},
        }
    },
    {
        "name": "Near price floor - should show baseline_guard",
        "payload": {
            "schema_version": "1.0",
            "run_id": 0,
            "tick": 15,
            "country_id": 0,
            "firm_id": "F0n0",
            "price": 0.82,  # Close to floor
            "unit_cost": 0.8,
            "inventory": 20.0,
            "inventory_value": 16.4,
            "production_effective": 10.0,
            "baseline": {"price": 0.80, "expected_demand": 10.0},  # At floor
            "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.80},
        }
    },
]

valid_codes = {"demand_spike", "demand_softening", "inventory_pressure",
               "cost_push", "credit_constraint", "baseline_guard", "llm_uncertain"}

for i, scenario in enumerate(scenarios):
    print("\n" + "="*80)
    print(f"SCENARIO {i+1}: {scenario['name']}")
    print("="*80)

    payload = scenario['payload']
    print(f"\n  Price: {payload['price']}, Unit Cost: {payload['unit_cost']}, Floor: {payload['guards']['price_floor']}")
    print(f"  Inventory: {payload['inventory']}, Production: {payload['production_effective']}")
    print(f"  Baseline price: {payload['baseline']['price']}")

    system_msg = firm_prompt["system"]
    user_msg = firm_prompt["user_template"].replace("{payload_json}", json.dumps(payload, indent=2))

    try:
        if i > 0:
            print("\n  Waiting 10s to avoid rate limits...")
            time.sleep(10)

        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=200 + i,
        )

        print("\n### Full LLM Response:")
        print(json.dumps(decision, indent=2))

        print("\n### Manual Review:")
        print(f"  Direction: {decision.get('direction')}")
        print(f"  Price step: {decision.get('price_step')}")
        print(f"  Expectation bias: {decision.get('expectation_bias')}")
        print(f"  Why: {decision.get('why', [])}")
        print(f"  Confidence: {decision.get('confidence')}")
        if 'comment' in decision:
            print(f"  Comment: {decision['comment']}")

        # Validate why codes
        why_codes = decision.get('why', [])
        print("\n### Why-Code Validation:")
        if not why_codes:
            print("  ✗ NO WHY-CODES PROVIDED")
        else:
            for code in why_codes:
                if code in valid_codes:
                    print(f"  ✓ '{code}' - valid code")
                else:
                    print(f"  ✗ '{code}' - INVALID (not in predefined set)")

        # Check constraints
        print("\n### Constraint Check:")
        new_price = payload['price'] + decision.get('price_step', 0)
        price_floor = payload['guards']['price_floor']
        if new_price < price_floor:
            print(f"  ✗ PRICE FLOOR VIOLATED: {new_price:.3f} < {price_floor:.3f}")
        else:
            print(f"  ✓ Price floor respected: {new_price:.3f} >= {price_floor:.3f}")

        price_step = abs(decision.get('price_step', 0))
        max_step = payload['guards']['max_price_step']
        if price_step > max_step:
            print(f"  ✗ MAX STEP VIOLATED: |{price_step:.4f}| > {max_step:.4f}")
        else:
            print(f"  ✓ Max step respected: |{price_step:.4f}| <= {max_step:.4f}")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")

print("\n" + "="*80)
print("REVIEW COMPLETE")
print("="*80)
