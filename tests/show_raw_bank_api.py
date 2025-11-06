"""Show raw JSON for bank credit decision API call."""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

# Load prompts
with open("tools/decider/prompts/bank_live.json") as f:
    bank_prompt = json.load(f)

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-raw-demo", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

# Create a high-risk borrower scenario
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
        "firm_id": "F-DISTRESS",
        "country_id": 0,
        "loan_request": 100.0,
        "leverage": 4.5,
        "relative_productivity": 0.7,
        "profit_rate": -0.01,
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

# Build the actual prompt
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

# Build the request payload
request_payload = {
    "model": model,
    "temperature": 0.0,
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ],
    "response_format": {"type": "json_object"},
    "seed": 43,
}

print("="*80)
print("BANK CREDIT DECISION: RAW API REQUEST")
print("="*80)
print("\nScenario: High-risk borrower (leverage 4.5x, -1% profits)")
print("\nEndpoint: POST https://openrouter.ai/api/v1/chat/completions")
print("\nRequest Body:")
print(json.dumps(request_payload, indent=2))

print("\n" + "="*80)
print("MAKING ACTUAL API CALL...")
print("="*80)

time.sleep(5)  # Avoid rate limiting

try:
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=43,
    )

    print("\n" + "="*80)
    print("RAW API RESPONSE")
    print("="*80)

    api_response = {
        "id": "gen-...",
        "model": meta.get("model", model),
        "object": "chat.completion",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(decision)
                },
                "finish_reason": meta.get("finish_reason", "stop")
            }
        ],
        "usage": meta.get("usage", {}),
    }

    print("\nResponse Body:")
    print(json.dumps(api_response, indent=2))

    print("\n" + "="*80)
    print("PARSED CREDIT DECISION")
    print("="*80)
    print(json.dumps(decision, indent=2))

    print("\n" + "="*80)
    print("KEY OBSERVATIONS")
    print("="*80)
    print(f"\n✓ Decision: {'APPROVE' if decision.get('approve') else 'DENY'}")
    print(f"✓ Spread: {decision.get('spread_bps')} bps")
    print(f"✓ Credit limit: {decision.get('credit_limit_ratio', 0)*100:.0f}%")
    print(f"✓ Confidence: {decision.get('confidence', 0)*100:.0f}%")
    print(f"\n✓ Risk Analysis:")
    print(f"  \"{decision.get('risk_analysis', 'N/A')}\"")

    print(f"\n✓ Token usage:")
    print(f"  Prompt: {meta.get('usage', {}).get('prompt_tokens', 'N/A')} tokens")
    print(f"  Completion: {meta.get('usage', {}).get('completion_tokens', 'N/A')} tokens")
    print(f"  Time: {meta.get('elapsed_ms', 0):.1f}ms")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    if hasattr(e, 'body'):
        print("\nError response body:")
        print(e.body)
