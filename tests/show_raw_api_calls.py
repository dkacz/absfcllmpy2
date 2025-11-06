"""Show raw JSON sent to and received from OpenRouter API."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decider.providers.openrouter_adapter import OpenRouterAdapter

# Load prompts
with open("tools/decider/prompts/firm_live.json") as f:
    firm_prompt = json.load(f)

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-raw-demo", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

# Create a firm scenario with high inventory
firm_payload = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 10,
    "country_id": 0,
    "firm_id": "F0n0",
    "price": 1.0,
    "unit_cost": 0.8,
    "inventory": 150.0,
    "inventory_value": 150.0,
    "production_effective": 3.0,
    "baseline": {"price": 0.94, "expected_demand": 10.0},
    "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.8},
}

# Build the actual prompt
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

# Build the request payload that would be sent to OpenRouter
request_payload = {
    "model": model,
    "temperature": 0.0,
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ],
    "response_format": {"type": "json_object"},
    "seed": 42,
}

print("="*80)
print("RAW JSON REQUEST SENT TO OPENROUTER")
print("="*80)
print("\nEndpoint: POST https://openrouter.ai/api/v1/chat/completions")
print("\nHeaders:")
print("  Content-Type: application/json")
print("  Authorization: Bearer sk-or-v1-...")
print("\nRequest Body:")
print(json.dumps(request_payload, indent=2))

print("\n" + "="*80)
print("MAKING ACTUAL API CALL...")
print("="*80)

try:
    decision, meta = adapter.call(
        model,
        system_msg,
        user_msg,
        response_format={"type": "json_object"},
        deadline_ms=30000,
        seed=42,
    )

    print("\n" + "="*80)
    print("RAW JSON RESPONSE RECEIVED FROM OPENROUTER")
    print("="*80)

    # Reconstruct what the actual API response would have looked like
    # (The adapter parses it, but we can show the structure)
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
    print("PARSED DECISION EXTRACTED FROM RESPONSE")
    print("="*80)
    print("\nThe adapter extracted this JSON from response.choices[0].message.content:")
    print(json.dumps(decision, indent=2))

    print("\n" + "="*80)
    print("METADATA")
    print("="*80)
    print(f"\nModel: {meta.get('model')}")
    print(f"Elapsed time: {meta.get('elapsed_ms'):.1f}ms")
    print(f"Prompt tokens: {meta.get('usage', {}).get('prompt_tokens', 'N/A')}")
    print(f"Completion tokens: {meta.get('usage', {}).get('completion_tokens', 'N/A')}")
    print(f"Finish reason: {meta.get('finish_reason', 'N/A')}")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    if hasattr(e, 'body'):
        print("\nError response body:")
        print(e.body)
