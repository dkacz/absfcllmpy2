#!/usr/bin/env python3
"""Generate experiment C (coordinated upsilon reduction) demo artifacts.

This helper runs the Python 2 ``run_ab_demo`` with overrides that decrease the
wage adjustment parameter ``upsilon`` across *all* countries to 90% of its
baseline value starting at tick 50 (``run_id=0``, ``ncycle=250``). The OFF leg
remains baseline; the ON leg applies the policy switch simultaneously across the
union. As with the other experiment helpers you can either let this script start
its own Decider stub or reuse one you already launched in a separate terminal.

Outputs:

* ``data/expC_demo/expC_metrics.csv`` – summary metrics (wage dispersion,
  fill rate) for baseline vs. policy-on scenarios.
* ``data/expC_demo/expC_wage_dispersion_series.csv`` – long-form wage dispersion
  series for OFF vs. ON.
* ``data/expC_demo/expC_fill_rate_series.csv`` – long-form vacancy fill rate
  series.
* ``figs/expC_demo/expC_wage_dispersion_overlay.png`` – overlay plot with OFF
  dashed, ON solid, final 50 ticks shaded, and a policy-switch marker at tick 50.

Run from the repository root::

    python3 tools/generate_exp_c_demo.py

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
from typing import Dict, Iterable, List

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt

RUN_ID = 0
NCYCLE = 250
POLICY_T0 = 50
UPSILON_FACTOR = 0.9
METRICS = ("wage_dispersion", "fill_rate")
SCENARIO_MAP = {"off": "baseline", "on": "policy_low"}
FINAL_SHADE = 50
DECIDER_URL = "http://127.0.0.1:8000/healthz"
SERIES_OUTPUTS = {
    "wage_dispersion": "expC_wage_dispersion_series.csv",
    "fill_rate": "expC_fill_rate_series.csv",
}
PLOT_SETTINGS = {
    "metric": "wage_dispersion",
    "ylabel": "Wage dispersion",
    "title": f"Experiment C – wage dispersion overlay (run {RUN_ID}, {NCYCLE} ticks)",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _stub_healthy(timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(DECIDER_URL, timeout=timeout):
            return True
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def start_decider_stub() -> subprocess.Popen | None:
    if _stub_healthy():
        print("Detected existing Decider stub on http://127.0.0.1:8000 – reusing it.")
        return None

    root = repo_root()
    print("Starting Decider stub on http://127.0.0.1:8000 …")
    with open(os.devnull, "wb") as devnull:
        proc = subprocess.Popen(
            ["python3", "tools/decider/server.py", "--stub"],
            cwd=str(root),
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )

    deadline = time.time() + 10.0
    while time.time() < deadline:
        if _stub_healthy():
            print("Decider stub healthy.")
            return proc
        time.sleep(0.2)

    proc.terminate()
    proc.wait()
    raise RuntimeError("Decider stub failed health check")


def stop_decider_stub(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def run_simulation(tmp_json: Path) -> None:
    code = """
from code.timing import run_ab_demo
from code.parameter import Parameter
import json

base_upsilon = Parameter().upsilon
result = run_ab_demo(
    run_id={run_id},
    ncycle={ncycle},
    parameter_overrides={{}},
    llm_overrides={{
        'startingPolicy': {policy_t0},
        'policyKind': 'ModAll',
        'policyVariable': base_upsilon * {upsilon_factor},
    }},
)
with open(r"{json_path}", 'w') as handle:
    json.dump(result, handle)
""".format(
        run_id=RUN_ID,
        ncycle=NCYCLE,
        policy_t0=POLICY_T0,
        upsilon_factor=UPSILON_FACTOR,
        json_path=tmp_json.as_posix(),
    )

    root = repo_root()
    tmp_json.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"Running run_ab_demo via python2 (run_id={RUN_ID}, ncycle={NCYCLE}, t0={POLICY_T0}) …"
    )
    print("  • Monitor timing.log for toggle snapshots and usage lines.")
    with open(os.devnull, "wb") as devnull:
        subprocess.check_call(
            ["python2", "-c", code],
            cwd=str(root),
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )


def load_results(tmp_json: Path) -> Dict:
    with tmp_json.open("r") as handle:
        return json.load(handle)


def write_summary_table(results: Dict, output_path: Path) -> None:
    rows: List[List[object]] = []
    for label, payload in results.items():
        scenario = SCENARIO_MAP.get(label)
        if not scenario:
            continue
        metrics = (payload.get("core_metrics") or {})
        for metric_name in METRICS:
            if metric_name in metrics:
                rows.append([scenario, metric_name, metrics[metric_name]])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scenario", "metric", "value"])
        writer.writerows(rows)


def write_series(results: Dict, output_dir: Path, metric: str, filename: str) -> None:
    rows: List[List[object]] = []
    for label, payload in results.items():
        scenario = SCENARIO_MAP.get(label)
        if not scenario:
            continue
        series: Iterable[float] = (payload.get("metric_series", {}) or {}).get(metric, [])
        for tick, value in enumerate(series):
            rows.append([tick, scenario, value])

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / filename).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["tick", "scenario", "value"])
        writer.writerows(rows)


def plot_overlay(results: Dict, output_path: Path) -> None:
    metric = PLOT_SETTINGS["metric"]
    baseline = results.get("off", {})
    policy_on = results.get("on", {})
    off_series: List[float] = (baseline.get("metric_series", {}) or {}).get(metric, [])
    on_series: List[float] = (policy_on.get("metric_series", {}) or {}).get(metric, [])

    if not off_series or not on_series:
        raise RuntimeError(f"Missing {metric} series in simulation results")
    if len(off_series) != len(on_series):
        raise RuntimeError("Scenario series lengths do not match")

    ticks = list(range(len(off_series)))
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    ax.plot(ticks, off_series, linestyle="--", linewidth=1.6, label="Baseline (OFF)")
    ax.plot(ticks, on_series, linestyle="-", linewidth=1.6, label="Policy ON")

    shade_start = max(0, len(ticks) - FINAL_SHADE)
    ax.axvspan(shade_start, len(ticks) - 1, color="tab:gray", alpha=0.15, label="Final 50 ticks")
    ax.axvline(POLICY_T0, color="tab:red", linestyle=":", linewidth=1.0, label="Policy switch (t=50)")

    ax.set_title(PLOT_SETTINGS["title"])
    ax.set_xlabel("Tick")
    ax.set_ylabel(PLOT_SETTINGS["ylabel"])
    ax.grid(True, linewidth=0.4, alpha=0.4)
    ax.legend(loc="best")
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=144)
    plt.close(fig)


def main() -> None:
    root = repo_root()
    tmp_json = root / "artifacts" / "expC_result.json"

    decider_proc = start_decider_stub()
    try:
        run_simulation(tmp_json)
        results = load_results(tmp_json)
    finally:
        stop_decider_stub(decider_proc)

    data_dir = root / "data" / "expC_demo"
    figs_dir = root / "figs" / "expC_demo"

    write_summary_table(results, data_dir / "expC_metrics.csv")
    for metric, filename in SERIES_OUTPUTS.items():
        write_series(results, data_dir, metric, filename)
    plot_overlay(results, figs_dir / "expC_wage_dispersion_overlay.png")

    tmp_json.unlink(missing_ok=True)
    print("Generated experiment C artifacts under data/expC_demo and figs/expC_demo.")


if __name__ == "__main__":
    main()
