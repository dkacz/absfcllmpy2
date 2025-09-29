# Horizon Stability Check — Architect Brief

**Baseline run:** OFF only, seed `run_id=0`, `ncycle=1001`, LLM toggles OFF. Outputs captured under `data/reference/hsc_1001_seed0/` with derived series in `data/reference/hsc_series.json`.

**Decision (2025-09-29):** Adopt A/B horizon **240**; keep scenarios **250**, robustness **120**; Bank KPIs = {average spread, loan-to-output ratio}. Credit growth is robustness-only overlay.

## Tail-window metrics

| Metric | T=120 | T=200 | T=240 | T=320 | T=400 |
|---|---|---|---|---|---|
| inflation | 0.013503 | 0.012964 | 0.012834 | 0.012962 | 0.012613 |
| price dispersion | 40.258961 | 50.419852 | 54.036348 | 57.873764 | 59.019611 |
| wage dispersion | 54.176803 | 83.097816 | 88.735406 | 92.907970 | 92.045233 |
| avg spread | 0.011553 | 0.011951 | 0.011928 | 0.011942 | 0.012093 |
| fill rate | 0.260853 | 0.271624 | 0.275789 | 0.287556 | 0.296508 |
| credit growth | 2.517707 | 4.883771 | 6.780562 | 19.227687 | 29.277086 |
| credit growth per tick | 0.011152 | 0.009447 | 0.009130 | 0.010058 | 0.009187 |

*Values pulled from `data/reference/hsc_stability_table.csv` (per-metric definitions: volatility/dispersion as σ, spreads/fill-rate as window means, credit growth both cumulative and per-tick change).* 

## Stability verdict

| Metric | Smallest stable window | Notes |
|---|---|---|
| inflation volatility | **120** | Within ±5% by T=120, stable through 400. |
| average spread | **160** | Within ±2%; negligible drift thereafter. |
| fill rate | **120** | Gradual upward trend but <5% change between 200 and 240. |
| price dispersion | **240** | Continues rising until ≥240; 200-tick snapshot is biased low. |
| wage dispersion | **240** | Similar to price dispersion; trend flattens only after 240. |
| credit growth | — | Monotonic climb; fails ±5% even at 1 000 ticks. |
| credit growth (per tick) | — | Still outside ±2% tolerance up to 1 000 ticks. |

*Source: `data/reference/hsc_summary.csv` (tolerance = 5% except avg spread/per-tick growth at 2%).*

## Observations

- **On-horizon metrics (keep T=200):** inflation, average spread, fill rate. These stabilise well before 200 ticks.
- **Metrics needing longer windows:** price and wage dispersion only level off after ~240 ticks. A 200-tick manuscript view understates long-run dispersion.
- **Credit growth:** both cumulative and per-tick forms violate the tolerance band even at 1 000 ticks. The series is trending rather than stationary; we must either normalise the KPI (e.g., growth rate relative to GDP) or accept a much longer horizon before reporting.

Convergence plots are available for review:
`figs/reference/hsc_convergence_{inflation,price_dispersion,wage_dispersion,avg_spread,fill_rate,credit_growth}.png`.

## Applied actions

1. Manuscript A/B runs now use **240** ticks; scenario and robustness horizons remain 250/120 respectively.
2. Bank A/B table reports **average spread** and **loan-to-output ratio**; credit growth is tracked only as a robustness overlay/figure.

Blueprint, assumptions, and runner defaults have been updated accordingly.

---
*Prepared for architect review. Raw data: `data/reference/hsc_series.json`, summarised QA page `docs/stability.qmd`.*
