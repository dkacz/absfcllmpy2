---
title: "Writer Brief — Issue #38 (M4 Bank LLM Methods)"
description: "Context packet for the 300–500 word Methods snippet covering the bank credit & spreads hook."
format:
  html:
    toc: true
    toc-depth: 2
---

# Assignment
- **Milestone:** M4 — Bank Credit & Spreads (eq. 26–27)
- **Issue:** #38 (role: writer)
- **Deliverable:** 300–500 word prose paragraph for the Manuscript Methods chapter detailing how the live LLM bridge augments the bank credit decision.
- **Audience:** readers already familiar with the Caiani AB‑SFC baseline equations; tone is technical and methods-first.
- **Placement:** Methods chapter in `docs/main.qmd` (bank subsection) with cross-references to manuscript artifacts (`@tbl-bank-ab`, `@fig-bank-ab`).
- **Scope:** Focus on *instrumentation* (payload, guards, fallbacks, counters) rather than A/B results narrative.

# Story beats to cover
1. **Baseline recap** — remind the reader what equations 26–27 do in the legacy model (probability/limit/spread derived from leverage & loan supply).
2. **LLM hook flow** — Python 2 simulation (`code/bank.py`) builds feature payload → invokes Decider service via `llm_runtime` → receives `(decision, error)` tuple.
3. **Feature pack & guards** — enumerate the payload fields (capital, reserves, borrower block) and the guard configuration (min/max spread window, epsilon, credit-limit clamps). Reference `get_bank_guard_config()` and `_apply_llm_decision`.
4. **Fallback ladder & counters** — describe `log_llm_call('bank')`, fallback reasons, and the timing log snapshot that now records `[LLM bank] … calls/fallbacks/timeouts`.
5. **Manuscript artifacts** — note that `docs/bank_ab.qmd` cites `data/bank/bank_ab_table.csv` and `figs/bank/bank_ab_overlay.png`; explain why OFF/ON values currently coincide (stub returns deterministic fallbacks) and how the infrastructure supports future live prompts.
6. **Forward link** — mention the architect’s live-mode plan (OpenRouter adapter, JSON schema prompts) as the next step beyond the stub.

# Key artifacts & excerpts
## Bank guard enforcement (`code/bank.py`)
```python
          payload=self._build_llm_payload(firm_obj,leverage,relPhi,loan_request,loan_supply,baseline)
          log_llm_call('bank')
          decision,error=client.decide_bank(payload)
          if error:
             reason='error'
             detail=None
             if isinstance(error,dict):
                reason=error.get('reason','error')
                detail=error.get('detail')
             log_fallback('bank',reason,detail)
             state['fallback']=True
             state['fallback_reason']=reason
             self._llm_bank_last_decision=state
             return state
...
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
          baseline_guarded=min(max(baseline_spread,min_spread),max_spread)
          if spread+epsilon<baseline_guarded:
             log_fallback('bank','spread_monotonicity','%.1f<%.1f' % (spread,baseline_guarded))
             spread=baseline_guarded
```

## Guard configuration (`code/llm_runtime.py`)
```python
def get_bank_guard_config():
    base_min = 50.0
    base_max = 500.0
    parameter = get_parameter()
    if parameter:
        custom_bounds = getattr(parameter, 'bank_guard_bounds', None)
        bounds = _sanitise_bank_bounds(custom_bounds)
        if bounds is not None:
            base_min, base_max = bounds
    preset = _resolve_guard_preset(parameter, 'bank_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)
    min_bps = base_min if preset != 'tight' else base_min + 50.0
    window = max(0.0, base_max - base_min)
    max_bps = max(min_bps, min_bps + window * factor)
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
        'epsilon': max(0.0, epsilon),
    }
```

## Timing log snapshot (10-tick smoke run)
```
[2025-10-01 10:46:35] LLM toggles server=http://127.0.0.1:8000 timeout_ms=10 batch=off firm=off bank=on wage=off
[LLM firm] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=off calls=0 fallbacks=0 timeouts=0
[LLM bank] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=on calls=2267 fallbacks=91 timeouts=0
```

## Quarto results page (`docs/bank_ab.qmd` excerpt)
```markdown
# Overview
This page documents the bank credit & spreads experiment for Milestone M4. Both runs use `run_id = 0` over a 200-tick horizon. The CSV and overlay below are generated via `python3 tools/generate_bank_ab.py` and report the metrics exported by `code/timing.py`.

Because the Decider stub currently returns deterministic fallbacks, the OFF and ON scenarios remain identical. We publish the artifacts now so prompt work can later drop in differentiated behaviour without restructuring the page.

## Core metrics
The table summarises the average spread, loan-to-output ratio, and credit-growth proxy for baseline (`OFF`) versus LLM-enabled (`ON`) runs. Values follow manuscript formatting (two decimals, comma separators for large magnitudes).

```{python}
#| label: tbl-bank-ab
#| tbl-cap: "Bank A/B metrics (run 0, 200 ticks)."
...
```

![Bank average spread overlay (OFF dashed, ON solid; final 50 ticks shaded)](../figs/bank/bank_ab_overlay.png){#fig-bank-ab}
```

## Blueprint anchor
- `docs/blueprint.md` lists `data/bank_ab_table.csv` and `figs/bank_ab_overlay.png` as the canonical manuscript artifacts for the bank block.

# Additional notes
- The architect’s live-mode spec (OpenRouter adapter, structured prompts) is documented in `docs/prompts/question-architect-llm-live.md`; acknowledge it as upcoming work.
- Mention that current runs use the stub (`tools/decider/server.py --stub`) and enforce a hard 200 ms deadline (`Parameter.llm_timeout_ms`).
- If you cite logs, refer to the timing snapshot above and explain that high fallback counts stem from the stub’s deterministic responses.

# Deliverable checklist for the writer
- 300–500 words, formal research tone.
- Cite manuscript artifacts (`@tbl-bank-ab`, `@fig-bank-ab`).
- Reference the guard and counter plumbing shown above.
- Include one sentence on current OFF/ON parity and future live-mode work.
- Submit prose (Markdown) via the GitHub issue comment thread.
