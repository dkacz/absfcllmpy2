"""Test the redesigned realistic role-playing prompts."""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

# Load the new prompts
with open("tools/decider/prompts/firm_live.json") as f:
    firm_prompt = json.load(f)

with open("tools/decider/prompts/bank_live.json") as f:
    bank_prompt = json.load(f)

with open("tools/decider/prompts/wage_live.json") as f:
    wage_prompt = json.load(f)

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-prompt-test", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

print("="*80)
print("TESTING NEW REALISTIC ROLE-PLAYING PROMPTS")
print("="*80)

# Test 1: Firm with high inventory
print("\n" + "="*80)
print("TEST 1: FIRM PRICING - High Inventory Scenario")
print("="*80)

firm_payload = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 10,
    "country_id": 0,
    "firm_id": "F0n0",
    "price": 1.0,
    "unit_cost": 0.8,
    "inventory": 100.0,  # Very high
    "inventory_value": 100.0,
    "production_effective": 5.0,  # Low production
    "baseline": {"price": 0.96, "expected_demand": 10.0},
    "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.8},
}

print("\nScenario: High inventory (100 units), low production (5), baseline suggests cut to 0.96")

# Build user message manually with template variables
template_vars = {
    "payload_json": json.dumps(firm_payload, indent=2),
    "price": firm_payload["price"],
    "unit_cost": firm_payload["unit_cost"],
    "price_floor": firm_payload["guards"]["price_floor"],
    "inventory": firm_payload["inventory"],
    "production_effective": firm_payload["production_effective"],
    "baseline_price": firm_payload["baseline"]["price"],
    "max_price_step": firm_payload["guards"]["max_price_step"],
    "max_expectation_bias": firm_payload["guards"]["max_expectation_bias"],
}

system_msg = firm_prompt["system"]
user_msg = firm_prompt["user_template"].format(**template_vars)

print(f"\nGenerated prompt (first 500 chars):\n{user_msg[:500]}...\n")

try:
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=300,
    )

    print("### LLM RESPONSE:")
    print(json.dumps(decision, indent=2))

    print("\n### EVALUATION:")
    if "reasoning" in decision:
        print(f"✓ Has 'reasoning' field")
        print(f"  Reasoning: {decision['reasoning']}")
    else:
        print(f"✗ Missing 'reasoning' field")

    if "direction" in decision:
        print(f"✓ Has 'direction': {decision['direction']}")
    else:
        print(f"✗ Missing 'direction'")

    if "price_step" in decision:
        print(f"✓ Has 'price_step': {decision['price_step']}")
        if abs(decision['price_step']) <= 0.04:
            print(f"  ✓ Respects constraint |{decision['price_step']}| <= 0.04")
        else:
            print(f"  ✗ VIOLATES constraint |{decision['price_step']}| > 0.04")
    else:
        print(f"✗ Missing 'price_step'")

    # Check if reasoning mentions inventory
    if "reasoning" in decision:
        reasoning_lower = decision["reasoning"].lower()
        if "inventor" in reasoning_lower:
            print(f"✓ Reasoning mentions inventory")
        else:
            print(f"⚠ Reasoning does NOT mention inventory (but has 100 units!)")

except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2: Bank with high-risk borrower
print("\n" + "="*80)
print("TEST 2: BANK CREDIT - High Risk Borrower")
print("="*80)

time.sleep(10)  # Avoid rate limits

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
        "loan_request": 100.0,
        "leverage": 4.5,  # Very high!
        "relative_productivity": 0.7,
        "profit_rate": -0.01,  # Losing money!
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

print("\nScenario: High leverage (4.5x), negative profit rate (-1%), low productivity (0.7)")

template_vars = {
    "payload_json": json.dumps(bank_payload, indent=2),
    "firm_id": bank_payload["borrower"]["firm_id"],
    "loan_request": bank_payload["borrower"]["loan_request"],
    "leverage": bank_payload["borrower"]["leverage"],
    "profit_rate": bank_payload["borrower"]["profit_rate"],
    "relative_productivity": bank_payload["borrower"]["relative_productivity"],
    "capital": bank_payload["capital"],
    "reserves": bank_payload["reserves"],
    "loan_book_value": bank_payload["loan_book_value"],
    "deposits": bank_payload["deposits"],
    "spread_min_bps": bank_payload["guards"]["spread_min_bps"],
    "spread_max_bps": bank_payload["guards"]["spread_max_bps"],
}

system_msg = bank_prompt["system"]
user_msg = bank_prompt["user_template"].format(**template_vars)

try:
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=301,
    )

    print("### LLM RESPONSE:")
    print(json.dumps(decision, indent=2))

    print("\n### EVALUATION:")
    if "risk_analysis" in decision:
        print(f"✓ Has 'risk_analysis' field")
        print(f"  Analysis: {decision['risk_analysis']}")
    else:
        print(f"✗ Missing 'risk_analysis' field")

    if "approve" in decision:
        print(f"✓ Has 'approve': {decision['approve']}")
        if not decision['approve']:
            print(f"  ✓ Correctly denies high-risk borrower")
        else:
            print(f"  ⚠ Approves high-risk borrower (leverage 4.5x, negative profits)")
    else:
        print(f"✗ Missing 'approve'")

    # Check if reasoning mentions leverage or risk
    if "risk_analysis" in decision:
        analysis_lower = decision["risk_analysis"].lower()
        if "leverag" in analysis_lower or "risk" in analysis_lower:
            print(f"✓ Analysis mentions leverage/risk")
        else:
            print(f"⚠ Analysis does NOT mention leverage/risk")

except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "="*80)
print("TESTS COMPLETE")
print("="*80)
