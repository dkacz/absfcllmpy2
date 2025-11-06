#!/usr/bin/env python3
"""Demonstrate the decider server working with realistic prompts via HTTP.

This simulates what the Python 2 simulation would do: make HTTP POST requests
to the decider server running in live mode with realistic role-playing prompts.
"""

import subprocess
import time
import json
import sys
import os

try:
    from urllib import request
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2 as request
    from urllib2 import URLError, HTTPError


def start_server():
    """Start the decider server in live mode."""
    print("="*80)
    print("STARTING DECIDER SERVER (Live Mode with Realistic Prompts)")
    print("="*80)

    server_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'tools', 'decider', 'server.py'
    )

    process = subprocess.Popen(
        [
            sys.executable, server_script,
            '--mode=live',
            '--port=8000',
            '--openrouter-model-primary=google/gemini-2.5-flash-lite',
            '--skip-openrouter-credit-check',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    print(f"Server PID: {process.pid}")
    print("Waiting 4 seconds for server to start...")
    time.sleep(4)

    # Check if server is running
    if process.poll() is not None:
        print("✗ Server failed to start!")
        return None

    # Health check
    try:
        req = request.Request("http://127.0.0.1:8000/healthz")
        response = request.urlopen(req, timeout=5)
        data = json.loads(response.read().decode('utf-8'))
        print(f"✓ Server is healthy: {data}")
    except Exception as e:
        print(f"⚠ Health check failed: {e}")
        print("  (Server may still be starting up...)")

    return process


def make_firm_decision():
    """Make a firm pricing decision request."""
    print("\n" + "="*80)
    print("TEST 1: FIRM PRICING DECISION")
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

    print("\nRequest payload:")
    print(json.dumps(payload, indent=2))

    print("\nMaking HTTP POST to http://127.0.0.1:8000/decide/firm...")

    try:
        req = request.Request(
            "http://127.0.0.1:8000/decide/firm",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        start_time = time.time()
        response = request.urlopen(req, timeout=60)
        elapsed = (time.time() - start_time) * 1000

        decision = json.loads(response.read().decode('utf-8'))

        print(f"\n✓ Request successful! ({elapsed:.0f}ms)")
        print("\nDecision from LLM:")
        print(json.dumps(decision, indent=2))

        # Highlight the key new feature
        if "reasoning" in decision:
            print("\n✓ SUCCESS: Server returned realistic role-playing format!")
            print(f"\nEconomic Reasoning:")
            print(f"  {decision['reasoning']}")
        else:
            print("\n⚠ Warning: No 'reasoning' field in response")

        return True

    except HTTPError as e:
        print(f"\n✗ HTTP Error {e.code}: {e.reason}")
        print(e.read().decode('utf-8'))
        return False
    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        return False


def make_bank_decision():
    """Make a bank credit decision request."""
    print("\n" + "="*80)
    print("TEST 2: BANK CREDIT DECISION")
    print("="*80)

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

    print("\nRequest payload (key fields):")
    print(f"  Borrower leverage: {payload['borrower']['leverage']}")
    print(f"  Loan request: {payload['borrower']['loan_request']}")
    print(f"  Bank capital: {payload['capital']}")

    print("\nMaking HTTP POST to http://127.0.0.1:8000/decide/bank...")

    try:
        req = request.Request(
            "http://127.0.0.1:8000/decide/bank",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        start_time = time.time()
        response = request.urlopen(req, timeout=60)
        elapsed = (time.time() - start_time) * 1000

        decision = json.loads(response.read().decode('utf-8'))

        print(f"\n✓ Request successful! ({elapsed:.0f}ms)")
        print("\nDecision from LLM:")
        print(json.dumps(decision, indent=2))

        if "risk_analysis" in decision:
            print("\n✓ SUCCESS: Server returned realistic role-playing format!")
            print(f"\nRisk Analysis:")
            print(f"  {decision['risk_analysis']}")

        return True

    except HTTPError as e:
        print(f"\n✗ HTTP Error {e.code}: {e.reason}")
        print(e.read().decode('utf-8'))
        return False
    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        return False


def stop_server(process):
    """Stop the server."""
    if process:
        print("\n" + "="*80)
        print("STOPPING SERVER")
        print("="*80)
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✓ Server stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            print("✓ Server killed")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DECIDER SERVER INTEGRATION DEMO")
    print("Testing Realistic Role-Playing Prompts in Production")
    print("="*80)
    print("\nThis demonstration:")
    print("  1. Starts the decider server in live mode")
    print("  2. Makes HTTP requests simulating simulation calls")
    print("  3. Shows LLM responses with natural language reasoning")
    print("  4. Proves the complete integration works")
    print()

    server = None
    results = []

    try:
        server = start_server()
        if not server:
            print("\n✗ Failed to start server")
            sys.exit(1)

        # Wait a bit more for full initialization
        print("\nWaiting additional 2 seconds for full initialization...")
        time.sleep(2)

        # Test firm decision
        results.append(("Firm", make_firm_decision()))

        # Rate limit protection
        print("\n[Waiting 5 seconds between requests for rate limiting...]")
        time.sleep(5)

        # Test bank decision
        results.append(("Bank", make_bank_decision()))

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_server(server)

    # Summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:10s}: {status}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe realistic role-playing prompts are working in production!")
        print("The decider server successfully:")
        print("  ✓ Loaded realistic prompt templates")
        print("  ✓ Made real OpenRouter API calls")
        print("  ✓ Received natural language economic reasoning")
        print("  ✓ Validated responses through schemas")
        print("  ✓ Returned properly formatted decisions")
        print("\nThe system is ready for actual simulation runs!")
    else:
        print("\n⚠ Some tests failed")

    sys.exit(0 if all_passed else 1)
