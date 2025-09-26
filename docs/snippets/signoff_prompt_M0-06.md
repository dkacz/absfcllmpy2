# Signoff Prompt — Issue #6 (M0-06)

## Instructions for the Signoff Agent
- You do **not** have repository access. Base your decision solely on the evidence below.
- If every acceptance criterion for M0 is satisfied, reply on issue #6 with:
  - `M0 ✅`
  - Bullet links to the rendered landing page (`docs/_site/index.html`) and conventions page (`docs/_site/conventions.html`).
  - Confirmation that issue #6 is closed.
- If anything looks incomplete, list the blockers instead of approving.

## Evidence Bundle

### 1. Quarto project renders successfully
```
quarto render docs
[1/4] blueprint.md
[2/4] conventions.md
[3/4] index.qmd
[4/4] methods/decider.md
Output created: _site/index.html
```

### 2. Landing page (docs/index.qmd)
```
---
title: "Live LLM-Enhanced Behavioral Decisions in a Stock-Flow Consistent Agent-Based Monetary Union"
date: last-modified
page-layout: article
---

Welcome to the manuscript workspace for the live LLM project. This Quarto site collects the pages, figures, and tables described in the working outline.

- Build date: {{< meta date >}}
- For the full blueprint, see [docs/blueprint.md](blueprint.md).
- Upstream outline: `papers/outline.md`

> This site will expand as we implement the milestone tasks (M0 through M11). The landing page stays short on purpose so new sections can surface in their own `.qmd` files.

## Artifact conventions

For file naming, see the [Artifact Naming & Cross-Reference Conventions](conventions.md) page.

![Example overlay from `_examples`](../figs/_examples/sample_overlay.png){#fig-example-overlay}

::: {.table #tbl-example-metrics}
| scenario | metric | value |
| --- | --- | --- |
| baseline | price_dispersion | 0.012 |
| llm_on | price_dispersion | 0.009 |
| baseline | inflation_volatility | 0.021 |
| llm_on | inflation_volatility | 0.017 |
:::

The table above is drawn from `data/_examples/sample_metrics.csv`; future Quarto pages should cite the CSV when narrating results (for example, “see @tbl-example-metrics”).

## Ethics & scope

{{< include snippets/ethics_scope.md >}}
```

### 3. Ethics & scope disclaimer (docs/snippets/ethics_scope.md)
```
## Ethics & Scope Disclaimer

This study uses the Caiani monetary-union agent-based stock–flow consistent codebase as a sandbox for **methodological** experimentation. The Python 2 baseline we run today inherits parameter values, simplifications, and data-handling decisions that deviate from the 2017 paper; no attempt is made to recalibrate or reproduce that original macro path. Every result we show—figures, tables, or counter summaries—should therefore be read as **illustrative evidence** of the live LLM integration pattern, not as an empirical or policy replication.

The Python 3 Decider microservice injects bounded, qualitative cues at three behavioural junctions (firm pricing, bank credit, wage decisions). Guardrails clamp every LLM suggestion to the same floors, spreads, and unit-cost rules that govern the baseline heuristics. On any timeout, schema violation, or malformed reply, the simulation falls back immediately to the legacy numeric rule and logs the reason once. These guardrails are in place to avoid overstating what an LLM can do for real-time economic decision making while still letting us probe richer narrative behaviour.

All manuscript claims must cite the generated `data/` CSVs and `figs/` PNGs produced under short demonstration runs (`run_id = 0` with horizons ≤ 250 ticks). Longer Monte Carlo sweeps remain out of scope; users who re-run them should document their own configurations. Researchers and readers should treat the resulting manuscript as a **methods guide** with reproducible assets, not as an endorsement of any specific policy outcome.
```

### 4. Quickstart (AGENTS.md)
```
## Quickstart — Py2 Sim + Py3 Decider + Quarto

Run these from the repo root; keep the Decider stub in its own terminal while the sim executes.

1. **Start the Decider stub (Python 3).**

   ```bash
   python3 tools/decider/server.py --stub
   ```

   - Health check: `curl http://127.0.0.1:8000/healthz` should return `{ "status": "ok" }`.
   - Logs appear on stdout (and will later mirror into `logs/decider_stub.log`). Leave this process running.

2. **Kick a short baseline run (Python 2).**

   ```bash
   python2 code/timing.py
   ```

   - Default parameters cover 1001 ticks; for smoke tests temporarily set `Parameter.ncycle = 200` *locally* (do **not** commit) or switch to the demo runner from #19 once it lands.
   - Aggregates land in `data/`; runtime notes (and future LLM fallback counts) append to `timing.log`.

3. **Render the Quarto docs.**

   ```bash
   quarto render docs
   ```

   - Output site lives under `docs/_site/`; cite figures from `figs/` and tables from `data/` in the manuscript pages.
```

### 5. Naming conventions page (docs/conventions.md)
```
## Directory layout
- Figures live under `figs/<section>/`
- Tables / metrics live under `data/<section>/`
- Filenames are lowercase with descriptive suffixes (e.g., `_overlay`, `_table`).
- `_examples/` holds illustrative assets that can be cleaned up later.

## Filenames & labels
| asset type | pattern | example |
| --- | --- | --- |
| Firm A/B overlay figure | `figs/firm/firm_ab_overlay.png` | `figs/firm/firm_ab_overlay.png` |
| Bank A/B table | `data/bank/bank_ab_table.csv` | `data/bank/bank_ab_table.csv` |
| Wage scenario panels | `figs/experiments/exp_<scenario>_panel.png` | `figs/experiments/exp_A_panel.png` |
| Robustness tables | `data/robustness/robustness_<topic>_table.csv` | `data/robustness/robustness_beta_table.csv` |

Code sample:
```markdown
![Firm price overlay](../figs/firm/firm_ab_overlay.png){#fig-firm-ab}

::: {.table #tbl-firm-ab}
| scenario | metric | value |
| --- | --- | --- |
| baseline | price_dispersion | 0.012 |
| llm_on | price_dispersion | 0.009 |
:::
```

Referencing rules and example assets follow in the remainder of the page.
```

### 6. Manuscript outline present (papers/outline.md)
```
# Manuscript Outline: Live LLM-Enhanced Behavioral Decisions in an AB-SFC Monetary Union

This outline follows the manuscript blueprint in `docs/blueprint.md` and treats GitHub issues and milestones as the source of truth. Issue references below use the form `#<number> (Mx-yy - title)` to map directly onto the backlog.

## 1. Introduction
... (IMRaD structure continues with figures/tables inventory)
```

### 7. Rendered HTML assets
- Landing page: `docs/_site/index.html`
- Conventions page: `docs/_site/conventions.html`
- Decider stub doc: `docs/_site/methods/decider.html`

Use the evidence to confirm every acceptance criterion for M0-06 before approving.
