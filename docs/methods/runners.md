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

result = run_ab_demo(run_id=0, ncycle=50)
print(result['off']['folder'])
print(result['on']['folder'])
```

Key defaults:

- Output folders land under `artifacts/ab_demo/run_<seed>/<off|on>/` unless you provide
  `output_root`.
- `parameter_overrides` lets you tweak `Parameter` attributes (e.g., `{"ncycle": 120}`).
- `llm_overrides` applies only to the ON run so you can exercise a subset of hooks.
- The function returns metadata only; downstream issues (#48 and beyond) will enrich the
  dictionary with concrete CSV/PNG paths once exporters land.

> Both runs call into the legacy simulation directly; expect stdout noise from the
> Python 2 model until we stabilize logging during Milestone M6.
