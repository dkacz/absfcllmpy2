#!/usr/bin/env python3
"""
End-to-end integration test for the realistic role-playing prompts.

This test verifies that:
1. The server can load the new prompt templates
2. LLM API calls work with real OpenRouter
3. Schema validation passes with new natural language fields
4. Validation functions accept the new format
5. The complete decision flow works end-to-end
"""

import sys
import os
import time
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.server import (
    FIRM_LIVE_PROMPT, BANK_LIVE_PROMPT, WAGE_LIVE_PROMPT,
    _validate_firm_decision, _validate_bank_decision, _validate_wage_decision
)
from tools.decider.providers.openrouter_adapter import OpenRouterAdapter


def test_firm_end_to_end():
    """Test the complete firm pricing decision flow."""
    print("\n" + "="*80)
    print("FIRM PRICING DECISION - End-to-End Integration Test")
    print("="*80)

    # 1. Load the actual prompt template
    print("\n[1] Loading firm prompt template...")
    prompt = FIRM_LIVE_PROMPT
    print(f"✓ Loaded prompt successfully")
    print(f"  System prompt length: {len(prompt.system)} chars")
    print(f"  User template length: {len(prompt.user_template)} chars")

    # 2. Build payload and messages
    print("\n[2] Building prompt with test payload...")
    payload = {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 0,
        "country_id": 0,
        "firm_id": "F0n0",
        "price": 1.05,
        "unit_cost": 0.95,
        "inventory": 150,
        "inventory_value": 157.5,
        "production_effective": 120,
        "baseline": {
            "price": 1.08,
            "expected_demand": 100,
        },
        "guards": {
            "price_floor": 0.96,
            "max_price_step": 0.04,
            "max_expectation_bias": 0.04,
        },
    }

    system_msg = prompt.system
    user_msg = prompt.build_user(payload)

    print(f"✓ Built prompt successfully")
    print(f"  Payload keys: {list(payload.keys())}")
    print(f"  User message length: {len(user_msg)} chars")

    # 3. Make real API call
    print("\n[3] Making real OpenRouter API call...")
    adapter = OpenRouterAdapter()
    model = "google/gemini-2.5-flash-lite"

    try:
        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=42
        )

        print(f"✓ API call successful!")
        print(f"  Model: {meta.get('model_id', model)}")
        print(f"  Tokens: {meta.get('tokens_prompt', '?')} prompt + {meta.get('tokens_completion', '?')} completion")
        print(f"  Cost: ${meta.get('cost_usd', 0):.6f}")

    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False

    # 4. Display raw LLM response
    print("\n[4] LLM Response (raw JSON):")
    print(json.dumps(decision, indent=2))

    # 5. Validate against schema
    print("\n[5] Validating response...")
    try:
        validated = _validate_firm_decision(decision)
        print("✓ Schema validation passed!")
        print(f"  Required fields present: direction, price_step, expectation_bias, confidence")

        # Check which format was used
        if "reasoning" in validated:
            print(f"  ✓ Using NEW format: 'reasoning' field")
            print(f"    Reasoning preview: {validated['reasoning'][:100]}...")
        elif "why" in validated:
            print(f"  ✓ Using OLD format: 'why' codes")
            print(f"    Why codes: {validated['why']}")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

    # 6. Verify decision is usable
    print("\n[6] Verifying decision is usable by simulation...")
    required_keys = ["direction", "price_step", "expectation_bias", "confidence"]
    missing = [k for k in required_keys if k not in validated]

    if missing:
        print(f"✗ Missing required keys: {missing}")
        return False

    print("✓ All required simulation fields present!")
    print(f"  Direction: {validated['direction']}")
    print(f"  Price step: {validated['price_step']}")
    print(f"  Expectation bias: {validated['expectation_bias']}")
    print(f"  Confidence: {validated['confidence']}")

    print("\n✓✓✓ FIRM END-TO-END TEST PASSED ✓✓✓")
    return True


def test_bank_end_to_end():
    """Test the complete bank credit decision flow."""
    print("\n" + "="*80)
    print("BANK CREDIT DECISION - End-to-End Integration Test")
    print("="*80)

    # 1. Load prompt
    print("\n[1] Loading bank prompt template...")
    prompt = BANK_LIVE_PROMPT
    print(f"✓ Loaded prompt successfully")

    # 2. Build payload
    print("\n[2] Building prompt with test payload...")
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
    print("✓ Built prompt successfully")

    # 3. API call
    print("\n[3] Making real OpenRouter API call...")
    adapter = OpenRouterAdapter()
    model = "google/gemini-2.5-flash-lite"

    try:
        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=43
        )
        print(f"✓ API call successful!")
        print(f"  Tokens: {meta.get('tokens_prompt', '?')} + {meta.get('tokens_completion', '?')}")

    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False

    # 4. Display response
    print("\n[4] LLM Response:")
    print(json.dumps(decision, indent=2))

    # 5. Validate
    print("\n[5] Validating response...")
    try:
        validated = _validate_bank_decision(decision)
        print("✓ Schema validation passed!")

        if "risk_analysis" in validated:
            print(f"  ✓ Using NEW format: 'risk_analysis' field")
            print(f"    Analysis preview: {validated['risk_analysis'][:100]}...")
        elif "why" in validated:
            print(f"  ✓ Using OLD format: 'why' codes")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

    # 6. Verify usability
    print("\n[6] Verifying decision is usable...")
    required_keys = ["approve", "credit_limit_ratio", "spread_bps", "confidence"]
    missing = [k for k in required_keys if k not in validated]

    if missing:
        print(f"✗ Missing required keys: {missing}")
        return False

    print("✓ All required fields present!")
    print(f"  Approve: {validated['approve']}")
    print(f"  Credit limit ratio: {validated['credit_limit_ratio']}")
    print(f"  Spread (bps): {validated['spread_bps']}")
    print(f"  Confidence: {validated['confidence']}")

    print("\n✓✓✓ BANK END-TO-END TEST PASSED ✓✓✓")
    return True


def test_wage_end_to_end():
    """Test the complete wage decision flow."""
    print("\n" + "="*80)
    print("WAGE DECISION - End-to-End Integration Test")
    print("="*80)

    # 1. Load prompt
    print("\n[1] Loading wage prompt template...")
    prompt = WAGE_LIVE_PROMPT
    print(f"✓ Loaded prompt successfully")

    # 2. Build payload
    print("\n[2] Building prompt with test payload...")
    payload = {
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 0,
        "context": "firm_offer",
        "agent_id": "F0n0",
        "country_id": 0,
        "current_wage": 1.02,
        "wage_floor": 0.8,
        "wage_ceiling": 1.2,
        "guards": {
            "max_wage_step": 0.04,
        },
        "vacancies": 2,
        "recent_fill_rate": 0.7,
    }

    system_msg = prompt.system
    user_msg = prompt.build_user(payload)
    print("✓ Built prompt successfully")

    # 3. API call
    print("\n[3] Making real OpenRouter API call...")
    adapter = OpenRouterAdapter()
    model = "google/gemini-2.5-flash-lite"

    try:
        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=44
        )
        print(f"✓ API call successful!")
        print(f"  Tokens: {meta.get('tokens_prompt', '?')} + {meta.get('tokens_completion', '?')}")

    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False

    # 4. Display response
    print("\n[4] LLM Response:")
    print(json.dumps(decision, indent=2))

    # 5. Validate
    print("\n[5] Validating response...")
    try:
        validated = _validate_wage_decision(decision)
        print("✓ Schema validation passed!")

        if "labor_market_assessment" in validated:
            print(f"  ✓ Using NEW format: 'labor_market_assessment' field")
            print(f"    Assessment preview: {validated['labor_market_assessment'][:100]}...")
        elif "why" in validated:
            print(f"  ✓ Using OLD format: 'why' codes")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

    # 6. Verify usability
    print("\n[6] Verifying decision is usable...")
    required_keys = ["direction", "wage_step", "confidence"]
    missing = [k for k in required_keys if k not in validated]

    if missing:
        print(f"✗ Missing required keys: {missing}")
        return False

    print("✓ All required fields present!")
    print(f"  Direction: {validated['direction']}")
    print(f"  Wage step: {validated['wage_step']}")
    print(f"  Confidence: {validated['confidence']}")

    print("\n✓✓✓ WAGE END-TO-END TEST PASSED ✓✓✓")
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("END-TO-END INTEGRATION TEST SUITE")
    print("Testing new realistic role-playing prompts with actual OpenRouter API")
    print("="*80)

    results = []

    # Test all three decision types
    results.append(("Firm", test_firm_end_to_end()))

    # Rate limit protection
    print("\n[Waiting 8 seconds to avoid rate limits...]")
    time.sleep(8)

    results.append(("Bank", test_bank_end_to_end()))

    print("\n[Waiting 8 seconds to avoid rate limits...]")
    time.sleep(8)

    results.append(("Wage", test_wage_end_to_end()))

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:10s}: {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! The system works realistically end-to-end! 🎉")
        print("\nThe new realistic role-playing prompts are:")
        print("  ✓ Successfully loaded by the server")
        print("  ✓ Generating valid LLM responses")
        print("  ✓ Passing schema validation")
        print("  ✓ Passing validation functions")
        print("  ✓ Producing decisions usable by the simulation")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")

    sys.exit(0 if all_passed else 1)
