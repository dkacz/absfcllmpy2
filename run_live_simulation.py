#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run a very short ABSFC simulation with actual LLM calls."""

from __future__ import print_function
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code'))

from parameter import Parameter
from timing import run_simulation

print("="*80)
print("RUNNING ABSFC SIMULATION WITH LIVE LLM CALLS")
print("="*80)
print()

# Create minimal configuration for very short run
para = Parameter()

# VERY short simulation (just 2 cycles to minimize API calls)
para.ncycle = 2
para.Lrun = [42]
para.weSeedRun = 'yes'

# Reduce scale to minimize API usage
para.ncountry = 2  # Just 2 countries
para.nconsumer = 5  # Very few consumers

# Enable LLM for FIRM pricing only (to keep API usage minimal)
para.use_llm_firm_pricing = True
para.use_llm_bank_credit = False  # Disabled to reduce API calls
para.use_llm_wage = False  # Disabled to reduce API calls

# Point to our live decider server
para.llm_server_url = 'http://127.0.0.1:9000'
para.llm_timeout_ms = 90000  # 90 seconds timeout (longer for API calls)
para.llm_batch = False

# Output directory
output_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'artifacts',
    'live_llm_simulation'
)
para.folder = os.path.abspath(output_dir)
para.name = 'live_llm_test'

# Data collection
para.timeCollectingStart = 0
para.LtimeCollecting = list(range(para.ncycle))
para.printAgent = 'no'

print("Configuration:")
print("  Cycles: %d (very short to minimize API calls)" % para.ncycle)
print("  Countries: %d" % para.ncountry)
print("  Consumers per country: %d" % para.nconsumer)
print("  LLM Firm Pricing: %s" % para.use_llm_firm_pricing)
print("  LLM Bank Credit: %s" % para.use_llm_bank_credit)
print("  LLM Wage: %s" % para.use_llm_wage)
print("  Decider Server: %s" % para.llm_server_url)
print()
print("-" * 80)
print()

try:
    result = run_simulation(para, progress=True)

    print()
    print("-" * 80)
    print()
    print("="*80)
    print("SIMULATION COMPLETED SUCCESSFULLY!")
    print("="*80)
    print()

    # Display LLM usage statistics
    llm_counters = result.get('llm_counters', {})
    run_counters = llm_counters.get(42, {})

    print("LLM Usage Statistics:")
    for block in ['firm', 'bank', 'wage']:
        counters = run_counters.get(block, {})
        calls = counters.get('calls', 0)
        fallbacks = counters.get('fallbacks', 0)
        timeouts = counters.get('timeouts', 0)

        enabled = {
            'firm': para.use_llm_firm_pricing,
            'bank': para.use_llm_bank_credit,
            'wage': para.use_llm_wage
        }[block]

        status = "ENABLED" if enabled else "DISABLED"
        print("  %s (%s): %d calls, %d fallbacks, %d timeouts" % (
            block.upper().ljust(5), status.ljust(8), calls, fallbacks, timeouts
        ))

    print()
    print("Output directory: %s" % para.folder)
    print()

    if run_counters.get('firm', {}).get('calls', 0) > 0:
        print("="*80)
        print("SUCCESS! The simulation made actual LLM calls!")
        print("The realistic role-playing prompts worked in production!")
        print("="*80)
    else:
        print("WARNING: No LLM calls were made (check server connection)")

    sys.exit(0)

except Exception as e:
    print()
    print("="*80)
    print("SIMULATION FAILED!")
    print("="*80)
    print("Error: %s" % str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
