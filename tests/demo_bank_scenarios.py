"""Demonstrate bank credit decisions with new prompts."""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

with open("tools/decider/prompts/bank_live.json") as f:
    bank_prompt = json.load(f)

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-demo", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

def test_bank(name, payload):
    print("="*80)
    print(f"BANK SCENARIO: {name}")
    print("="*80)

    print("\n📋 Borrower Profile:")
    print(f"  Leverage: {payload['borrower']['leverage']}x")
    print(f"  Profit rate: {payload['borrower']['profit_rate']*100:+.1f}%")
    print(f"  Productivity: {payload['borrower']['relative_productivity']:.2f} (relative)")
    print(f"  Loan request: ${payload['borrower']['loan_request']}")

    print("\n🏦 Bank Position:")
    print(f"  Capital: ${payload['capital']}")
    print(f"  Reserves: ${payload['reserves']}")
    print(f"  Loan book: ${payload['loan_book_value']}")

    template_vars = {
        "payload_json": json.dumps(payload, indent=2),
        "firm_id": payload["borrower"]["firm_id"],
        "loan_request": payload["borrower"]["loan_request"],
        "leverage": payload["borrower"]["leverage"],
        "profit_rate": payload["borrower"]["profit_rate"],
        "relative_productivity": payload["borrower"]["relative_productivity"],
        "capital": payload["capital"],
        "reserves": payload["reserves"],
        "loan_book_value": payload["loan_book_value"],
        "deposits": payload["deposits"],
        "spread_min_bps": payload["guards"]["spread_min_bps"],
        "spread_max_bps": payload["guards"]["spread_max_bps"],
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
            seed=700 + hash(name) % 100,
        )

        print("\n📊 CREDIT DECISION:")
        approve = decision.get('approve')
        print(f"  {'✅ APPROVE' if approve else '❌ DENY'}")
        print(f"  Credit limit: {decision.get('credit_limit_ratio', 0)*100:.0f}% of requested")
        print(f"  Spread: {decision.get('spread_bps', 0):.0f} bps")
        print(f"  Confidence: {decision.get('confidence', 0):.0%}")

        print("\n💭 CREDIT OFFICER'S RISK ANALYSIS:")
        analysis = decision.get('risk_analysis', 'N/A')
        # Wrap text nicely
        import textwrap
        wrapped = textwrap.fill(analysis, width=75, initial_indent="  ", subsequent_indent="  ")
        print(wrapped)

        print("\n✓ CHECKS:")
        spread = decision.get('spread_bps', 0)
        min_s, max_s = payload['guards']['spread_min_bps'], payload['guards']['spread_max_bps']
        print(f"  {'✓' if min_s <= spread <= max_s else '✗'} Spread in corridor: {spread:.0f} bps [{min_s:.0f}-{max_s:.0f}]")

        ratio = decision.get('credit_limit_ratio', 0)
        print(f"  {'✓' if 0 <= ratio <= 1 else '✗'} Credit ratio valid: {ratio:.2f} [0-1]")

        # Economic sense check
        if payload['borrower']['leverage'] > 3 and approve:
            print(f"  ⚠ High leverage ({payload['borrower']['leverage']}x) but approved - check reasoning")
        if payload['borrower']['profit_rate'] < 0 and approve:
            print(f"  ⚠ Negative profits but approved - check reasoning")

        return decision

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return None

# Scenario 1: Excellent borrower
print("\n")
scenario_excellent = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 5,
    "bank_id": "B0n0",
    "country_id": 0,
    "capital": 100.0,
    "loan_supply": 200.0,
    "reserves": 80.0,
    "loan_book_value": 120.0,
    "deposits": 250.0,
    "non_allocated_money": 50.0,
    "borrower": {
        "firm_id": "F-EXCELLENT",
        "country_id": 0,
        "loan_request": 30.0,
        "leverage": 1.2,  # Low leverage
        "relative_productivity": 1.3,  # High productivity
        "profit_rate": 0.08,  # Strong profits
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

test_bank("Excellent Borrower - Low Risk", scenario_excellent)

time.sleep(12)

# Scenario 2: Risky borrower
scenario_risky = {
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
        "firm_id": "F-DISTRESS",
        "country_id": 0,
        "loan_request": 100.0,  # Large request
        "leverage": 4.5,  # Very high leverage
        "relative_productivity": 0.7,  # Below average
        "profit_rate": -0.01,  # Losing money
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

test_bank("Distressed Borrower - High Risk", scenario_risky)

time.sleep(12)

# Scenario 3: Marginal borrower
scenario_marginal = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 5,
    "bank_id": "B0n0",
    "country_id": 0,
    "capital": 100.0,
    "loan_supply": 200.0,
    "reserves": 60.0,
    "loan_book_value": 140.0,
    "deposits": 250.0,
    "non_allocated_money": 30.0,
    "borrower": {
        "firm_id": "F-MARGINAL",
        "country_id": 0,
        "loan_request": 50.0,
        "leverage": 2.8,  # Moderately high
        "relative_productivity": 0.95,  # Slightly below average
        "profit_rate": 0.015,  # Small positive profits
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

test_bank("Marginal Borrower - Medium Risk", scenario_marginal)

print("\n" + "="*80)
print("BANK SCENARIOS COMPLETE")
print("="*80)
