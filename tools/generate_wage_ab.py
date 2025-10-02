#!/usr/bin/env python3
"""Generate wage A/B comparison artifacts (CSV + overlay figure).

This helper orchestrates the Python 2 simulation (via ``run_ab_demo``)
for ``run_id=0`` over 200 ticks, then emits:

* ``data/wage/wage_ab_table.csv`` – raw metrics (wage dispersion, fill rate)
  for baseline vs. LLM ON scenarios.
* ``figs/wage/wage_ab_overlay.png`` – wage dispersion overlay (OFF dashed, ON solid)
  with the final 50 ticks shaded.

Run from the repository root:

    python3 tools/generate_wage_ab.py

"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt


RUN_ID = 0
NCYCLE = 200
SCENARIO_MAP = {"off": "baseline", "on": "llm_on"}
FINAL_SHADE = 50  # number of trailing ticks to shade in overlay
DECIDER_URL = "http://127.0.0.1:8000/healthz"
TABLE_METRICS = ("wage_dispersion", "fill_rate")
OVERLAY_SERIES = "wage_dispersion"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def start_decider_stub() -> subprocess.Popen:
    """Launch the Decider stub and wait until the health check passes."""

    root = repo_root()
    print("Starting Decider stub on http://127.0.0.1:8000 ...")
    with open(os.devnull, "wb") as devnull:
        proc = subprocess.Popen(
            ["python3", "tools/decider/server.py", "--stub"],
            cwd=str(root),
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )
    deadline = time.time() + 10.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(DECIDER_URL, timeout=0.5):
                print("Decider stub healthy on http://127.0.0.1:8000")
                return proc
        except (urllib.error.URLError, urllib.error.HTTPError):
            time.sleep(0.2)
    proc.terminate()
    proc.wait()
    raise RuntimeError("Decider stub failed to pass health check")


def stop_decider_stub(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def run_simulation(tmp_json: Path) -> None:
    """Invoke python2 run_ab_demo and persist results to ``tmp_json``."""

    code = """
from code.timing import run_ab_demo
import json
result = run_ab_demo(
    run_id={run_id},
    ncycle={ncycle},
    llm_overrides={{
        'use_llm_firm_pricing': False,
        'use_llm_bank_credit': False,
    }},
)
with open(r"{json_path}", "w") as handle:
    json.dump(result, handle)
""".format(run_id=RUN_ID, ncycle=NCYCLE, json_path=tmp_json.as_posix())

    root = repo_root()
    tmp_json.parent.mkdir(parents=True, exist_ok=True)
    print(
        "Running run_ab_demo via python2 (run_id={}, ncycle={})...".format(
            RUN_ID, NCYCLE
        )
    )
    print("  • This can take several minutes; monitor timing.log for toggle snapshots.")
    with open(os.devnull, "wb") as devnull:
        subprocess.check_call(
            ["python2", "-c", code],
            cwd=str(root),
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )


def load_results(tmp_json: Path) -> Dict[str, dict]:
    with tmp_json.open("r") as handle:
        return json.load(handle)


def write_table(results: Dict[str, dict], output_path: Path) -> None:
    rows = []
    for label, payload in results.items():
        scenario = SCENARIO_MAP.get(label)
        if not scenario:
            continue
        metrics = payload.get("core_metrics", {}) or {}
        for metric_name in TABLE_METRICS:
            if metric_name in metrics:
                rows.append((scenario, metric_name, metrics[metric_name]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scenario", "metric", "value"])
        writer.writerows(rows)


def plot_overlay(results: Dict[str, dict], output_path: Path) -> None:
    baseline = results.get("off", {})
    llm_on = results.get("on", {})
    off_series = baseline.get("metric_series", {}).get(OVERLAY_SERIES, [])
    on_series = llm_on.get("metric_series", {}).get(OVERLAY_SERIES, [])

    if not off_series or not on_series:
        raise RuntimeError("Missing {} series in simulation results".format(OVERLAY_SERIES))

    ticks = list(range(len(off_series)))
    if len(on_series) != len(ticks):
        raise RuntimeError("Scenario series lengths do not match")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ticks, off_series, linestyle="--", linewidth=1.6, label="Baseline (OFF)")
    ax.plot(ticks, on_series, linestyle="-", linewidth=1.6, label="LLM ON")

    shade_start = max(0, len(ticks) - FINAL_SHADE)
    ax.axvspan(shade_start, len(ticks) - 1, color="tab:gray", alpha=0.15, label="Final 50 ticks")

    ax.set_title("Wage dispersion – A/B overlay (run 0, 200 ticks)")
    ax.set_xlabel("Tick")
    ax.set_ylabel("Wage dispersion")
    ax.legend(loc="upper left")
    ax.grid(True, linewidth=0.4, alpha=0.4)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=144)
    plt.close(fig)


def main() -> None:
    root = repo_root()
    tmp_json = root / "artifacts" / "wage_ab_result.json"

    decider_proc = start_decider_stub()
    try:
        run_simulation(tmp_json)
        results = load_results(tmp_json)
    finally:
        stop_decider_stub(decider_proc)

    table_path = root / "data" / "wage" / "wage_ab_table.csv"
    figure_path = root / "figs" / "wage" / "wage_ab_overlay.png"

    write_table(results, table_path)
    plot_overlay(results, figure_path)

    tmp_json.unlink(missing_ok=True)
    relative_table = table_path.relative_to(root)
    relative_figure = figure_path.relative_to(root)
    print("Generated {} and {}".format(relative_table, relative_figure))


if __name__ == "__main__":
    main()
