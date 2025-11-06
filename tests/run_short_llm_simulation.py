#!/usr/bin/env python
"""Run a very short ABSFC simulation with actual LLM calls.

This demonstrates the end-to-end integration of the realistic role-playing
prompts in the actual simulation context.
"""

import sys
import os
import time
import subprocess
import signal

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code'))

from parameter import Parameter
from timing import run_simulation


def start_decider_server():
    """Start the decider server in live mode (background process)."""
    print("\n" + "="*80)
    print("STARTING DECIDER SERVER (Live Mode)")
    print("="*80)

    server_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'tools', 'decider', 'server.py'
    )

    # Start server in background with our tested model
    process = subprocess.Popen(
        [
            'python', server_script,
            '--mode=live',
            '--port=8000',
            '--openrouter-model-primary=google/gemini-2.5-flash-lite',
            '--skip-openrouter-credit-check',
            '--log-level=INFO'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )

    print(f"✓ Server started (PID: {process.pid})")
    print("  Waiting 3 seconds for server to initialize...")
    time.sleep(3)

    # Check if server is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print("✗ Server failed to start!")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return None

    print("✓ Server should be ready at http://127.0.0.1:8000")
    return process


def stop_decider_server(process):
    """Stop the decider server."""
    if process:
        print("\n" + "="*80)
        print("STOPPING DECIDER SERVER")
        print("="*80)

        process.terminate()
        try:
            process.wait(timeout=5)
            print("✓ Server stopped cleanly")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            print("✓ Server killed (force)")


def run_llm_simulation():
    """Run a very short simulation with LLM enabled."""
    print("\n" + "="*80)
    print("RUNNING SHORT SIMULATION WITH ACTUAL LLM CALLS")
    print("="*80)
    print("\nConfiguration:")
    print("  - Cycles: 3 (very short to minimize API calls)")
    print("  - Countries: 2")
    print("  - LLM enabled for: FIRM pricing only (to keep API usage minimal)")
    print("  - Decider server: http://127.0.0.1:8000 (live mode)")
    print()

    # Create minimal parameter configuration
    para = Parameter()

    # Very short run
    para.ncycle = 3
    para.Lrun = [42]  # Single run with seed 42
    para.weSeedRun = 'yes'

    # Reduce scale to minimize API calls
    para.ncountry = 2  # Just 2 countries
    para.nconsumer = 10  # Fewer consumers per country

    # Enable LLM only for firm pricing (to keep API usage minimal)
    para.use_llm_firm_pricing = True
    para.use_llm_bank_credit = False  # Disable to reduce API calls
    para.use_llm_wage = False  # Disable to reduce API calls

    # Decider server configuration
    para.llm_server_url = 'http://127.0.0.1:8000'
    para.llm_timeout_ms = 30000  # 30 seconds timeout
    para.llm_batch = False  # Disable batching for now

    # Output directory
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'artifacts',
        'llm_test_simulation'
    )
    para.folder = os.path.abspath(output_dir)
    para.name = 'llm_test'

    # Data collection
    para.timeCollectingStart = 0
    para.LtimeCollecting = list(range(para.ncycle))
    para.printAgent = 'no'  # Don't print individual agent files

    print("Starting simulation...\n")
    print("-" * 80)

    try:
        result = run_simulation(para, progress=True)

        print("-" * 80)
        print("\n" + "="*80)
        print("SIMULATION COMPLETED SUCCESSFULLY!")
        print("="*80)

        # Display LLM usage statistics
        llm_counters = result.get('llm_counters', {})
        run_counters = llm_counters.get(42, {})

        print("\nLLM Usage Statistics:")
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
            print(f"  {block.upper():5s} ({status:8s}): {calls:3d} calls, {fallbacks:3d} fallbacks, {timeouts:3d} timeouts")

        # Display core metrics
        core_metrics = result.get('core_metrics', {})
        if core_metrics:
            print("\nCore Metrics:")
            for metric, value in sorted(core_metrics.items())[:10]:  # Show first 10
                print(f"  {metric}: {value}")

        print(f"\nOutput directory: {para.folder}")

        return True

    except Exception as e:
        print("-" * 80)
        print("\n✗ SIMULATION FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SHORT ABSFC SIMULATION WITH ACTUAL LLM INTEGRATION")
    print("="*80)
    print("\nThis will:")
    print("  1. Start the decider server in live mode (using realistic prompts)")
    print("  2. Run a 3-cycle simulation with firm LLM pricing enabled")
    print("  3. Make actual OpenRouter API calls with realistic role-playing prompts")
    print("  4. Stop the server and display results")
    print()

    server_process = None

    try:
        # Start server
        server_process = start_decider_server()

        if server_process is None:
            print("\n✗ Failed to start server, aborting")
            sys.exit(1)

        # Run simulation
        success = run_llm_simulation()

        # Stop server
        stop_decider_server(server_process)

        if success:
            print("\n✓✓✓ ALL DONE! The realistic LLM prompts work in production! ✓✓✓\n")
            sys.exit(0)
        else:
            print("\n✗ Simulation failed, see errors above\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if server_process:
            stop_decider_server(server_process)
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        if server_process:
            stop_decider_server(server_process)
        sys.exit(1)
