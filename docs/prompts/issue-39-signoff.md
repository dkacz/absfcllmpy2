---
title: "Sign-off Prompt — Issue #39 (M4 Bank)"
description: "Self-contained evidence packet so the signoff agent can verify bank guard enforcement, counters logging, and A/B artifacts for Milestone M4."
format:
  html:
    toc: true
    toc-depth: 2
---

# Scope & Acceptance Checklist {#sec-scope}
- **Milestone:** M4 — Bank credit & spreads (eq. 26–27)
- **Issue:** #39 (role: signoff, priority P0)
- **Objective for signoff agent:** Decide whether to post **M4 ✅** on issue #39. Acceptance hinges on three checks:
  1. **Guard enforcement:** Bank hook clamps credit limits, enforces monotonic spreads, and respects epsilon guardrails.
  2. **Counters logging:** Bank LLM counters (calls / fallbacks / timeouts) append to `timing.log` alongside the firm block.
  3. **Artifacts present:** Bank A/B CSV/PNG (`data/bank/bank_ab_table.csv`, `figs/bank/bank_ab_overlay.png`) exist and are cited on `docs/bank_ab.qmd`.

Everything the signoff agent needs is embedded below. If any criterion fails, reply on the GitHub issue with the blockers instead of approving.

# Evidence — Bank Guard Enforcement {#sec-guards}
Key sections from `code/bank.py` showing how the LLM decision is bounded before being applied:

```python
# code/bank.py — LLM decision application (selected excerpt)
from llm_runtime import bank_enabled, get_client, log_fallback
...
      def _apply_llm_decision(self,decision,baseline,loan_request):
          result=baseline.copy()
          guards=self._bank_guard_config()
          approve=decision.get('approve',True)
          ratio=decision.get('credit_limit_ratio',1.0)
          base_limit=baseline.get('credit_limit',0.0)
          credit_limit=base_limit*ratio
          if credit_limit>base_limit:
             log_fallback('bank','credit_limit_clamped_baseline')
             credit_limit=base_limit
          if credit_limit>loan_request:
             log_fallback('bank','credit_limit_clamped_demand')
             credit_limit=loan_request
          if credit_limit<0.0:
             log_fallback('bank','credit_limit_clamped_negative')
             credit_limit=0.0
          spread=decision.get('spread_bps')
          if spread is None:
             spread=baseline.get('spread_bps',0.0)
          min_spread=guards['min_bps']
          max_spread=guards['max_bps']
          epsilon=guards['epsilon']
          if spread<min_spread:
             log_fallback('bank','spread_clamped_min','%.1f<%.1f' % (spread,min_spread))
             spread=min_spread
          elif spread>max_spread:
             log_fallback('bank','spread_clamped_max','%.1f>%.1f' % (spread,max_spread))
             spread=max_spread
          baseline_spread=baseline.get('spread_bps',min_spread)
          baseline_guarded=baseline_spread
          if baseline_guarded<min_spread:
             baseline_guarded=min_spread
          if baseline_guarded>max_spread:
             baseline_guarded=max_spread
          if spread+epsilon<baseline_guarded:
             log_fallback('bank','spread_monotonicity','%.1f<%.1f' % (spread,baseline_guarded))
             spread=baseline_guarded
          interest=self.rDiscount+spread/10000.0
          probability=baseline.get('probability',0.0)
          if not approve:
             probability=0.0
             credit_limit=0.0
          result.update({
              'approve':bool(approve),
              'probability':self._clamp_probability(probability),
              'credit_limit':credit_limit,
              'interest_rate':interest,
              'spread_bps':spread,
          })
          return result
```

The guard configuration comes from `code/llm_runtime.py`:

```python
# code/llm_runtime.py — bank guard configuration
_BANK_GUARD_EPSILON = {
    'baseline': 1e-6,
    'tight': 0.0,
    'loose': 1e-6,
}
...
def get_bank_guard_config():
    base_min = 50.0
    base_max = 500.0
    parameter = get_parameter()

    if parameter:
        custom_bounds = getattr(parameter, 'bank_guard_bounds', None)
        bounds = _sanitise_bank_bounds(custom_bounds)
        if bounds is not None:
            base_min, base_max = bounds

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'bank_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)

    min_bps = base_min
    if preset == 'tight':
        min_bps = base_min + 50.0

    window = max(0.0, base_max - base_min)
    max_bps = min_bps + window * factor
    if max_bps < min_bps:
        max_bps = min_bps

    epsilon = _BANK_GUARD_EPSILON.get(preset, 1e-6)
    if parameter:
        custom_eps = getattr(parameter, 'bank_guard_epsilon', None)
        try:
            if custom_eps is not None:
                epsilon = max(0.0, float(custom_eps))
        except (TypeError, ValueError):
            pass

    return {
        'min_bps': min_bps,
        'max_bps': max_bps,
        'epsilon': epsilon,
    }
```

**Guard verdict:** Clamping logic exists and calls `log_fallback` when adjustments occur, satisfying the first portion of the signoff checklist.

# Evidence — Counters Logging (Blocker) {#sec-counters}
The current master branch still logs **only firm counters** in `timing.log`. Relevant snippets:

```python
# code/timing.py — counter flush (lines 57–82)
def _log_llm_counter_line(parameter, run_id, counters):
    counters = counters or {}
    calls = int(counters.get('calls', 0))
    fallbacks = int(counters.get('fallbacks', 0))
    timeouts = int(counters.get('timeouts', 0))
    line = (
        '[LLM firm] counters name=%s run=%s llm=%s calls=%d fallbacks=%d timeouts=%d\n'
        % (
            getattr(parameter, 'name', 'n/a'),
            run_id,
            _flag(getattr(parameter, 'use_llm_firm_pricing', False)),
            calls,
            fallbacks,
            timeouts,
        )
    )
    ...
    print line.strip()

for run in para.Lrun:
    ...
    reset_llm_counters()
    ensure_llm_counter('firm')
    ...
    _log_llm_counter_line(para, run, counters_snapshot.get('firm'))
```

`code/llm_runtime.py` exposes a `log_llm_call('bank')` helper, but `code/bank.py` never invokes it — search results are empty:

```text
$ rg "log_llm_call" code/bank.py
<no matches>
```

Because the bank hook neither registers its counter nor writes to the log, **acceptance criterion #2 currently fails**. The signoff agent should flag this unless the missing logging lands before review.

For reference, the one-liner to reproduce after starting the Decider stub is:

```bash
python2 -c "from code.timing import run_ab_demo; run_ab_demo(run_id=0, ncycle=200, llm_overrides={'use_llm_bank_credit': True, 'use_llm_firm_pricing': False, 'use_llm_wage': False}, progress=False)"
```

Running it today appends a single `[LLM firm] counters ...` line; there is no `[LLM bank]` entry.

# Evidence — Manuscript Artifacts (Missing) {#sec-artifacts}
Neither the CSV nor the PNG nor the Quarto page exists on this branch. Output from `find`:

```text
$ find data -maxdepth 2 -type f
data/core_metrics.csv
data/firm/firm_ab_table.csv
data/reference/hsc_core_metrics.json
data/reference/hsc_metric_series.json
data/reference/hsc_series.json
data/reference/hsc_stability_table.csv
data/reference/hsc_summary.csv
data/_examples/sample_metrics.csv
```

```text
$ find figs -maxdepth 2 -type f
figs/firm/firm_ab_overlay.png
figs/reference/hsc_convergence_avg_spread.png
figs/reference/hsc_convergence_credit_growth.png
figs/reference/hsc_convergence_fill_rate.png
figs/reference/hsc_convergence_inflation.png
figs/reference/hsc_convergence_price_dispersion.png
figs/reference/hsc_convergence_wage_dispersion.png
figs/_examples/sample_overlay.png
```

Attempting to open the expected files confirms they are absent:

```text
$ cat data/bank/bank_ab_table.csv
cat: data/bank/bank_ab_table.csv: No such file or directory

$ sed -n '1,40p' docs/bank_ab.qmd
sed: can't read docs/bank_ab.qmd: No such file or directory
```

**Artifact verdict:** Acceptance criterion #3 fails until Issues #36/#37 land and deposit the CSV/PNG + Quarto page.

# Quick Reproduction Checklist {#sec-repro}
1. Start the Decider stub in another terminal: `python3 tools/decider/server.py --stub`.
2. Run the demo helper (command above) to regenerate counters and OFF/ON artifacts under `artifacts/ab_demo/run_000/`.
3. Inspect `timing.log` — expect only `[LLM firm]` counters, highlighting the current gap.
4. Confirm that no `data/bank/...` outputs exist without implementing Issue #36 first.

# Signoff Guidance {#sec-guidance}
- **Guards:** ✅ The clamp logic and monotonic spread enforcement live in `code/bank.py` as required.
- **Counters:** ❌ Bank counters never log; `timing.log` only tracks the firm block. Needs follow-up (Issue #35 or equivalent).
- **Artifacts:** ❌ `data/bank/bank_ab_table.csv`, `figs/bank/bank_ab_overlay.png`, and `docs/bank_ab.qmd` are missing (Issues #36/#37 outstanding).

Unless the missing pieces merge before review, respond on Issue #39 with the blockers instead of approving. Once the executor delivers the counters logging and artifacts, re-run the verification steps and update this prompt accordingly.
