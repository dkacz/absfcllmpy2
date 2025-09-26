# Manuscript Outline: Live LLM-Enhanced Behavioral Decisions in an AB-SFC Monetary Union

This outline follows the manuscript blueprint in `docs/blueprint.md` and treats GitHub issues and milestones as the source of truth. Issue references below use the form `#<number> (Mx-yy - title)` to map directly onto the backlog.

## 1. Introduction

**Focus:** Motivation, context, research questions, and contribution.
**Content Source:** `docs/blueprint.md` Section Section sec-exec, sec-rqs.
**Prose/Data supplied by:** #71 (M9-04 - Quarto manuscript "spine"), #72 (M9-05 - Writer: Title & abstract). A dedicated introduction issue may be opened under Milestone M9 if additional depth is required.

### 1.1 Motivation: Behavioral Heterogeneity in Macro-Finance
- **Legacy context:** Agent-Based Stock-Flow Consistent (AB-SFC) models provide rigorous accounting frameworks.
- **Legacy context:** Behavioral rules are typically stylized numeric heuristics (fixed adjustment speeds, simple expectations).
- **New LLM contribution:** Real-world decisions incorporate qualitative "soft" information; we add bounded LLM cues to capture this heterogeneity.
- **New LLM contribution:** Live LLM integration supplies qualitative guidance without replacing the underlying AB-SFC structure.

### 1.2 Baseline Model and Scope
- **Legacy context:** We reuse the Python 2 Caiani monetary-union codebase (multi-country, stock-flow consistent).
- **New LLM contribution:** A Python 3 LLM "Decider" microservice injects decisions for firm pricing, bank credit, and wage setting.
- **New LLM contribution:** **Scope disclaimer:** Treat the repo as a methods sandbox-not a replication of the original calibration (per blueprint Section sec-model).

### 1.3 Research Questions (RQ1-RQ3)
- **RQ1 (Firms):** Do LLM pricing cues change inflation volatility or price dispersion versus numeric heuristics?
- **RQ2 (Banks):** Does LLM-based soft information alter credit growth or average spreads?
- **RQ3 (Wages):** Do LLM wage cues affect wage dispersion or vacancy fill rates?

### 1.4 Contribution
- **Methods focus:** Safe, reproducible pattern for live LLM decisions inside an SFC framework.
- **Key features:** (i) Guards/floors to preserve accounting discipline, (ii) deterministic caching, (iii) transparent A/B reporting with CSV/PNG artifacts.

## 2. Methods

**Focus:** Baseline model recap, LLM architecture, integration, safety, and experimental design.
**Content Source:** `docs/blueprint.md` Section Section sec-model, sec-llm-design, sec-design.
**Prose/Data supplied by:** #16 (M2-01 - Code annotations with equation references), #17 (M2-02 - Aggregator: export base metrics), #18 (M2-03 - Variable dictionary), #20 (M2-05 - Quarto Methods hub page), #22 (M2-07 - Writer: "Model overview"), #68 (M9-01 - Methods draft).
**Quarto Reference:** `docs/methods/index.qmd` (to be authored in #20).

### 2.1 Baseline AB-SFC Model (Caiani implementation)
- Agents, markets, multi-country structure (K=5) and enforcing ledgers (`lebalance.py`).
- Equations targeted for augmentation: firms (Eq. 12-14), banks (Eq. 26-27), wages (Eq. 1, Eq. 15).
- Cross-reference to `docs/appendix_eq_map.qmd` (#74) and `docs/data_dictionary.qmd` (#76).

### 2.2 Live LLM Architecture ("Decider" microservice)
- Python 2 sim calls Python 3 localhost service; deterministic prompts (`temperature=0`).
- State-hash cache (#9, M1-03) and JSON Schema validation (#8, M1-02).
- Service stub and health check implemented in #7 (M1-01).

### 2.3 Integration, Guards, and Fallbacks
- Timeout handling and hard fallback to baseline (#11, M1-05).
- Toggle & configuration plumbing (#12, M1-06; #10, M1-04).
- Safety checks prior to state mutation: price step clamp & floor (#26, M3-03), spread clamps (#34, M4-03), wage step bounds (#43, M5-04).

### 2.4 Experimental Design: A/B Comparisons and Scenarios
- OFF vs ON runs with identical seeds; metrics aggregated via #17 (M2-02) and runners (#19, M2-04).
- Wage scenario configs (#55-#57) and long-run guidance (#60).
- Robustness demos (#62-#64) covering beta, K, and guard bounds.

## 3. Results

**Focus:** Present OFF/ON comparisons, wage scenarios, and robustness demos.
**Content Source:** `docs/blueprint.md` Section Section sec-design, sec-expectations.
**Prose/Data supplied by:**
- A/B blocks: #24-#30 (M3 Firm stream), #32-#38 (M4 Bank stream), #40-#46 (M5 Wage stream).
- Scenario work: #55-#59 (M7 Experiments) plus #58 (Quarto pages).
- Robustness: #62-#66 (M8 sensitivity, commentary).
- Manuscript integration: #69 (M9-02 - Results section).
**Quarto Reference:** `docs/ab_overview.qmd` (#29) and block-specific pages (#29, #37, #46).

### 3.1 Firms (RQ1)
- Compare inflation volatility and price dispersion; interpret relative to hypothesis (LLM holds more often when inventories normal).
- Artifacts: `data/firm_ab_table.csv`, `figs/firm_ab_overlay.png` from #28 (table/figure generation).
- Documentation: `docs/firm_ab.qmd` (#29).

### 3.2 Banks (RQ2)
- Evaluate credit growth and average spreads; relate to expectation of tighter approvals.
- Artifacts: `data/bank_ab_table.csv`, `figs/bank_ab_overlay.png` (#36).
- Documentation: `docs/bank_ab.qmd` (#37).

### 3.3 Wages (RQ3)
- Track wage dispersion and vacancy fill-rate; examine reservation/offer adjustments.
- Artifacts: `data/wage_ab_table.csv`, `figs/wage_ab_overlay.png` (#45).
- Documentation: `docs/wage_ab.qmd` (#46).

### 3.4 Wage-Regime Scenarios (A/B/C)
- Scenario A (single-country acceleration, #55) -> `docs/exp_A.qmd` (#58).
- Scenario B (single-country moderation, #56) -> `docs/exp_B.qmd` (#58).
- Scenario C (coordinated change, #57) -> `docs/exp_C.qmd` (#58).
- Narrative support: #59 (experiment write-ups).

### 3.5 Robustness Demonstrations
- beta sensitivity (#62) and country-count sensitivity (#63).
- Guard tightening/loosening stress test (#64) with manuscript commentary (#65) and caveat refresh (#66).
- Documentation: `docs/robustness.qmd` (authored under #65/#66).

## 4. Discussion

**Focus:** Interpretation, methodological implications, limitations, ethics.
**Content Source:** `docs/blueprint.md` Section sec-limits.
**Prose/Data supplied by:** #69 (Results integration), #70 (Discussion & limitations), #65-#66 (Robustness narrative), #72 (Title & abstract for framing).

### 4.1 Interpretation and Methodological Implications
- Synthesis of RQ1-RQ3 findings versus blueprint expectations.
- Emphasize guards/fallbacks enabling safe qualitative augmentation.

### 4.2 Limitations and Boundaries
- "Not a replication" reminder; dependence on specific LLM prompts/models.
- Focus on short horizons; long runs deferred to user (`run_by:user` issues #60, #63).

### 4.3 Ethics and Reproducibility
- Guardrails and fallback philosophy (#11, #34, #43).
- CSV/PNG + `.qmd` provenance and deterministic cache (#9, #17).

## 5. Conclusion

**Focus:** Concise summary and future work.
**Prose/Data supplied by:** #70 (Discussion & limitations) and future conclusion paragraph drafted under #71/#72.
- Reiterate methods contribution and highlight key comparative findings.
- Suggest future calibration, alternative LLMs, and extended horizons.

---

## Figure & Table Inventory

| id | type | focus | source path | generating issue(s) | owning milestone | dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| `fig-architecture` | figure | System architecture (Py2 sim <-> Py3 Decider, guards, cache) | `figs/methods/architecture.png` | #7, #8, #11 | M1 Bridge | #9 (cache), #12 (config) |
| `tbl-firm-ab` | table | Firm A/B metrics (inflation vol., price dispersion) | `data/firm_ab_table.csv` | #28 | M3 Firm | #24-#27, #17 |
| `fig-firm-ab-overlay` | figure | Firm variables overlay (OFF vs ON) | `figs/firm_ab_overlay.png` | #28 | M3 Firm | `tbl-firm-ab`, #29 |
| `tbl-bank-ab` | table | Bank A/B metrics (credit growth, average spread) | `data/bank_ab_table.csv` | #36 | M4 Bank | #32-#35, #17 |
| `fig-bank-ab-overlay` | figure | Bank variables overlay | `figs/bank_ab_overlay.png` | #36 | M4 Bank | `tbl-bank-ab`, #37 |
| `tbl-wage-ab` | table | Wage A/B metrics (dispersion, fill-rate) | `data/wage_ab_table.csv` | #45 | M5 Wage | #40-#44, #17 |
| `fig-wage-ab-overlay` | figure | Wage variables overlay | `figs/wage_ab_overlay.png` | #45 | M5 Wage | `tbl-wage-ab`, #46 |
| `fig-ab-overview` | figure | Multi-block synthesis (firm/bank/wage) | `figs/ab_overview.png` | #29 | M3 Firm | #28, #36, #45 |
| `fig-exp-A-panel` | figure | Scenario A outcomes (baseline vs LLM) | `figs/exp_A_panel.png` | #55, #58 | M7 Experiments | #19, #28/#36/#45 |
| `fig-exp-B-panel` | figure | Scenario B outcomes | `figs/exp_B_panel.png` | #56, #58 | M7 Experiments | same as above |
| `fig-exp-C-panel` | figure | Scenario C outcomes | `figs/exp_C_panel.png` | #57, #58 | M7 Experiments | same as above |
| `tbl-robustness-beta` | table | beta-sensitivity metrics | `data/robustness_beta.csv` | #62 | M8 Robustness | #17, #64 |
| `tbl-robustness-K` | table | Country-count sensitivity | `data/robustness_K.csv` | #63 | M8 Robustness | #17 |
| `tbl-robustness-bounds` | table | Guard bounds stress comparison | `data/robustness_bounds.csv` | #64 | M8 Robustness | #11, #34, #43 |

