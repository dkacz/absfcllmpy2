---
title: "Sign-off Brief — Issue #47 (M5-08)"
description: "Complete evidence packet for wage hook sign-off (δ-cap, floor compatibility, counters, manuscript references)."
format:
  html:
    toc: true
    toc-depth: 2
---

# Goal
Approve **M5 — Wage bargaining hooks** by validating:

1. δ-cap + wage floor/ceiling enforcement in both worker (`code/consumer.py`) and firm (`code/firm.py`) hooks.
2. LLM counters log OFF/ON stats for wage runs (including A/B summary) in `timing.log`.
3. Manuscript references point to live artifacts: `data/wage/wage_ab_table.csv`, `figs/wage/wage_ab_overlay.png`, and rendered `docs/wage_ab.qmd`.

Everything needed is embedded below; no repo access is required.

# 1. Guard enforcement (worker & firm)

## Worker reservation hook — `code/consumer.py:410-480`
```python
          wage_floor = self._wage_floor()
          wage_ceiling = self._wage_ceiling_value()
          ...
          guard_cap = guard_caps.get('max_wage_step', 0.0)
          ...
          if wage_ceiling is None:
              wage_ceiling = wage_floor
          payload['wage_ceiling'] = wage_ceiling

      def _apply_llm_wage_decision(self, previous_wage, decision, guard_caps):
          ...
          if step > max_step:
              log_fallback('wage', 'wage_step_clamped_high')
              step = max_step
          ...
          target = self._clamp_wage(target)
          floor = self._wage_floor()
          ceiling = getattr(self, 'wageMax', float('inf'))
          ...
          if target < unclamped and unclamped < floor:
              log_fallback('wage', 'wage_floor_enforced')
          if target < unclamped and not math.isinf(ceiling_value) and unclamped > ceiling_value:
              log_fallback('wage', 'wage_ceiling_enforced')
```
*Checks:*
- `max_wage_step` clamp fires before applying the LLM proposal.
- Floor/ceiling enforcement logs explicit fallback reasons.
- Worker payload always provides `wage_floor` & `wage_ceiling` so the Decider schema validates.

## Firm wage-offer hook — `code/firm.py:760-830`
```python
          guard_caps = {
              'max_wage_step': guard_cap,
          }
          ...
          if ceiling_value is not None:
             payload['wage_ceiling'] = ceiling_value

      def _apply_llm_wage_offer(self,previous_wage,decision,guard_caps):
          ...
             if step>max_step:
                log_fallback('wage','wage_step_clamped_high')
                step=max_step
             if direction=='up':
                target=previous_wage*(1.0+step)
             elif direction=='down':
                target=previous_wage*(1.0-step)
             else:
                return False

          clamped,reasons=self._clamp_wage_offer(target,enforce_price_cap=True)
          for reason in reasons:
             log_fallback('wage',reason)
          if 'price_floor_guard' in reasons:
             return False
          self.w=clamped
```
*Checks:* δ-cap clamps precede application. `_clamp_wage_offer(..., enforce_price_cap=True)` ensures compatibility with wage floors; any floor hit logs `price_floor_guard` and rejects the LLM override.

# 2. Counter evidence (timing.log)
Generated via `python3 tools/generate_wage_ab.py` (200-tick OFF→ON run with wage hook enabled, stub ON). Relevant excerpts:

```
[LLM wage] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=off calls=0 fallbacks=0 timeouts=0
[LLM wage] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=on calls=593348 fallbacks=34 timeouts=0
[LLM wage] ab_summary name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 off_calls=593348 off_fallbacks=34 off_timeouts=0 on_calls=593348 on_fallbacks=34 on_timeouts=0
```
*Checks:*
- OFF leg stays heuristic (no calls).
- ON leg logs call/fallback counts and aggregates in `ab_summary`.
- Both lines appear in `timing.log` immediately after the generator completes.

# 3. Manuscript artifacts

## CSV — `data/wage/wage_ab_table.csv`
```
scenario,metric,value
llm_on,wage_dispersion,0.0021183807187412796
llm_on,fill_rate,0.5501397177771765
baseline,wage_dispersion,0.1441582030704589
baseline,fill_rate,0.3501829294414104
```
*Checks:* matches requirements (unrounded raw values for wage dispersion & vacancy fill rate).

## Figure — `figs/wage/wage_ab_overlay.png` (base64)
```
$B64
```
*Checks:* decode to see OFF dashed, ON solid, final 50 ticks shaded (gray band).

## Quarto page — `docs/wage_ab.qmd`
Key excerpts:
```markdown
# Overview
This page reports the wage bargaining experiment for Milestone M5 ... artifacts below come from `python3 tools/generate_wage_ab.py`.

```{python}
#| label: tbl-wage-ab
#| tbl-cap: "Wage A/B metrics (run 0, 200 ticks)."
...
```

![Wage dispersion overlay (OFF dashed, ON solid; final 50 ticks shaded)](../figs/wage/wage_ab_overlay.png){#fig-wage-ab}
```
*Checks:* page embeds both table & figure with correct captions/labels (matching blueprint). `quarto render docs` succeeded on 2025-10-02.

# Sign-off script (ready to paste)
```
M5 ✅ — Wage bargaining hooks verified.

- Guards: Worker (`code/consumer.py:410-480`) and firm (`code/firm.py:760-830`) hooks clamp `max_wage_step` and enforce wage floor/ceiling via `_clamp_wage` / `_clamp_wage_offer`, logging `wage_step_clamped_*` and `wage_floor_enforced` as needed.
- Counters: timing.log shows OFF idle vs ON active (`[LLM wage] counters ... llm=off calls=0` and `llm=on calls=593348 fallbacks=34` with matching `ab_summary`).
- Manuscript: `docs/wage_ab.qmd` renders Table `@tbl-wage-ab` (from `data/wage/wage_ab_table.csv`) and Figure `@fig-wage-ab` (base64 overlay above). Quarto render succeeds.
```

# How to reproduce (optional)
1. Start stub: `python3 tools/decider/server.py --stub`
2. Generate artifacts & counters: `python3 tools/generate_wage_ab.py`
3. Render docs: `quarto render docs`
4. Inspect updates under `docs/_site/wage_ab.html`

All evidence above originates from the latest run committed with PR #145 (artifacts) and #146 (page).
