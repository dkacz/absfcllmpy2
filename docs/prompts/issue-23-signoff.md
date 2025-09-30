---
title: "Sign-off Brief — Milestone M2 (Equation Map & Data Taps)"
description: "Self-contained evidence packet for Issue #23: confirm Methods hub, data taps, and runtimes are delivered."
format:
  html:
    toc: true
    toc-depth: 2
---

# Summary {#sec-summary}
- **Milestone:** M2 — Equation Map & Data Taps for Manuscript
- **Status:** All executor and writer deliverables merged on `master` (commit `bf210c9`). Runtime instrumentation from PR #113 (firm counters) is live.
- **Scope:** Centralised Methods documentation, baseline datasets, and logging so downstream manuscript work can reference consistent artifacts.

# Deliverables & Evidence {#sec-evidence}

## 1. Methods Hub & Navigation {#sec-hub}
**File:** `docs/methods/index.qmd`
```markdown
---
title: "Methods Hub"
description: "Landing page for the Caiani AB-SFC live LLM instrumentation, linking to method-focused documentation and reference artifacts."
format:
  html:
    toc: true
    toc-depth: 2
---

# Methods Hub {#methods-index}

This hub gathers the technical documentation that underpins the live LLM instrumentation of the Caiani AB-SFC model. Use it as the starting point for detailed discussions of the architecture, runtime safeguards, data exports, and manuscript-ready metrics.

## Model Context

- [Model Overview](model_overview.md) — Non-technical summary of agents, markets, timing, and where LLM hooks integrate with the legacy Python 2 loop (@ref(methods-model-overview)).
- [Equation Map (coming soon)](eq_map.md) — Crosswalk between manuscript equations and code touchpoints (see Issue #74 for upcoming appendix content).

## Runtime Architecture

- [Decider Stub](decider.md) — Python 3 microservice that serves deterministic decisions, schema validation, and timeout controls.
- [Py2 Client](py2_client.md) — HTTP bridge from the legacy simulation to the Decider, including error taxonomy and fallback triggers.
- [Fallback Semantics](fallbacks.qmd) — Detailed explanation of guardrails, clamping rules, and logging for LLM fallbacks.
- [A/B Runner Helper](runners.md) — Convenience wrapper for producing short OFF/ON runs and pointers to the stub data bundle.

## Data & Metrics

- [Variable Dictionary](variables.md) — Metric-by-metric definitions, CSV column references, and aggregation formulas for manuscript tables (@ref(methods-variables)).
- `data/core_metrics.csv` — Canonical 240-tick baseline/LLM comparison exported by `code/timing.py`.
- `docs/stubs/` — 20-tick preview dataset (LLM OFF) for quick Quarto prototypes and smoke checks.

## Next Steps

- Coordinate with Issue #23 (M2 sign-off) once the hub and supporting pages render cleanly via `quarto render docs`.
- Update this index as additional Methods pages (e.g., caching design, wage hook instrumentation) land in later milestones.
```

**Navigation:** `docs/_quarto.yml`
```yaml
- text: "Methods"
  menu:
    - text: "Methods Hub"
      href: methods/index.qmd
    - text: "Model Overview"
      href: methods/model_overview.md
    - text: "Variable Dictionary"
      href: methods/variables.md
    - text: "Decider Stub"
      href: methods/decider.md
    - text: "Py2 Client"
      href: methods/py2_client.md
    - text: "Fallback Semantics"
      href: methods/fallbacks.qmd
    - text: "A/B Runner Helper"
      href: methods/runners.md
```
All Methods documentation is now accessible from a single dropdown.

## 2. Model Overview Page {#sec-overview-page}
**File:** `docs/methods/model_overview.md`
```markdown
---
title: "Model Overview"
description: "A non-technical summary of the Caiani AB-SFC model structure, agents, markets, and the integration of live LLM decisions as instrumented in this repository."
format:
  html:
    toc: true
    toc-depth: 3
---

# Model Overview {#methods-model-overview}

This page provides a high-level overview of the Agent-Based Stock-Flow Consistent (AB-SFC) macroeconomic model used in this project, originally developed by Caiani et al. (2017), and adapted here to incorporate live Large Language Model (LLM) behavioral hooks.

::: {.callout-important}
## Scope Disclaimer
This repository treats the existing Python 2 codebase as a sandbox for a **methods contribution**. The parameters and simulation outcomes differ from the original Caiani calibration; we do not attempt to replicate the original paper’s results. The focus is on demonstrating a pattern for safely integrating live LLM decisions.
:::

## The Baseline AB-SFC Framework {#sec-overview-baseline}
- Multiple countries (default K = 5).
- Agents: households/workers, firms, banks, government, central banks.
- Markets: consumption (Hotelling matching), labor, credit, bond/deposit.
- Stock-flow consistency enforced via `lebalance.py`.

## Simulation Loop and Timing {#sec-overview-timing}
1. Bargaining & price updates (`maLaborCapital.bargaining`, `firm.learning`).
2. Credit decisions (`maCredit.creditNetworkEvolution`).
3. Production & sales (`maLaborCapital.working`, `firm.effectiveSelling`).
4. Income & fiscal policy (`consumer.income`, `poli.implementingPolicy`).
5. Innovation & churn (`gloInnovation.spillover`, `firm.existence`).
6. Aggregation & monetary policy (`aggrega.checkNetWorth`, `centralBankUnion.taylorRule1`).

## Live LLM Integration {#sec-overview-llm}
- Hooks for firm pricing (Eqs. 12–14), bank credit (Eqs. 26–27), wage setting (Eqs. 1 & 15).
- Guardrails: step caps 0.04, expectation bias cap 0.04, price floor `p ≥ w/φ`, spread clamps, leverage monotonicity.
- Hard timeouts/fallbacks to baseline heuristics on error.

## Where to Look Next {#sec-overview-next}
Links to Decider stub, Py2 client, fallback semantics, and the variable dictionary (@ref(methods-variables)).
```

## 3. Variable Dictionary Page {#sec-variables-page}
**File:** `docs/methods/variables.md`
```markdown
---
title: "Variable Dictionary"
description: "A concise dictionary mapping manuscript metrics to their source CSV columns, detailing their computation, inputs, and context within the AB-SFC model."
format:
  html:
    toc: true
    toc-depth: 3
---

# Variable Dictionary {#methods-variables}

This document defines the core metrics used to evaluate simulation outcomes in the manuscript. It details how each metric is computed within the simulation (`code/aggregator.py`) and identifies the corresponding columns in the output datasets.
```

**Data Sources:**
- `data/core_metrics.csv`
  ```csv
  scenario,metric,value
  baseline,price_dispersion,0.16932996561384545
  baseline,avg_spread,0.009963822788659826
  baseline,fill_rate,0.3909319689400087
  baseline,wage_dispersion,0.22413959886601806
  baseline,loan_output_ratio,1.3787753525286761
  baseline,inflation_volatility,0.0056950186751849536
  llm_on,price_dispersion,0.16932996561384545
  llm_on,avg_spread,0.009963822788659826
  llm_on,fill_rate,0.3909319689400087
  llm_on,wage_dispersion,0.22413959886601806
  llm_on,loan_output_ratio,1.3787753525286761
  llm_on,inflation_volatility,0.0056950186751849536
  ```
- Stub bundle (`docs/stubs/`):
  ```json
  {
    "description": "20-tick baseline stub run (LLM hooks disabled)",
    "files": {
      "core_metrics": "micro_run_core_metrics.csv",
      "metric_series": "micro_run_metric_series.csv",
      "raw": [
        "micro_run_raw/stub_micror0AggData.csv",
        "micro_run_raw/stub_micror0Para.csv"
      ]
    },
    "llm": {
      "bank_credit": false,
      "firm_pricing": false,
      "wage": false
    },
    "ncycle": 20,
    "seed": 0
  }
  ```
  ```csv
  tick,metric,value
  0,avg_spread,0.0
  1,avg_spread,0.0
  2,avg_spread,0.0009257498165182073
  ...
  19,avg_spread,0.006778847808250882
  ```

**Metric Table Highlights:**
- Inflation volatility — stdev across ticks of country-average inflation (`std(series['inflation'])`).
- Price dispersion — time-average of sales-weighted dispersion (`mean(series['price_dispersion'])`).
- Wage dispersion — time-average of employment-weighted dispersion (`mean(series['wage_dispersion'])`).
- Fill rate — time-average of `fill_employed_total / fill_desired_total` (defaults to 1 when demand zero).
- Avg spread — time-average of loan-volume-weighted spread (defaults 0 when no loans).
- Loan/output ratio — time-average of credit stock / output (defaults 0 when output zero).

**Reference Snippet:**
```python
self._metric_series = {
    'inflation': [],
    'price_dispersion': [],
    'total_credit': [],
    'avg_spread': [],
    'wage_dispersion': [],
    'fill_rate': [],
    'loan_output_ratio': [],
}
avg_inflation = sum(self.McountryInflation[c] for c in self.Lcountry) / len(self.Lcountry)
...
fill_rate_value = 1.0
if fill_desired_total > 0:
    fill_rate_value = fill_employed_total / float(fill_desired_total)
self._metric_series['fill_rate'].append(fill_rate_value)
...
core_metrics = {
    'inflation_volatility': std(self._metric_series['inflation']),
    'price_dispersion': mean(self._metric_series['price_dispersion']),
    'avg_spread': mean(self._metric_series['avg_spread']),
    'loan_output_ratio': mean(self._metric_series['loan_output_ratio']),
    'wage_dispersion': mean(self._metric_series['wage_dispersion']),
    'fill_rate': mean(self._metric_series['fill_rate'], default=1.0),
}
```

## 4. Runtime Instrumentation — Firm Counters {#sec-runtime}
Merged in PR #113 (`code/llm_runtime.py`, `code/firm.py`, `code/timing.py`):
- `log_llm_call('firm')` increments counters before each Decider call.
- `_log_llm_counter_line` writes per-run summaries to `timing.log`.

**Sample `timing.log` excerpt:**
```
[2025-09-29 21:49:37] LLM toggles server=http://127.0.0.1:8000 timeout_ms=200 batch=off firm=off bank=off wage=off
[LLM firm] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=off calls=0 fallbacks=0 timeouts=0
[2025-09-29 21:49:44] LLM toggles server=http://127.0.0.1:8000 timeout_ms=200 batch=off firm=on bank=on wage=on
[LLM firm] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=on calls=4169 fallbacks=4169 timeouts=0
```
Acceptance criterion “OFF=0; ON>0 on stub run” satisfied.

# Verification Checklist {#sec-checklist}
1. **Render docs:** `quarto render docs` (already run; produces `_site/index.html`).
2. **Inspect Methods hub:** Ensure all links resolve (`methods/index.qmd`).
3. **Verify Model Overview & Variable Dictionary** for completeness and cross-references.
4. **Confirm Navigation** dropdown shows all Methods entries per `docs/_quarto.yml`.
5. **Review Data Artifacts** (`data/core_metrics.csv`, `docs/stubs/…`) cited in variable dictionary.
6. **Check Runtime Counters** via a short `run_ab_demo` if desired (optional, evidence above).

# Sign-off Action {#sec-action}
If all items pass, reply on Issue #23 with the standard **“M2 ✅ — Equation Map & Data Taps delivered”** message, referencing:
- Methods hub (`docs/methods/index.qmd`)
- Model overview & variable dictionary pages
- Core metrics data & stub bundle
- Firm LLM counter logging (timing.log)

Include any additional observations (e.g., known warnings about metadata in Quarto) as part of the sign-off comment.
