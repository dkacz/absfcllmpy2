#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run only the full LLM simulation (50 cycles)."""

from __future__ import print_function
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code'))

from parameter import Parameter
from timing import run_simulation

print("="*80)
print("RUNNING FULL LLM SIMULATION (50 CYCLES)")
print("="*80)
print()

# Create configuration
para = Parameter()
para.ncycle = 50
para.Lrun = [42]
para.weSeedRun = 'yes'

# Standard scale
para.ncountry = 2
para.nconsumer = 20

# Enable ALL LLM decision-making
para.use_llm_firm_pricing = True
para.use_llm_bank_credit = True
para.use_llm_wage = True

# LLM server configuration
para.llm_server_url = 'http://127.0.0.1:9000'
para.llm_timeout_ms = 90000  # 90 seconds
para.llm_batch = False

# Output directory
output_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'artifacts',
    'comparison_50cycles',
    'full_llm'
)
para.folder = os.path.abspath(output_dir)
para.name = 'full_llm'

# Data collection
para.timeCollectingStart = 0
para.LtimeCollecting = list(range(para.ncycle))
para.printAgent = 'no'

print("Configuration:")
print("  Cycles: %d" % para.ncycle)
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
    print("FULL LLM SIMULATION COMPLETED!")
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
        success_rate = 0.0
        if calls > 0:
            success_rate = ((calls - fallbacks) / float(calls)) * 100.0

        print("  %s: %d calls, %d fallbacks, %d timeouts (%.1f%% success)" % (
            block.upper().ljust(5), calls, fallbacks, timeouts, success_rate
        ))

    print()
    print("Output directory: %s" % para.folder)
    print()

    total_calls = sum(run_counters.get(b, {}).get('calls', 0) for b in ['firm', 'bank', 'wage'])
    total_fallbacks = sum(run_counters.get(b, {}).get('fallbacks', 0) for b in ['firm', 'bank', 'wage'])

    if total_calls > 0 and total_fallbacks < total_calls:
        print("="*80)
        print("SUCCESS! LLM decisions were used in the simulation!")
        print("Total LLM calls: %d" % total_calls)
        print("Successful calls: %d" % (total_calls - total_fallbacks))
        print("Fallbacks: %d" % total_fallbacks)
        print("="*80)
    elif total_calls > 0 and total_fallbacks == total_calls:
        print("="*80)
        print("WARNING: All LLM calls fell back to deterministic baseline")
        print("Total calls: %d (all failed)" % total_calls)
        print("="*80)
    else:
        print("WARNING: No LLM calls were made")

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
