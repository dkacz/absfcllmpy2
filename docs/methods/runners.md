---
title: "A/B Runner Helper"
format:
  html:
    toc: false
---

The minimal runner lives inside `code/timing.py` and returns a dictionary that captures
where each OFF/ON pass wrote its outputs. The helper keeps the seed fixed while toggling
**all LLM hooks** so downstream scripts can inspect the resulting artifacts.

```python
from code.timing import run_ab_demo

result = run_ab_demo(run_id=0)
print(result['off']['artifacts']['csv'])
print(result['on']['counters'])
```

Key defaults:

- Output folders land under `artifacts/ab_demo/run_<seed>/<off|on>/` unless you provide
  `output_root`.
- `mode` selects the default horizon: `"ab"` → 200 ticks, `"scenario"` → 250,
  `"robustness"` → 120. Pass `ncycle` (or set `parameter_overrides['ncycle']`) to override.
- `parameter_overrides` lets you tweak `Parameter` attributes. Example: tighten firm guards by
  setting `firm_guard_preset="tight"` (or `llm_guard_preset` to affect all blocks).
- `llm_overrides` applies only to the ON run so you can exercise a subset of hooks.
- The returned metadata now includes:
  - `artifacts`: lists of CSV/PNG files generated under each run folder.
  - `counters`: a pointer to `timing.log` plus stub fallback/timeout counters (always zero
    today; later issues will populate them from hook instrumentation).

### Examples

**Scenario demo with tight guard preset**

```python
from code.timing import run_ab_demo

tight = {
    'ncycle': 250,  # optional, matches mode='scenario'
    'firm_guard_preset': 'tight',
}

result = run_ab_demo(
    run_id=2,
    mode='scenario',
    parameter_overrides=tight,
    llm_overrides={'use_llm_wage': True},
)
print(result['on']['artifacts']['csv'])
```

**Robustness sweep (loose guards + firm/bank LLM)**

```python
loose = {
    'ncycle': 120,
    'llm_guard_preset': 'loose',
}

result = run_ab_demo(
    run_id=3,
    mode='robustness',
    parameter_overrides=loose,
    llm_overrides={'use_llm_firm_pricing': True, 'use_llm_bank_credit': True},
)
print(result['off']['ncycle'], result['on']['llm'])
```

> Both runs call into the legacy simulation directly; expect stdout noise from the
> Python 2 model until we stabilize logging during Milestone M6.
