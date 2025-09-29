# Assumptions and Open Questions (Issue #1 / M0-01)

This list captures assumptions made while drafting `papers/outline.md` and highlights confirmations needed from the executor or sign-off leads. Defaults let downstream work continue but should be verified before implementation commits are opened.

## 1. Backlog Mapping and Artifact Conventions

### 1.1 Issue Mapping
* Assumption: Outline references have been aligned to current GitHub issues (for example, M1-01 -> issue #7, M2-02 -> issue #17). If new issues are added or numbers change, update both `papers/outline.md` and this document.

### 1.2 Artifact Naming
* Assumption: Proposed artifact names (for scenarios, robustness tables, etc.) follow the pattern in `docs/blueprint.md` and current milestones.
* Default: Use names listed in the outline (for example, `figs/exp_A_panel.png`, `data/robustness_beta.csv`). Adjust only if implementation uncovers clashes or better conventions.

## 2. LLM Guard and Runtime Parameters

These parameters will be implemented primarily under issues #17 (M2-02), #11 (M1-05), #26 (M3-03), #34 (M4-03), and #43 (M5-04).

### 2.1 Firm Pricing (Eq. 12-14)
* Resolved: Cap on price adjustment step `delta` and expectation bias `delta_e` are 0.04 (baseline code).
* Decision: `delta = 0.04`, `delta_e = 0.04`.

### 2.2 Bank Spreads (Eq. 26-27)
* Resolved: Spread bounds remain at baseline code values (no changes).
* Decision: `bp_min = 50 bp`, `bp_max = 500 bp`.

### 2.3 Wage Steps (Eq. 1 and Eq. 15)
* Resolved: Wage step cap matches price cap (baseline).
* Decision: `delta = 0.04` (max 4 percent per tick).

### 2.4 LLM Service Timeout
* Resolved: Py2 client timeout derived from calibrated provider values (initial default 200 ms).
* Decision: initial default 200 ms; updated after calibration.

## 3. Experimental Design Parameters

These defaults will be consumed by runners (#19, #28, #36, #45, #55-#57, #62-#64) and manuscript drafts (#58, #69).

### 3.1 Horizon Length
* Resolved: Short horizons fixed per blueprint.
* Decision: A/B = 200 periods; scenarios = 250; robustness demos = 120.

### 3.2 Seeds and Run Counts
* Resolved: Single seed for manuscript artifacts.
* Decision: Use seed/run_id = 0; document in runners.

### 3.3 Scenario Parameter Shifts
* Resolved: Scenario shifts set via runtime overrides.
* Decision: `t0 = 50`.
  * Scenario A: `nu` reduced by 20 percent in country 0.
  * Scenario B: `nu` increased by 20 percent in country 0.
  * Scenario C: `nu` reduced by 10 percent in all countries.

### 3.4 Robustness Definition
* Resolved: Guard presets defined (tight/loose).
* Decision: Tight = 0.5x, Loose = 1.5x, spread adjustments as documented.
* Resolved: beta variation only at K = 5.
* Decision: beta in {beta0, 0.75beta0, 1.25beta0}; K fixed at 5.

## 4. Technical and Presentation Choices

* Resolved: Providers set to openai:gpt5-nano and google:gemini2.5-flash-lite via `DECIDER_PROVIDER`.
* Decision: Deterministic adapters per provider; see blueprint.

* Resolved: Overlay and table presentation rules fixed.
* Decision: See presentation defaults below (line styling, shading, rounding).

## 5. Outstanding Items

* Resolved: Issues #85 and #86 track introduction and conclusion writing.
* Done: blueprint updated 2025-09-26.
* Pending: long-run MC guidance still to be defined in issue #60.

### Finalized defaults (presentation & guards)

- delta_price = 0.04, delta_wage = 0.04, delta_e = 0.04; Tight = 0.5x, Loose = 1.5x.
- Overlays: one per block; ON solid, OFF dashed; shade last 50 periods; single legend.
- Horizons: A/B = **240**, Scenarios = **250**, Robustness = **120** (window = full run).
- Scenarios: A/B target country index 0; C applies to all five.
- Robustness: K = 5 only; beta in {beta0, 0.75beta0, 1.25beta0}; no heatmaps, no multi-K grid.
- Tables: CSV raw; Quarto shows 2-decimal ratios/spreads; comma-separated counts; captions include units.
- Bank KPIs: {avg_spread_pp, loan_to_output_ratio}. Credit growth appears only as a robustness overlay.
- One-off Horizon Stability Check (HSC): 1001-tick baseline, OFF only, seed=0; stability rule τ = 5% (inflation/dispersion/fill) and τ = 2% (spreads, per-tick credit overlay).

### Executor notes (for uniform implementation)

- Exporters should not round when writing CSV; apply rounding in Quarto table formatting.
- Figure filenames remain: `figs/firm/firm_ab_overlay.png`, `figs/bank/bank_ab_overlay.png`, `figs/wage/wage_ab_overlay.png`, robustness visuals under `figs/robustness/`.
- Table filenames remain: `data/firm_ab_table.csv`, `data/bank_ab_table.csv`, `data/wage_ab_table.csv`, robustness table `data/robustness_beta_table.csv`.
