"""Manual review script to see what the LLM actually returns with real prompts."""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

# Load actual prompts from the simulation
with open("tools/decider/prompts/firm_live.json") as f:
    firm_prompt = json.load(f)

with open("tools/decider/prompts/bank_live.json") as f:
    bank_prompt = json.load(f)

with open("tools/decider/prompts/wage_live.json") as f:
    wage_prompt = json.load(f)

# Initialize adapter
adapter = OpenRouterAdapter(
    user_agent="absfcllmpy2-manual-review",
    default_timeout=30.0,
)
model = "google/gemini-2.5-flash-lite"

# Test scenarios
firm_payload = {
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

print("="*80)
print("TESTING FIRM PRICING DECISION WITH REAL PROMPTS")
print("="*80)

# Use the ACTUAL system prompt
system_msg = firm_prompt["system"]
user_msg = firm_prompt["user_template"].replace("{payload_json}", json.dumps(firm_payload, indent=2))

print("\n### Scenario:")
print(f"  Price: {firm_payload['price']}, Unit Cost: {firm_payload['unit_cost']}")
print(f"  Inventory: {firm_payload['inventory']}, Production: {firm_payload['production_effective']}")
print(f"  Baseline price: {firm_payload['baseline']['price']}")

try:
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=100,
    )

    print("\n### LLM Decision:")
    print(json.dumps(decision, indent=2))

    print("\n### Manual Review:")
    print(f"  Direction: {decision.get('direction')}")
    print(f"  Price step: {decision.get('price_step')}")
    print(f"  Why codes: {decision.get('why', [])}")
    print(f"  Confidence: {decision.get('confidence')}")

    # Check if why codes are valid
    valid_codes = {"demand_spike", "demand_softening", "inventory_pressure",
                   "cost_push", "credit_constraint", "baseline_guard", "llm_uncertain"}
    why_codes = decision.get('why', [])

    print("\n### Validation:")
    for code in why_codes:
        if code in valid_codes:
            print(f"  ✓ '{code}' is a valid why-code")
        else:
            print(f"  ✗ '{code}' is NOT a valid why-code (expected one of {valid_codes})")

except Exception as e:
    print(f"\nError: {e}")

print("\n" + "="*80)
print("TESTING BANK CREDIT DECISION WITH REAL PROMPTS")
print("="*80)

bank_payload = {
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
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

print("\n### Scenario:")
print(f"  Borrower leverage: {bank_payload['borrower']['leverage']}")
print(f"  Profit rate: {bank_payload['borrower']['profit_rate']}")
print(f"  Loan request: {bank_payload['borrower']['loan_request']}")

system_msg = bank_prompt["system"]
user_msg = bank_prompt["user_template"].replace("{payload_json}", json.dumps(bank_payload, indent=2))

try:
    import time
    time.sleep(5)  # Avoid rate limiting

    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=101,
    )

    print("\n### LLM Decision:")
    print(json.dumps(decision, indent=2))

    print("\n### Manual Review:")
    print(f"  Approve: {decision.get('approve')}")
    print(f"  Credit limit ratio: {decision.get('credit_limit_ratio')}")
    print(f"  Spread (bps): {decision.get('spread_bps')}")
    print(f"  Why codes: {decision.get('why', [])}")
    print(f"  Confidence: {decision.get('confidence')}")

    # Check if why codes are valid
    valid_codes = {"borrower_risk", "capital_buffer_low", "capital_buffer_high",
                   "liquidity_pressure", "policy_rate_shift", "baseline_guard", "llm_uncertain"}
    why_codes = decision.get('why', [])

    print("\n### Validation:")
    for code in why_codes:
        if code in valid_codes:
            print(f"  ✓ '{code}' is a valid why-code")
        else:
            print(f"  ✗ '{code}' is NOT a valid why-code (expected one of {valid_codes})")

except Exception as e:
    print(f"\nError: {e}")

print("\n" + "="*80)
