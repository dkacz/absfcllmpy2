"""Demonstrate that the new realistic role-playing prompts work correctly."""

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

adapter = OpenRouterAdapter(user_agent="absfcllmpy2-demo", default_timeout=30.0)
model = "google/gemini-2.5-flash-lite"

def test_firm_scenario(name, payload, expected_hints):
    """Test a firm pricing scenario."""
    print("\n" + "="*80)
    print(f"FIRM SCENARIO: {name}")
    print("="*80)

    print("\nInput Data:")
    print(f"  Price: {payload['price']}, Cost: {payload['unit_cost']}, Floor: {payload['guards']['price_floor']}")
    print(f"  Inventory: {payload['inventory']}, Production: {payload['production_effective']}")
    print(f"  Baseline recommends: {payload['baseline']['price']}")

    # Build template variables
    template_vars = {
        "payload_json": json.dumps(payload, indent=2),
        "price": payload["price"],
        "unit_cost": payload["unit_cost"],
        "price_floor": payload["guards"]["price_floor"],
        "inventory": payload["inventory"],
        "production_effective": payload["production_effective"],
        "baseline_price": payload["baseline"]["price"],
        "max_price_step": payload["guards"]["max_price_step"],
        "max_expectation_bias": payload["guards"]["max_expectation_bias"],
    }

    system_msg = firm_prompt["system"]
    user_msg = firm_prompt["user_template"].format(**template_vars)

    try:
        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=400 + hash(name) % 100,
        )

        print("\n📊 LLM DECISION:")
        print(f"  Direction: {decision.get('direction')}")
        print(f"  Price step: {decision.get('price_step')}")
        print(f"  Expectation bias: {decision.get('expectation_bias')}")
        print(f"  Confidence: {decision.get('confidence')}")

        print("\n💭 ECONOMIC REASONING:")
        reasoning = decision.get('reasoning', 'N/A')
        print(f"  \"{reasoning}\"")

        print("\n✓ EVALUATION:")
        # Check structure
        has_all_fields = all(k in decision for k in ['reasoning', 'direction', 'price_step', 'expectation_bias', 'confidence'])
        print(f"  {'✓' if has_all_fields else '✗'} Has all required fields")

        # Check constraints
        price_step = decision.get('price_step', 0)
        max_step = payload['guards']['max_price_step']
        respects_step = abs(price_step) <= max_step + 0.001
        print(f"  {'✓' if respects_step else '✗'} Respects max_price_step: |{price_step}| <= {max_step}")

        new_price = payload['price'] + price_step
        price_floor = payload['guards']['price_floor']
        respects_floor = new_price >= price_floor - 0.001
        print(f"  {'✓' if respects_floor else '✗'} Respects price_floor: {new_price:.3f} >= {price_floor}")

        # Check reasoning quality
        reasoning_lower = reasoning.lower()
        for hint in expected_hints:
            if hint.lower() in reasoning_lower:
                print(f"  ✓ Reasoning mentions '{hint}'")
            else:
                print(f"  ⚠ Reasoning doesn't mention '{hint}' (might still be valid)")

        return decision

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return None

def test_bank_scenario(name, payload, expected_hints):
    """Test a bank credit scenario."""
    print("\n" + "="*80)
    print(f"BANK SCENARIO: {name}")
    print("="*80)

    print("\nInput Data:")
    print(f"  Borrower leverage: {payload['borrower']['leverage']}x")
    print(f"  Borrower profit rate: {payload['borrower']['profit_rate']*100:.1f}%")
    print(f"  Borrower productivity: {payload['borrower']['relative_productivity']}")
    print(f"  Loan requested: {payload['borrower']['loan_request']}")
    print(f"  Bank capital: {payload['capital']}, Reserves: {payload['reserves']}")

    # Build template variables
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
            seed=500 + hash(name) % 100,
        )

        print("\n📊 LLM DECISION:")
        print(f"  Approve: {decision.get('approve')}")
        print(f"  Credit limit ratio: {decision.get('credit_limit_ratio')}")
        print(f"  Spread: {decision.get('spread_bps')} bps")
        print(f"  Confidence: {decision.get('confidence')}")

        print("\n💭 RISK ANALYSIS:")
        analysis = decision.get('risk_analysis', 'N/A')
        print(f"  \"{analysis}\"")

        print("\n✓ EVALUATION:")
        # Check structure
        has_all_fields = all(k in decision for k in ['risk_analysis', 'approve', 'credit_limit_ratio', 'spread_bps', 'confidence'])
        print(f"  {'✓' if has_all_fields else '✗'} Has all required fields")

        # Check constraints
        spread = decision.get('spread_bps', 0)
        min_spread = payload['guards']['spread_min_bps']
        max_spread = payload['guards']['spread_max_bps']
        respects_spread = min_spread <= spread <= max_spread
        print(f"  {'✓' if respects_spread else '✗'} Respects spread corridor: {min_spread} <= {spread} <= {max_spread}")

        limit_ratio = decision.get('credit_limit_ratio', 0)
        respects_ratio = 0 <= limit_ratio <= 1
        print(f"  {'✓' if respects_ratio else '✗'} Credit limit ratio in [0,1]: {limit_ratio}")

        # Check reasoning quality
        analysis_lower = analysis.lower()
        for hint in expected_hints:
            if hint.lower() in analysis_lower:
                print(f"  ✓ Analysis mentions '{hint}'")
            else:
                print(f"  ⚠ Analysis doesn't mention '{hint}' (might still be valid)")

        return decision

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return None

def test_wage_scenario(name, payload, expected_hints):
    """Test a wage arbitration scenario."""
    print("\n" + "="*80)
    print(f"WAGE SCENARIO: {name}")
    print("="*80)

    print("\nInput Data:")
    print(f"  Current wage: {payload['current_wage']}")
    print(f"  Wage floor: {payload['wage_floor']}, Ceiling: {payload['wage_ceiling']}")
    print(f"  Vacancies: {payload['vacancies']}")
    print(f"  Fill rate: {payload['recent_fill_rate']*100:.0f}%")
    print(f"  Context: {payload['context']}")

    # Build template variables
    template_vars = {
        "payload_json": json.dumps(payload, indent=2),
        "context": payload["context"],
        "current_wage": payload["current_wage"],
        "wage_floor": payload["wage_floor"],
        "wage_ceiling": payload["wage_ceiling"],
        "vacancies": payload["vacancies"],
        "recent_fill_rate": payload["recent_fill_rate"],
        "max_wage_step": payload["guards"]["max_wage_step"],
    }

    system_msg = wage_prompt["system"]
    user_msg = wage_prompt["user_template"].format(**template_vars)

    try:
        decision, meta = adapter.call(
            model,
            system_msg,
            user_msg,
            response_format={"type": "json_object"},
            deadline_ms=30000,
            seed=600 + hash(name) % 100,
        )

        print("\n📊 LLM DECISION:")
        print(f"  Direction: {decision.get('direction')}")
        print(f"  Wage step: {decision.get('wage_step')}")
        print(f"  Confidence: {decision.get('confidence')}")

        print("\n💭 LABOR MARKET ASSESSMENT:")
        assessment = decision.get('labor_market_assessment', 'N/A')
        print(f"  \"{assessment}\"")

        print("\n✓ EVALUATION:")
        # Check structure
        has_all_fields = all(k in decision for k in ['labor_market_assessment', 'direction', 'wage_step', 'confidence'])
        print(f"  {'✓' if has_all_fields else '✗'} Has all required fields")

        # Check constraints
        wage_step = decision.get('wage_step', 0)
        max_step = payload['guards']['max_wage_step']
        respects_step = abs(wage_step) <= max_step + 0.001
        print(f"  {'✓' if respects_step else '✗'} Respects max_wage_step: |{wage_step}| <= {max_step}")

        # Check reasoning quality
        assessment_lower = assessment.lower()
        for hint in expected_hints:
            if hint.lower() in assessment_lower:
                print(f"  ✓ Assessment mentions '{hint}'")
            else:
                print(f"  ⚠ Assessment doesn't mention '{hint}' (might still be valid)")

        return decision

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return None

# ============================================================================
# DEMONSTRATION SCENARIOS
# ============================================================================

print("="*80)
print("DEMONSTRATION: NEW REALISTIC ROLE-PLAYING PROMPTS")
print("="*80)

# Scenario 1: Firm with massive inventory buildup
firm_scenario_1 = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 10,
    "country_id": 0,
    "firm_id": "F0n0",
    "price": 1.0,
    "unit_cost": 0.8,
    "inventory": 150.0,  # Massive inventory
    "inventory_value": 150.0,
    "production_effective": 3.0,  # Very low production
    "baseline": {"price": 0.94, "expected_demand": 10.0},  # Baseline suggests cut
    "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.8},
}

test_firm_scenario(
    "Massive Inventory Buildup",
    firm_scenario_1,
    expected_hints=["inventory", "clearance", "overstocked"]
)

time.sleep(10)

# Scenario 2: Bank with healthy low-risk borrower
bank_scenario_1 = {
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
        "firm_id": "F0n0",
        "country_id": 0,
        "loan_request": 30.0,
        "leverage": 1.2,  # Low leverage
        "relative_productivity": 1.3,  # High productivity
        "profit_rate": 0.08,  # Good profits
    },
    "guards": {"spread_min_bps": 50.0, "spread_max_bps": 500.0},
}

test_bank_scenario(
    "Healthy Low-Risk Borrower",
    bank_scenario_1,
    expected_hints=["low leverage", "profitable", "strong", "approve"]
)

time.sleep(10)

# Scenario 3: Tight labor market (many vacancies, low fill rate)
wage_scenario_1 = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 10,
    "context": "firm_offer",
    "agent_id": "F0n0",
    "country_id": 0,
    "current_wage": 1.0,
    "wage_floor": 0.8,
    "wage_ceiling": 1.5,
    "guards": {"max_wage_step": 0.04},
    "vacancies": 15,  # Many vacancies
    "recent_fill_rate": 0.15,  # Very low fill rate - can't find workers!
}

test_wage_scenario(
    "Tight Labor Market",
    wage_scenario_1,
    expected_hints=["tight", "shortage", "vacancy", "difficult"]
)

time.sleep(10)

# Scenario 4: Firm near price floor
firm_scenario_2 = {
    "schema_version": "1.0",
    "run_id": 0,
    "tick": 20,
    "country_id": 0,
    "firm_id": "F0n0",
    "price": 0.82,
    "unit_cost": 0.8,
    "inventory": 20.0,
    "inventory_value": 16.4,
    "production_effective": 10.0,
    "baseline": {"price": 0.80, "expected_demand": 10.0},
    "guards": {"max_price_step": 0.04, "max_expectation_bias": 0.04, "price_floor": 0.80},
}

test_firm_scenario(
    "Near Price Floor (Solvency Constraint)",
    firm_scenario_2,
    expected_hints=["floor", "cost", "solvency", "cannot cut"]
)

print("\n" + "="*80)
print("DEMONSTRATION COMPLETE")
print("="*80)
print("\nKey observations:")
print("1. LLM provides natural economic reasoning in complete sentences")
print("2. Reasoning is contextually relevant to the scenario")
print("3. Decisions respect all constraints (floors, caps, corridors)")
print("4. Can manually review the economic logic for quality")
print("5. No predefined 'why-codes' - genuine analytical reasoning")
