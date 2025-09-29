---
title: "Live LLM–Enhanced Behavioral Decisions in a Stock–Flow Consistent Agent‑Based Monetary Union"
subtitle: "A manuscript blueprint for the Caiani AB‑SFC codebase with live, bounded LLM hooks"
authors: ["Project Team (Executor + Writer LLM)"]
date: "YYYY-MM-DD"
keywords: [agent-based, stock-flow consistency, behavioral rules, monetary union, wages, bank credit, pricing, LLM, qualitative heuristics]
format:
  html:
    toc: true
    toc-depth: 3
    number-sections: true
---

# Executive summary {#sec-exec}

We study how **bounded, qualitative decision cues from a Large Language Model (LLM)**—embedded *live* into a classic **Agent‑Based Stock–Flow Consistent (AB‑SFC)** macro model—affect short‑run macro‑financial dynamics under different wage regimes. We do **not** attempt to replicate the original paper’s calibration or results. Instead, we keep the **Python 2 Caiani code** *as‑is* and interpose LLM decisions **at runtime** for three behavioral functions:

1. **Firm pricing & expectations** *(eq. 12–14)* – whether and by how much to adjust prices given backlog/inventory/costs.
2. **Bank credit approval & spread setting** *(eq. 26–27)* – soft‑information flavored accept/limit/spread.
3. **Wage setting** – **worker reservation wage** *(eq. 1)* and **firm offered wage** *(eq. 15)*.

The LLM runs as a **Python 3 localhost microservice**. The sim (Python 2) calls it per decision, with **hard timeouts, strict bounds, and baseline fallback**. We compare **A/B** (baseline numeric rule vs. live LLM rule) under small‑horizon runs and document differences via **Quarto pages** and **portable CSV/PNG artifacts**.

# Research questions & proposed contribution {#sec-rqs}

**RQ1.** Do live, qualitative pricing cues (via LLM) measurably change **inflation volatility** or **price dispersion** relative to fixed numeric heuristics?

**RQ2.** Does introducing soft‑information‑like loan screening (via LLM) alter the **loan-to-output ratio** and **average spreads** in ways consistent with narrative banking behavior (credit-growth trends shown as overlays only)?

**RQ3.** Do LLM‑mediated wage decisions change **wage dispersion** and **vacancy fill‑rates** in a direction consistent with qualitative labor‑market accounts?

**Contribution.** A **methods contribution**: a disciplined pattern for **live LLM decisions inside AB‑SFC** with (i) stock‑flow safety via **guards and floors**, (ii) **deterministic** caching, and (iii) transparent **A/B reporting** that is publishable (Quarto) and reproducible (CSV/PNG).

# Model in brief (baseline Caiani code) {#sec-model}

- **Agents:** households/workers, firms, banks, a monetary‑union central bank, and a government sector across multiple countries (5 in the code).
- **Markets:** consumption with Hotelling matching; labor market with wage formation and hiring shortfalls; credit market with bank rationing; bond & deposit markets; fiscal and monetary policy blocks.
- **Accounting:** **Stock–flow consistency** enforced by ledgers (`lebalance.py`).
- **Equations of interest (by paper numbering):**
  - **Wages:** worker reservation *(eq. 1)*; firm offered wage *(eq. 15)*.
  - **Firms:** inventories, **pricing & expectations** *(eq. 12–14)*.
  - **Banks:** loan approval probabilities, **spreads** *(eq. 26–27)*.
  - Policy blocks *(eq. 26–37)* retained but not LLM‑augmented.

> **Scope disclaimer.** The current repo’s parameters and outcomes **differ** from the original Caiani calibration; this study treats the existing code as a **sandbox** for methods.

# Live LLM design (what changes, what stays safe) {#sec-llm-design}

**What changes (live, per tick):**
- **Firms (eq. 12–14):** `direction ∈ {up,down,hold}`, `step ∈ [0, δ]`, optional `exp_bias ∈ [−δ_e, +δ_e]`.
- **Banks (eq. 26–27):** `{approve ∈ {0,1}, credit_limit ≤ demand, spread_bp ∈ [bp_min, bp_max]}`.
- **Wages (eq. 1, 15):** `direction ∈ {up,down,hold}`, `step ∈ [0, δ]`.

**LLM call contract (server‑side):**
- **Deterministic** (`temperature=0`), **state‑hash cache**, **JSON Schema** validation.
- **Timeouts** (e.g., 100 ms). On timeout/invalid JSON ⇒ **baseline fallback**.
- **Guards applied in Py2** *before* state updates: **clip steps**, **enforce unit‑cost price floor** `p ≥ w/φ`, **spread clamps**, **monotonicity** vs leverage.

**Philosophy:** the LLM supplies **qualitative cues** informed by local states; it **does not** optimize or rewrite the model. It augments choice under uncertainty where **theory‑of‑choice/firm** admits narrative heterogeneity.

# Experimental design & metrics {#sec-design}

**A/B Design (small horizon).** Run OFF (baseline numeric rules) then ON (live LLM), **same seed**, export:
- **Firm block:** `data/firm_ab_table.csv` → **inflation volatility**, **price dispersion**; `figs/firm_ab_overlay.png`.
- **Bank block:** `data/bank_ab_table.csv` → **loan-to-output ratio**, **average spread** (credit growth overlay only in robustness); `figs/bank_ab_overlay.png`.
- **Wage block:** `data/wage_ab_table.csv` → **wage dispersion**, **vacancy fill‑rate**; `figs/wage_ab_overlay.png`.

**Scenario set (illustrative):**
1. **A: Wage acceleration (1 country)** – lower wage sensitivity parameter υ at t₀.
2. **B: Wage moderation (1 country)** – raise υ at t₀.
3. **C: Coordinated change (all countries)** – uniform υ shift.

**Robustness demos:** parameter **β** (price sensitivity) and **K** (countries) small demos; **bounds stress** (tighter vs looser guards).

# Expected qualitative effects (testable sketches) {#sec-expectations}

- **Firms:** LLM may tilt toward **hold** when inventories normal & costs flat → **lower price dispersion**, possibly **lower inflation volatility**.
- **Banks:** LLM may **tighten approval** for high‑leverage borrowers (soft info cue) → **lower loan-to-output ratios** and **higher mean spreads** under stress (credit growth shown as a robustness overlay).
- **Wages:** LLM may **raise reservation** under low unemployment and **raise offers** when fill‑rates poor → **higher wage dispersion** with **improved fill‑rates**.

# Artifacts & Quarto plan {#sec-artifacts}

**Conventions.** Figures in `figs/<block>/...png`, tables/metrics in `data/<block>/...csv`. Every artifact is referenced by at least one `.qmd` page.

**Pages (Quarto):**
- `docs/index.qmd` — landing, scope, navigation.
- **Methods hub:** `docs/methods/index.qmd` + subpages: Decider, Py2 client, fallbacks, equation map, variables, runners.
- **A/B pages:** `docs/firm_ab.qmd`, `docs/bank_ab.qmd`, `docs/wage_ab.qmd`, plus `docs/ab_overview.qmd`.
- **Experiments:** `docs/exp_A.qmd`, `docs/exp_B.qmd`, `docs/exp_C.qmd`.
- **Robustness:** `docs/robustness.qmd`.
- **Manuscript spine:** `docs/main.qmd` stitching Methods, Results, Discussion; appendices:
  - `docs/appendix_eq_map.qmd`, `docs/appendix_schemas.qmd`, `docs/data_dictionary.qmd`.

# Limitations & ethics {#sec-limits}

- **Not a replication.** Repo parameters differ from Caiani (2017). Results are **illustrative**.
- **LLM guardrails.** Decisions are **bounded** and **fallback‑protected**; we do **not** claim optimality or normative superiority.
- **Reproducibility.** All claims trace to **CSV/PNG + `.qmd`** under versioned paths; long runs are user‑initiated, with small demos included.

# Blueprint→Outline mapping {#sec-map}

The Writer’s `papers/outline.md` must mirror this blueprint: IMRaD sections, the specific **A/B tables/figures**, scenario and robustness sections, and explicit cross‑refs to the **exact artifact filenames** and **Quarto page paths** listed above.

## Run logistics & LLM backend (agreed)

**Short-horizon artifacts (manuscript figures/tables)**  
- Use a single seed (`run_id=0`).  
- Horizons: A/B comparisons **240** periods; scenario demos **250**; robustness demos **120**.  
- Baseline parameter files stay untouched; horizons and scenario tweaks are passed as runtime overrides in the A/B runner function (window = full run).

### Horizon stability check (HSC) — one-off QA
A single 1001-tick baseline (OFF only, seed=0) validates these short-horizon choices. Metrics are recomputed on tail
windows `T ∈ {120,160,200,240,280,320,360,400,500,750,1000}`. Stability requires `|m(T) - m(T+40)| / |m(T+40)| ≤ 5%`
(2% for average spread) for two consecutive steps. If `T = 200` passes, manuscript horizons stay A/B = 200, scenarios = 250,
robustness = 120; otherwise we raise only the failing block to the smallest `T` that passes. Artifacts: `data/reference/hsc_stability_table.csv`,
`figs/reference/hsc_convergence_<metric>.png`, and `docs/stability.qmd`.

**Guard-stress presets (robustness demos only)**  
- Tight: `δ_price = 0.5x`, `δ_wage = 0.5x`, `bp_min += 50bp`, monotonicity tolerance `ε = 0`.  
- Loose: `δ_price = 1.5x`, `δ_wage = 1.5x`, `bp_min` unchanged, monotonicity tolerance `ε = 1e-6`.  
- All guards still enforce stock-flow safety and floors.

**LLM providers under test**  
- `DECIDER_PROVIDER = openai:gpt5-nano` or `google:gemini2.5-flash-lite`.  
- Deterministic (`temperature=0`), JSON-only contract, state-hash cache.  
- Timeout calibration: for each provider, send 200 calls per endpoint, set `LLM_TIMEOUT_MS = min(300, ceil(p95 + 30ms))`; cap at 350ms. Initial default: 200 ms.  
- On timeout/invalid JSON: baseline fallback with a one-line reason logged; A/B counters report calls/timeouts/fallbacks.

### Presentation & guard defaults (final)

**Guard caps (baseline & presets)**  
- Price step cap: `δ_price = 0.04`.  
- Wage step cap: `δ_wage = 0.04`.  
- Expectation-bias cap: `δ_e = 0.04`.  
- Presets: Tight = 0.5x caps; Loose = 1.5x caps.  
- Guard rules unchanged elsewhere (unit-cost floor `p ≥ w/φ`; spread clamps; leverage monotonicity; `ε` as above).

**Overlay presentation (A/B)**  
- One overlay per block (firm, bank, wage); OFF vs ON on the same axes.  
- Styling: ON = solid; OFF = dashed; consistent legend; shade the final 50 periods.

**Scenario country selection**  
- A/B single-country scenarios use country index 0.  
- Coordinated scenario applies to all five countries.

**Robustness scope**  
- `K = 5` only (no K sweep, no heatmaps).  
- β variation only at `K = 5`: baseline, +25%, −25% lines plus a compact comparison table.

**Tables: rounding & units**  
- CSVs store raw numeric values.  
- Quarto rendering: ratios & spreads to 2 decimals; counts with comma separators; captions spell out units.
