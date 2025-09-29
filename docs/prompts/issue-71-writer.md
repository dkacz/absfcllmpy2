# Writer Brief — Manuscript Spine (Issue #71)

This document inlines everything a writer needs. You do **not** need repository access.

## Project snapshot

- **Objective:** Document how live LLM decision cues modify the Caiani agent-based, stock-flow consistent (AB-SFC) macro model. Legacy Python 2 logic stays intact; LLM hooks sit on firm pricing, bank credit, and wage formation.
- **LLM integration:** Python 3 Decider stub at `http://127.0.0.1:8000`, toggled via `code/parameter.py`. Guardrails follow `docs/blueprint.md`: price/wage step cap 0.04, expectation-bias cap 0.04, spread clamps, leverage monotonicity, unit-cost floor `p >= w/phi`, and hard timeouts with fallback to baseline heuristics.
- **Horizon & KPI decisions (HSC OFF run):** A/B = 240 ticks, Scenarios = 250 ticks, Robustness = 120 ticks. Bank KPIs now headline **average spread** and **loan-to-output ratio**; credit growth becomes an overlay.
- **Canonical artifacts (PR #108 / Issue #17):** `data/core_metrics.csv`, `data/reference/hsc_summary.csv`, `data/reference/hsc_stability_table.csv`, convergence PNGs in `figs/reference/`, and the narrative captured in `docs/stability.qmd`.

## Full source content (verbatim)

### docs/main.qmd (manuscript spine)

<pre><code>---
title: &quot;Live LLM-Enhanced AB-SFC Manuscript&quot;
date: last-modified
page-layout: article
format:
  html:
    toc: true
    toc-depth: 2
    number-sections: true
---

::: {.callout-note}
This spine pulls together the manuscript sections tracked across Milestones M8-M11. Writing issues (e.g. #68, #69, #70, #85, #86) will replace the placeholders below as those drafts land.
:::

# Abstract {#sec-abstract}

_TBD — populated by Issue #72 once the abstract draft is ready._

# Introduction {#sec-introduction}

The introduction will situate the live LLM hooks within the Caiani agent-based, stock-flow consistent (AB-SFC) model. Draft lives in Issue #85; once merged, the text slots here and will cite the methodological blueprint (@sec-methods) and stability evidence (@sec-results-hsc).

# Methods {#sec-methods}

## Model and baseline guardrails {#sec-methods-model}

- Canonical Caiani model remains intact (legacy Python 2 codebase); see `docs/blueprint.md` (§Model in brief) for the full equation map.
- Guardrails (price floor, leverage clamps, timeout fallbacks) mirror the defaults documented in `docs/blueprint.md` (§Presentation &amp; guard defaults).
- Appendix A (Issue #74) will surface a dedicated equation-to-code table once delivered.

## Live LLM instrumentation {#sec-methods-llm}

- Python 3 Decider stub (`tools/decider/server.py --stub`) responds on `http://127.0.0.1:8000`; toggles live in `code/parameter.py`.
- Py2 client wiring is covered in `docs/methods/py2_client.md`, including timeout conversion and JSON-schema enforcement.
- Bank, firm, and wage prompts share the qualitative pattern recorded in `docs/methods/decider.md`; the cache design (Issue #68) will be summarized here when ready.

## Simulation workflow {#sec-methods-sim}

1. Launch the Decider stub (Python 3).
2. Run the Py2 simulation (`python2 code/timing.py`) with the desired horizon (baseline OFF/ON windows = 240 ticks per PR #108).
3. Persist aggregates under `data/` and figures under `figs/`; rerun `quarto render docs` once new artifacts land.

Issue #77 will extend this section with reproducibility checklists and automation details.

# Results {#sec-results}

## Core manuscript metrics {#sec-results-core}

&#96;&#96;&#96;{python}
import pandas as pd
from pathlib import Path

core = pd.read_csv(Path(&quot;../data/core_metrics.csv&quot;))
# Focus on baseline OFF run for the spine summary
baseline = (
    core.query(&quot;scenario == &#x27;baseline&#x27;&quot;)
        .pivot(index=&quot;metric&quot;, columns=&quot;scenario&quot;, values=&quot;value&quot;)
        .rename_axis(None, axis=1)
)
baseline
&#96;&#96;&#96;

::: {.callout-tip}
A/B results will add comparative columns once Issue #69 (Results integration) lands. For now, the baseline run (seeded by PR #108) establishes the canonical reference values.
:::

## Horizon stability evidence {#sec-results-hsc}

- Horizon Stability Check (HSC) OFF run: see `docs/stability.qmd` for full commentary.
- Canonical artifacts: `data/reference/hsc_summary.csv`, `data/reference/hsc_stability_table.csv`, and the convergence plots under `figs/reference/`.

Future subsections will cover the A/B overlays, robustness sweeps, and wage/bank tables once their CSV/PNG outputs are refreshed for the 240-tick horizon.

# Discussion &amp; outlook {#sec-discussion}

Discussion threads (limitations, policy takeaways, open questions) map to Issues #70 and #86. Once drafted, this section will cite:

- Narrative comparisons between baseline heuristics and LLM-mediated behaviours.
- Implications for macro-financial stability, tying back to the guardrails noted in @sec-methods-model.
- Future work on batch decision hooks and live LLM failover modes (tracked in blueprint roadmap).

# Appendices &amp; companion material {#sec-appendices}

- **Appendix A (Equation map).** `docs/appendix_eq_map.qmd` (Issue #74).
- **Appendix B (JSON schemas).** Issue #75 will capture schema excerpts for firm, bank, and wage endpoints.
- **Repro Manual.** `docs/repro_manual.qmd` (Issue #77) to detail end-to-end rebuild instructions.
- **Horizon Stability Notes.** Consult `docs/stability.qmd` for the OFF-run analysis that now replaces the retired architect brief.

Once these pages exist, update this list with direct `@ref` cross-references so Quarto can number them alongside the main manuscript.
</code></pre>

### docs/stability.qmd (renderable without R)

<pre><code>---
title: &quot;Horizon Stability Check&quot;
format:
  html:
    toc: true
    toc-depth: 2
---

## Overview

We ran a single 1001-tick baseline (OFF only, seed=0) to validate the short-horizon settings outlined in `docs/blueprint.md`. For each manuscript metric we recomputed tail-window estimates using windows `T ∈ {120,160,200,240,280,320,360,400,500,750,1000}`. A window is considered stable when two consecutive step comparisons satisfy the tolerance rule from the blueprint addition (`τ = 5%`, except `τ = 2%` for average spreads).

## Stability summary

&#96;&#96;&#96;{python}
import pandas as pd

hsc = pd.read_csv(&quot;../data/reference/hsc_summary.csv&quot;)
hsc
&#96;&#96;&#96;

Metrics that meet the tolerance rule by `T = 200` (inflation volatility, price dispersion, average spread, fill rate) confirm the existing A/B horizons. Credit growth and wage dispersion do not stabilise within 1 000 ticks; their series continue to trend, so keeping 200-tick snapshots would systematically understate their long-run behaviour.

## Convergence plots

&#96;&#96;&#96;{python}
from pathlib import Path
from IPython.display import display, Image

for plot in sorted(Path(&quot;../figs/reference&quot;).glob(&quot;hsc_convergence_*.png&quot;)):
    display(Image(filename=str(plot)))
&#96;&#96;&#96;

## Next steps

* Manuscript horizons adopted: **A/B = 240**, **Scenarios = 250**, **Robustness = 120** (window = full run).
* Bank KPI swap: headline metrics are **average spread** and **loan-to-output ratio**; credit-growth remains as a robustness overlay.
* Wage and price dispersion now use the 240-tick window; their Quarto tables should cite the new horizon in captions.

All raw series are stored in `data/reference/hsc_series.json` for future inspection.
</code></pre>

### docs/_quarto.yml (nav configuration)

<pre><code>project:
  type: website
  output-dir: _site
  title: &quot;Live LLM-Enhanced Behavioral Decisions&quot;
  resources:
    - ../figs
    - ../data

website:
  navbar:
    left:
      - text: &quot;Home&quot;
        href: index.qmd
      - text: &quot;Manuscript&quot;
        href: main.qmd
      - text: &quot;Blueprint&quot;
        href: blueprint.md
      - text: &quot;Conventions&quot;
        href: conventions.md
      - text: &quot;Decider Stub&quot;
        href: methods/decider.md
      - text: &quot;Py2 Client&quot;
        href: methods/py2_client.md

format:
  html:
    theme: cosmo
    toc: true
</code></pre>

### Baseline data tables

`data/core_metrics.csv`

<pre><code>scenario,metric,value
llm_on,price_dispersion,0.16932996561384545
llm_on,avg_spread,0.009963822788659826
llm_on,fill_rate,0.3909319689400087
llm_on,wage_dispersion,0.22413959886601806
llm_on,loan_output_ratio,1.3787753525286761
llm_on,inflation_volatility,0.0056950186751849536
baseline,price_dispersion,0.16932996561384545
baseline,avg_spread,0.009963822788659826
baseline,fill_rate,0.3909319689400087
baseline,wage_dispersion,0.22413959886601806
baseline,loan_output_ratio,1.3787753525286761
baseline,inflation_volatility,0.0056950186751849536
</code></pre>

`data/reference/hsc_summary.csv`

<pre><code>metric,recommended_window,note
avg_spread,160,
credit_growth,,No stable window ≤1000 (τ=5%)
credit_growth_per_tick,,No stable window ≤1000 (τ=2%)
fill_rate,120,
inflation,120,
price_dispersion,240,
wage_dispersion,240,
</code></pre>

`data/reference/hsc_stability_table.csv`

<pre><code>metric,window,value
inflation,120,0.013502894150110509
inflation,160,0.01340738776462835
inflation,200,0.012963563197103765
inflation,240,0.012834167599153573
inflation,280,0.012951129612773896
inflation,320,0.012962077610779055
inflation,360,0.012761259119921783
inflation,400,0.012613310739053848
inflation,500,0.012875836500189778
inflation,750,0.01159343503611985
inflation,1000,0.010436910885730422
price_dispersion,120,40.258960531989345
price_dispersion,160,45.78874527917132
price_dispersion,200,50.419851925102016
price_dispersion,240,54.03634756737063
price_dispersion,280,56.39667637286535
price_dispersion,320,57.87376362378603
price_dispersion,360,58.7096248764401
price_dispersion,400,59.0196110876044
price_dispersion,500,58.78651788653682
price_dispersion,750,55.26251479216961
price_dispersion,1000,50.974347848426135
wage_dispersion,120,54.17680286993805
wage_dispersion,160,69.60510373703758
wage_dispersion,200,83.09781645440819
wage_dispersion,240,88.73540624027689
wage_dispersion,280,91.41928042471694
wage_dispersion,320,92.90796971700439
wage_dispersion,360,92.72175129433728
wage_dispersion,400,92.04523297350812
wage_dispersion,500,90.01404706956266
wage_dispersion,750,82.33883767019367
wage_dispersion,1000,74.99455271422994
avg_spread,120,0.011552861615331983
avg_spread,160,0.01180605012453064
avg_spread,200,0.011950575686974036
avg_spread,240,0.01192785065743054
avg_spread,280,0.011908329040521573
avg_spread,320,0.011941606915841441
avg_spread,360,0.011984899958283278
avg_spread,400,0.012093058306818791
avg_spread,500,0.012432460728315331
avg_spread,750,0.01314908514101868
avg_spread,1000,0.012429278104500249
fill_rate,120,0.2608530143618158
fill_rate,160,0.26398569562444707
fill_rate,200,0.2716236876799224
fill_rate,240,0.27578934992446463
fill_rate,280,0.28164444007338557
fill_rate,320,0.28755603484404435
fill_rate,360,0.2925368394141293
fill_rate,400,0.2965079278871676
fill_rate,500,0.3000278763587511
fill_rate,750,0.2990722487701343
fill_rate,1000,0.32045102006853776
credit_growth,120,2.5177066050853147
credit_growth,160,3.0287228120756935
credit_growth,200,4.8837711346635455
credit_growth,240,6.780561934324284
credit_growth,280,11.271283782306122
credit_growth,320,19.227687275276548
credit_growth,360,22.497185439946254
credit_growth,400,29.277086493391778
credit_growth,500,79.25950379687485
credit_growth,750,456.3832334990004
credit_growth,1000,1.0
credit_growth_per_tick,120,0.011152179782977388
credit_growth_per_tick,160,0.009329561382728736
credit_growth_per_tick,200,0.009447370307072071
credit_growth_per_tick,240,0.009129587896145867
credit_growth_per_tick,280,0.009569186491657259
credit_growth_per_tick,320,0.010057653693115613
credit_growth_per_tick,360,0.009423572354113636
credit_growth_per_tick,400,0.009187283567340072
credit_growth_per_tick,500,0.009506254844342202
credit_growth_per_tick,750,0.008891042973606336
credit_growth_per_tick,1000,0.18205314256988206
</code></pre>

For completeness, tail-series CSVs live in `data/reference/hsc_1001_seed0/` (`muxSnCo5upsilon20.7polModPolVar0.512r0AggData.csv`, `muxSnCo5upsilon20.7polModPolVar0.512r0Para.csv`) and can be referenced if long-form data is needed.

### Convergence plot filenames

Reference these when drafting figure captions:

- `figs/reference/hsc_convergence_inflation.png`
- `figs/reference/hsc_convergence_price_dispersion.png`
- `figs/reference/hsc_convergence_wage_dispersion.png`
- `figs/reference/hsc_convergence_avg_spread.png`
- `figs/reference/hsc_convergence_credit_growth.png`
- `figs/reference/hsc_convergence_fill_rate.png`

## Section ownership & expectations

| Section | Anchor | Owner issue | Target scope |
| --- | --- | --- | --- |
| Abstract | `#sec-abstract` | #72 | 150-250 words, headline the method and core metrics. |
| Introduction | `#sec-introduction` | #85 | 600-900 words. Frame Caiani baseline vs. live LLM hooks, cite guardrails & stability choices. |
| Methods | `#sec-methods` | #68, #74, #75, #77 | Fill out guardrails, decider service, Py2 client, workflow. Keep existing subsections/anchors. |
| Results | `#sec-results` | #69 | Integrate OFF vs. ON tables/overlays, cite stability evidence, refer to CSV/PNG artifacts. |
| Discussion & outlook | `#sec-discussion` | #70 | Cover behavioural insights, limitations, policy implications, future enhancements (batch hooks, failover). |
| Appendices & companion material | `#sec-appendices` | #74, #75, #77 | Turn bullets into `@ref` cross-references once appendices exist; remind readers of HSC brief. |

## Writing guidance

1. **Keep anchors intact** so cross-references remain stable (`{#sec-...}`).
2. **Cite evidence** by path (e.g., “See `data/core_metrics.csv`). Mention fallback behaviour from `docs/methods/py2_client.md` where relevant.
3. **Narrative flow:** Methods should first restate Caiani structure, then describe the LLM instrumentation; Results should compare OFF vs. ON once data updates land; Discussion should connect behaviour to guardrails and open questions (batch mode, failover, credit growth instability).
4. **Style:** Follow repository conventions (`docs/conventions.md`): formal, third-person, present tense.
5. **Validation:** After edits, run `quarto render docs` so the Python chunks execute and tables/figures render without R.

## Deliverable checklist for writers

- [ ] Replace placeholder text in your assigned section(s) within `docs/main.qmd` (source above).
- [ ] Extend the Python table chunk in `#sec-results-core` to show ON/OFF comparisons when updated metrics arrive.
- [ ] Add figure/table references and ensure Quarto numbering resolves after rendering.
- [ ] Provide metric values + file paths in your issue comment as evidence when handing off for review.

This brief contains all current context as of Issue #71 completion. Use it directly—no repository access is required.
