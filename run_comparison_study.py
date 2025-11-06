#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparative study: Deterministic vs Full LLM Decision-Making

Runs two 50-cycle simulations:
1. Deterministic baseline (original Caiani et al. 2016)
2. Full LLM (firm pricing, bank credit, wage decisions all LLM-driven)

Then compares economic outcomes.
"""

from __future__ import print_function
import sys
import os
import json
import time

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code'))

from parameter import Parameter
from timing import run_simulation


def create_base_parameters():
    """Create base parameter configuration for both simulations."""
    para = Parameter()

    # 50 cycle simulation
    para.ncycle = 50
    para.Lrun = [42]
    para.weSeedRun = 'yes'

    # Reasonable scale
    para.ncountry = 2
    para.nconsumer = 20  # More realistic

    # Server configuration
    para.llm_server_url = 'http://127.0.0.1:9000'
    para.llm_timeout_ms = 90000
    para.llm_batch = False

    # Data collection
    para.timeCollectingStart = 0
    para.LtimeCollecting = list(range(para.ncycle))
    para.printAgent = 'no'

    return para


def run_deterministic_baseline():
    """Run 50-cycle simulation with NO LLM (pure deterministic)."""
    print("="*80)
    print("SCENARIO 1: DETERMINISTIC BASELINE (Pure Caiani et al. 2016)")
    print("="*80)
    print()

    para = create_base_parameters()

    # DISABLE all LLM
    para.use_llm_firm_pricing = False
    para.use_llm_bank_credit = False
    para.use_llm_wage = False

    # Output directory
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'artifacts',
        'comparison_50cycles',
        'deterministic'
    )
    para.folder = os.path.abspath(output_dir)
    para.name = 'deterministic_baseline'

    print("Configuration:")
    print("  Cycles: %d" % para.ncycle)
    print("  Countries: %d" % para.ncountry)
    print("  Consumers per country: %d" % para.nconsumer)
    print("  LLM Firm Pricing: %s" % para.use_llm_firm_pricing)
    print("  LLM Bank Credit: %s" % para.use_llm_bank_credit)
    print("  LLM Wage: %s" % para.use_llm_wage)
    print()
    print("-" * 80)

    start_time = time.time()
    result = run_simulation(para, progress=True)
    elapsed = time.time() - start_time

    print()
    print("-" * 80)
    print()
    print("DETERMINISTIC BASELINE COMPLETED")
    print("Time elapsed: %.1f seconds" % elapsed)
    print()

    # Display counters
    llm_counters = result.get('llm_counters', {})
    run_counters = llm_counters.get(42, {})

    print("LLM Usage:")
    for block in ['firm', 'bank', 'wage']:
        counters = run_counters.get(block, {})
        calls = counters.get('calls', 0)
        print("  %s: %d calls (expected 0)" % (block.upper(), calls))

    # Get core metrics
    core_metrics = result.get('core_metrics', {})

    return {
        'scenario': 'deterministic',
        'elapsed_seconds': elapsed,
        'counters': run_counters,
        'core_metrics': core_metrics,
        'output_dir': para.folder
    }


def run_full_llm():
    """Run 50-cycle simulation with FULL LLM (firm, bank, wage all enabled)."""
    print()
    print("="*80)
    print("SCENARIO 2: FULL LLM DECISION-MAKING (All agents use LLM)")
    print("="*80)
    print()

    para = create_base_parameters()

    # ENABLE all LLM
    para.use_llm_firm_pricing = True
    para.use_llm_bank_credit = True
    para.use_llm_wage = True

    # Output directory
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'artifacts',
        'comparison_50cycles',
        'full_llm'
    )
    para.folder = os.path.abspath(output_dir)
    para.name = 'full_llm'

    print("Configuration:")
    print("  Cycles: %d" % para.ncycle)
    print("  Countries: %d" % para.ncountry)
    print("  Consumers per country: %d" % para.nconsumer)
    print("  LLM Firm Pricing: %s" % para.use_llm_firm_pricing)
    print("  LLM Bank Credit: %s" % para.use_llm_bank_credit)
    print("  LLM Wage: %s" % para.use_llm_wage)
    print()
    print("-" * 80)

    start_time = time.time()
    result = run_simulation(para, progress=True)
    elapsed = time.time() - start_time

    print()
    print("-" * 80)
    print()
    print("FULL LLM SIMULATION COMPLETED")
    print("Time elapsed: %.1f seconds" % elapsed)
    print()

    # Display counters
    llm_counters = result.get('llm_counters', {})
    run_counters = llm_counters.get(42, {})

    print("LLM Usage:")
    for block in ['firm', 'bank', 'wage']:
        counters = run_counters.get(block, {})
        calls = counters.get('calls', 0)
        fallbacks = counters.get('fallbacks', 0)
        timeouts = counters.get('timeouts', 0)
        print("  %s: %d calls, %d fallbacks, %d timeouts" % (
            block.upper(), calls, fallbacks, timeouts
        ))

    # Get core metrics
    core_metrics = result.get('core_metrics', {})

    return {
        'scenario': 'full_llm',
        'elapsed_seconds': elapsed,
        'counters': run_counters,
        'core_metrics': core_metrics,
        'output_dir': para.folder
    }


def compare_results(deterministic, full_llm):
    """Compare results from both simulations."""
    print()
    print("="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)
    print()

    # Execution time comparison
    print("Execution Time:")
    print("  Deterministic: %.1f seconds" % deterministic['elapsed_seconds'])
    print("  Full LLM:      %.1f seconds" % full_llm['elapsed_seconds'])
    overhead = full_llm['elapsed_seconds'] - deterministic['elapsed_seconds']
    print("  LLM Overhead:  %.1f seconds (%.1f%%)" % (
        overhead,
        (overhead / deterministic['elapsed_seconds'] * 100) if deterministic['elapsed_seconds'] > 0 else 0
    ))
    print()

    # LLM usage
    print("LLM API Calls:")
    for block in ['firm', 'bank', 'wage']:
        det_calls = deterministic['counters'].get(block, {}).get('calls', 0)
        llm_calls = full_llm['counters'].get(block, {}).get('calls', 0)
        llm_fallbacks = full_llm['counters'].get(block, {}).get('fallbacks', 0)
        success_rate = ((llm_calls - llm_fallbacks) / float(llm_calls) * 100) if llm_calls > 0 else 0
        print("  %s: %d → %d calls (%.1f%% success)" % (
            block.upper(), det_calls, llm_calls, success_rate
        ))
    print()

    # Economic outcomes comparison
    print("Economic Outcomes:")
    print()

    det_metrics = deterministic['core_metrics']
    llm_metrics = full_llm['core_metrics']

    # Function to safely get and compare metrics
    def compare_metric(name, det_metrics, llm_metrics):
        det_val = det_metrics.get(name)
        llm_val = llm_metrics.get(name)

        if det_val is None or llm_val is None:
            return None

        try:
            det_val = float(det_val)
            llm_val = float(llm_val)
            diff = llm_val - det_val
            pct = (diff / det_val * 100) if det_val != 0 else 0
            return (det_val, llm_val, diff, pct)
        except (TypeError, ValueError):
            return None

    # Compare key metrics (if they exist)
    metrics_to_compare = [
        ('avg_unemployment', 'Average Unemployment'),
        ('avg_gdp', 'Average GDP'),
        ('avg_inflation', 'Average Inflation'),
        ('avg_wage', 'Average Wage'),
        ('final_unemployment', 'Final Unemployment'),
        ('final_gdp', 'Final GDP'),
    ]

    for metric_key, metric_name in metrics_to_compare:
        result = compare_metric(metric_key, det_metrics, llm_metrics)
        if result:
            det_val, llm_val, diff, pct = result
            print("  %s:" % metric_name)
            print("    Deterministic: %.4f" % det_val)
            print("    Full LLM:      %.4f" % llm_val)
            print("    Difference:    %.4f (%+.2f%%)" % (diff, pct))
            print()

    # If no specific metrics, show all available
    if not any(compare_metric(m[0], det_metrics, llm_metrics) for m in metrics_to_compare):
        print("  Available metrics:")
        all_keys = set(det_metrics.keys()) | set(llm_metrics.keys())
        for key in sorted(all_keys):
            det_val = det_metrics.get(key, 'N/A')
            llm_val = llm_metrics.get(key, 'N/A')
            print("    %s: %s (det) vs %s (llm)" % (key, det_val, llm_val))

    print()
    print("Output Directories:")
    print("  Deterministic: %s" % deterministic['output_dir'])
    print("  Full LLM:      %s" % full_llm['output_dir'])
    print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    total_llm_calls = sum(
        full_llm['counters'].get(b, {}).get('calls', 0)
        for b in ['firm', 'bank', 'wage']
    )
    total_fallbacks = sum(
        full_llm['counters'].get(b, {}).get('fallbacks', 0)
        for b in ['firm', 'bank', 'wage']
    )
    success_rate = ((total_llm_calls - total_fallbacks) / float(total_llm_calls) * 100) if total_llm_calls > 0 else 0

    print()
    print("Full LLM simulation made %d API calls with %.1f%% success rate" % (
        total_llm_calls, success_rate
    ))
    print("LLM overhead: %.1f seconds for 50 cycles" % overhead)
    print()
    print("Both simulations completed successfully!")
    print("Review output CSV files for detailed time-series data.")
    print()


if __name__ == "__main__":
    print()
    print("="*80)
    print("COMPARATIVE STUDY: DETERMINISTIC vs FULL LLM")
    print("50 Cycles - All Decision Types")
    print("="*80)
    print()
    print("This will run two complete simulations:")
    print("  1. Deterministic baseline (no LLM)")
    print("  2. Full LLM (firm, bank, wage all use LLM)")
    print()
    print("Expected duration: ~5-10 minutes total")
    print()

    try:
        # Run deterministic baseline first
        det_result = run_deterministic_baseline()

        # Small pause between runs
        print()
        print("[Waiting 10 seconds before LLM run to avoid rate limits...]")
        print()
        time.sleep(10)

        # Run full LLM simulation
        llm_result = run_full_llm()

        # Compare results
        compare_results(det_result, llm_result)

        print()
        print("="*80)
        print("STUDY COMPLETED SUCCESSFULLY!")
        print("="*80)
        print()

        sys.exit(0)

    except KeyboardInterrupt:
        print()
        print("Study interrupted by user")
        sys.exit(1)

    except Exception as e:
        print()
        print("ERROR: Study failed")
        print(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
