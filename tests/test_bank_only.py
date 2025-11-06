#!/usr/bin/env python3
"""Quick bank-only test."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.server import BANK_LIVE_PROMPT, _validate_bank_decision
from tools.decider.providers.openrouter_adapter import OpenRouterAdapter


def test_bank():
    prompt = BANK_LIVE_PROMPT
    payload = {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 0,
        "bank_id": "B0n0",
        "country_id": 0,
        "capital": 10.0,
        "loan_supply": 20.0,
        "reserves": 5.0,
        "loan_book_value": 15.0,
        "deposits": 25.0,
        "non_allocated_money": 2.0,
        "borrower": {
            "firm_id": "F0n0",
            "country_id": 0,
            "loan_request": 4.0,
            "leverage": 1.5,
            "relative_productivity": 1.0,
            "profit_rate": 0.02,
        },
        "guards": {
            "spread_min_bps": 50.0,
            "spread_max_bps": 500.0,
        },
    }

    system_msg = prompt.system
    user_msg = prompt.build_user(payload)

    adapter = OpenRouterAdapter()
    model = "google/gemini-2.5-flash-lite"

    print("Making API call...")
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=43
    )

    print("\n✓ API call successful!")
    print(f"\nLLM Response:")
    print(json.dumps(decision, indent=2))

    validated = _validate_bank_decision(decision)
    print("\n✓ Validation passed!")

    if "risk_analysis" in validated:
        print(f"\n✓ Using NEW format: 'risk_analysis' field")
        print(f"Risk analysis: {validated['risk_analysis']}")

    print(f"\nDecision fields:")
    print(f"  Approve: {validated['approve']}")
    print(f"  Credit limit ratio: {validated['credit_limit_ratio']}")
    print(f"  Spread (bps): {validated['spread_bps']}")
    print(f"  Confidence: {validated['confidence']}")

    print("\n✓✓✓ BANK TEST PASSED ✓✓✓")


if __name__ == "__main__":
    test_bank()
