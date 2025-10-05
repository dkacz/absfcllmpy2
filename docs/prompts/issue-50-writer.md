---
title: "Writer Brief — Issue #50 (M6-03)"
description: "Provide reusable narrative snippets for the firm/bank/wage A/B overlays (short-horizon OFF→ON comparison). All context included; writers lack repo access."
format:
  html:
    toc: true
    toc-depth: 2
---

# 1. Objective
- Build a **template pack** of short paragraphs that can be dropped into Results subsections or figure captions whenever we cite the **A/B overlays** (firm pricing, bank credit, wage bargaining).
- Each snippet should be reusable even after the overlays start diverging; note where text must be updated once live prompts replace the stub.
- Voice: concise, manuscript-ready prose that a writer can paste with minimal edits.

# 2. Shared Setup (applies to all snippets)
- Seed/run: `run_id = 0`
- Horizon: `ncycle = 200` (short-horizon tier for Milestone M6)
- Decider mode: deterministic **stub** (`python3 tools/decider/server.py --stub`, Temperature = 0)
- Guardrails: baseline preset (`δ_price = δ_wage = 0.04`, expectation bias cap 0.04, unit-cost floor, spread clamps)
- Hooks ON in LLM leg: firm pricing, bank credit, wage worker+offer
- Overlay styling: ON = **solid**, OFF = **dashed**, final 50 ticks shaded (grey)
- Figures/tables to cite:
  - **Firm:** Table @tbl-firm-ab, Figure @fig-firm-ab, `data/firm/firm_ab_table.csv`, `figs/firm/firm_ab_overlay.png`
  - **Bank:** Table @tbl-bank-ab, Figure @fig-bank-ab, `data/bank/bank_ab_table.csv`, `figs/bank/bank_ab_overlay.png`
  - **Wage:** Table @tbl-wage-ab, Figure @fig-wage-ab, `data/wage/wage_ab_table.csv`, `figs/wage/wage_ab_overlay.png`

# 3. Data Snapshots (current stub baseline)
## Firm metrics (Table @tbl-firm-ab)
```
scenario,metric,value
llm_on,inflation_volatility,0.0061805681026881705
llm_on,price_dispersion,0.20957101039825526
baseline,inflation_volatility,0.0061805681026881705
baseline,price_dispersion,0.20957101039825526
```
- Overlay: identical OFF/ON trajectory (stub rejects firm requests).

## Bank metrics (Table @tbl-bank-ab)
```
scenario,metric,value
llm_on,avg_spread,0.00889359407949925
llm_on,loan_output_ratio,1.287783914482426
llm_on,credit_growth,19012.88896143385
baseline,avg_spread,0.00889359407949925
baseline,loan_output_ratio,1.287783914482426
baseline,credit_growth,19012.88896143385
```
- Overlay: identical OFF/ON trajectory (stub returns deterministic fallback).

## Wage metrics (Table @tbl-wage-ab)
```
scenario,metric,value
llm_on,wage_dispersion,0.0021183807187412796
llm_on,fill_rate,0.5501397177771765
baseline,wage_dispersion,0.1441582030704589
baseline,fill_rate,0.3501829294414104
```
- Overlay: ON leg is flatter (guard clamps), baseline continues to drift.

# 4. Template Snippets
Each block below supplies an intro/linker sentence plus a paragraph that can be pasted as-is. Writers can choose between **baseline/stub** wording (current state) and **future/live mode** wording (to be used once OpenRouter prompts are active). Edit bold placeholders before publication.

## 4.1 Intro / lead-in options
- **Shared lead (current stub runs):**
  > “Using the short-horizon A/B runner (`run_id=0`, 200 ticks with the deterministic stub), we pair a baseline OFF leg with an ON leg that keeps all guardrails active (δ = 0.04, unit-cost floor, spread clamps). Figures @fig-firm-ab/@fig-bank-ab/@fig-wage-ab plot OFF as dashed and ON as solid with the final 50 ticks shaded.”

- **Future lead (once live mode lands):**
  > “All A/B overlays reuse the short-horizon runner (`run_id=0`, 200 ticks) and apply the live OpenRouter prompts under the baseline guard preset (δ = 0.04, expectation bias cap 0.04, enforce `p ≥ w/φ`). OFF traces reflect the legacy heuristics; ON traces show the guarded LLM path.”

## 4.2 Firm overlay snippets
- **Current stub baseline:**
  > “Figure @fig-firm-ab collapses to a single trajectory because the stub rejects every firm pricing request, leaving OFF and ON identical at `price_dispersion = 0.21` and `inflation_volatility = 0.006` (Table @tbl-firm-ab). The overlay establishes today’s parity baseline; we expect divergence only after live prompts replace the stub.”

- **Future live placeholder:**
  > “Figure @fig-firm-ab shows the guarded LLM path (solid) lifting/cutting prices relative to the baseline dashed trace. Table @tbl-firm-ab reports the corresponding changes in price dispersion and inflation volatility. Guardrails cap per-tick moves at δ = 0.04 and enforce the unit-cost floor, so even live prompts remain bounded.”

## 4.3 Bank overlay snippets
- **Current stub baseline:**
  > “Bank credit overlays (Figure @fig-bank-ab) still coincide—the stub falls back to the baseline leverage heuristic, so average spreads (`0.009`) and loan-to-output ratios (`1.29`) match across OFF and ON (Table @tbl-bank-ab). Use this as the visual control until a live credit officer prompt introduces soft-information deviations.”

- **Future live placeholder:**
  > “Figure @fig-bank-ab contrasts the baseline dashed spread path with the live LLM solid path. Table @tbl-bank-ab summarises the shift in loan-to-output ratios and average spreads. Guard clamps (50–500 bps) and monotonicity checks remain in force, so ON deviations reflect qualitative screening rather than unbounded lending.”

## 4.4 Wage overlay snippets
- **Current stub baseline:**
  > “Wage overlays already separate: the ON leg sticks to guard-clamped adjustments so wage dispersion collapses to `0.002` while OFF continues its adaptive drift (`0.144`), lifting fill rates from `0.35` to `0.55` (Table @tbl-wage-ab). Figure @fig-wage-ab uses the same dashed/solid convention, highlighting how guardrails alone can alter short-horizon outcomes even under the stub.”

- **Future live placeholder:**
  > “Once the live labour prompt is active, Figure @fig-wage-ab will juxtapose baseline inertia with LLM-coached settlements. Table @tbl-wage-ab should be updated with the latest wage dispersion and fill-rate deltas, noting that δ = 0.04 caps worker and firm steps while statutory floors remain enforced.”

## 4.5 Closing sentence options
- **Stub era:**
  > “Until live prompts ship, treat these overlays as calibration baselines: identical traces in firm/bank runs confirm the guard stack, while the wage clamp demonstrates how the same stack reshapes outcomes even without new heuristics.”

- **Live era:**
  > “Once OpenRouter prompts are online, update the paragraph with measured deltas (Δprice dispersion, Δspread, Δwage dispersion) and cross-reference the new why-code tables documented in `docs/blueprint.md`.”

# 5. Writer Checklist
- Deliver each snippet as Markdown that can drop straight into `docs/main.qmd` or any Results subsection.
- Preserve cross-reference syntax (`Table @tbl-…`, `Figure @fig-…`).
- For future-live placeholders, leave TODO comments if the numbers need refreshing when new artifacts land.
- Flag any edits to guard defaults if subsequent milestones change δ or the overlay styling conventions.
