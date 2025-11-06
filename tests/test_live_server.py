#!/usr/bin/env python3
"""Quick test of live server with realistic prompts."""

import subprocess
import time
import json
import sys
import os

try:
    import urllib.request as request
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2 as request
    from urllib2 import URLError, HTTPError


print("="*80)
print("STARTING DECIDER SERVER")
print("="*80)

# Start server
server_script = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'tools', 'decider', 'server.py'
)

print(f"Starting server from: {server_script}")
print("Configuration:")
print("  Mode: live")
print("  Model: google/gemini-2.5-flash-lite")
print("  Port: 8000")
print()

proc = subprocess.Popen(
    [
        sys.executable, server_script,
        '--mode=live',
        '--port=8000',
        '--openrouter-model-primary=google/gemini-2.5-flash-lite',
        '--skip-openrouter-credit-check'
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    bufsize=1,
    universal_newlines=True
)

print(f"Server PID: {proc.pid}")
print("Waiting 6 seconds for startup...")
time.sleep(6)

# Check health
print("\nChecking server health...")
try:
    req = request.Request("http://127.0.0.1:8000/healthz")
    resp = request.urlopen(req, timeout=5)
    health = json.loads(resp.read().decode('utf-8'))
    print(f"✓ Server is healthy!")
    print(f"  Response: {health}")
except Exception as e:
    print(f"⚠ Health check: {e}")
    print("  Trying to proceed anyway...")

# Make firm decision request
print("\n" + "="*80)
print("MAKING FIRM PRICING DECISION REQUEST")
print("="*80)

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

print("\nScenario:")
print(f"  Current price: {payload['price']}")
print(f"  Unit cost: {payload['unit_cost']}")
print(f"  Inventory: {payload['inventory']} units (high!)")
print(f"  Baseline price: {payload['baseline']['price']}")

print("\nSending HTTP POST to http://127.0.0.1:8000/decide/firm ...")

try:
    req = request.Request(
        "http://127.0.0.1:8000/decide/firm",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    start = time.time()
    resp = request.urlopen(req, timeout=60)
    elapsed_ms = (time.time() - start) * 1000

    decision = json.loads(resp.read().decode('utf-8'))

    print(f"\n✓ SUCCESS! Response received in {elapsed_ms:.0f}ms")
    print("\n" + "="*80)
    print("LLM DECISION")
    print("="*80)
    print(json.dumps(decision, indent=2))

    if "reasoning" in decision:
        print("\n" + "="*80)
        print("✓ REALISTIC PROMPT FORMAT CONFIRMED!")
        print("="*80)
        print("\nEconomic Reasoning (from LLM):")
        print(f"\n{decision['reasoning']}")
        print(f"\nDecision:")
        print(f"  Direction: {decision.get('direction')}")
        print(f"  Price step: {decision.get('price_step')}")
        print(f"  Expectation bias: {decision.get('expectation_bias')}")
        print(f"  Confidence: {decision.get('confidence')}")

        print("\n🎉 SUCCESS! The realistic prompts work in live production! 🎉")
        success = True
    else:
        print("\n⚠ Warning: No 'reasoning' field in response")
        success = False

except HTTPError as e:
    print(f"\n✗ HTTP Error {e.code}: {e.reason}")
    try:
        print(e.read().decode('utf-8'))
    except:
        pass
    success = False
except Exception as e:
    print(f"\n✗ Request failed: {e}")
    import traceback
    traceback.print_exc()
    success = False

# Cleanup
print("\n" + "="*80)
print("SHUTTING DOWN SERVER")
print("="*80)

proc.terminate()
try:
    proc.wait(timeout=5)
    print("✓ Server stopped")
except subprocess.TimeoutExpired:
    proc.kill()
    proc.wait()
    print("✓ Server killed")

sys.exit(0 if success else 1)
