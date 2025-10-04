---
title: "Sign-off Brief — Issue #54 (M6-07)"
description: "Evidence packet for A/B overlays & how-to page (Milestone M6 sign-off). All context inline; no repo access required."
format:
  html:
    toc: true
    toc-depth: 2
---

# Goal
Approve **M6 — A/B Runner & Overlays** by confirming:

1. `docs/ab_overview.qmd` renders the firm/bank/wage overlays with shared run settings (`run_id=0`, `ncycle=200`, stub ON), proper captions, and figure references (`fig-firm-ab`, `fig-bank-ab`, `fig-wage-ab`).
2. `docs/howto_ab.qmd` documents the three-step reproduction path (stub → `python2` `run_ab_demo` → `quarto render docs`) with guard/override guidance.
3. Landing page (`docs/index.qmd`) links both pages under the Milestone M6 section so readers can find the overview and how-to without digging through the repo.
4. Rendered outputs exist in `_site/` and match the latest Quarto build; overlay PNGs match the checksums listed below.

Everything required is embedded on this page.

# Acceptance Criteria (from Issue #54)
- Sign-off comment must report “M6 ✅” with links to the rendered overview and how-to pages.
- Dependencies (#48, #49, #51) are now closed; no blockers remain.

# Artifacts & Integrity Checks
- Rendered pages: `docs/_site/ab_overview.html`, `docs/_site/howto_ab.html` (produced by `quarto render docs`).
- Overlay PNGs:
  - `figs/firm/firm_ab_overlay.png` — SHA256 `d50844d4c74400e7f165142c3e0d4ee864a98715570696052b41f03afddd3088`
  - `figs/bank/bank_ab_overlay.png` — SHA256 `695ebe65ea3a30c24c68acbe08af37c2a04f1b8ce5d4868b8685d37276ecc9c3`
  - `figs/wage/wage_ab_overlay.png` — SHA256 `73968cbf0408cdce5decacf0ebae2968f2b79dc1463c195389c70e00c63f470c`
- Runner outputs referenced in captions derive from the deterministic stub (`run_id=0`, `ncycle=200`) used across the block pages.

# Source Content (inline)
## docs/ab_overview.qmd
```markdown
---
title: "A/B Overlay Overview"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

# Snapshot
The short-horizon A/B experiments share a common configuration: `run_id = 0`, `ncycle = 200`, and the deterministic Decider stub. Each overlay compares the legacy baseline (OFF) against the guard-railed LLM path (ON) with OFF rendered as a dashed line, ON as a solid line, and the final 50 ticks shaded for manuscript alignment.

## Overlays at a glance
All three overlays originate from the runner outputs documented on the block-specific pages. The captions restate the run settings and call out the detailed figure identifiers (`fig-firm-ab`, `fig-bank-ab`, `fig-wage-ab`) so cross-references in the manuscript remain stable.

::: {.layout-ncol=1}
![Firm price-dispersion overlay (OFF dashed, ON solid; final 50 ticks shaded). Run generated with `run_id=0`, `ncycle=200`. Detailed breakdown: [fig-firm-ab](firm_ab.qmd#fig-firm-ab).](../figs/firm/firm_ab_overlay.png){#fig-ab-overview-firm}

![Bank average-spread overlay (OFF dashed, ON solid; final 50 ticks shaded). Run generated with `run_id=0`, `ncycle=200`. Detailed breakdown: [fig-bank-ab](bank_ab.qmd#fig-bank-ab).](../figs/bank/bank_ab_overlay.png){#fig-ab-overview-bank}

![Wage dispersion overlay (OFF dashed, ON solid; final 50 ticks shaded). Run generated with `run_id=0`, `ncycle=200`. Detailed breakdown: [fig-wage-ab](wage_ab.qmd#fig-wage-ab).](../figs/wage/wage_ab_overlay.png){#fig-ab-overview-wage}
:::

## Detailed pages
For tables, counter snippets, and notes, consult the individual A/B write-ups:

- [Firm A/B comparison](firm_ab.qmd)
- [Bank A/B comparison](bank_ab.qmd)
- [Wage A/B comparison](wage_ab.qmd)

Each page includes the core metrics tables (`tbl-firm-ab`, `tbl-bank-ab`, `tbl-wage-ab`) and reiterates the OFF/ON artifact paths documented in `code/timing.py`.
```

## docs/howto_ab.qmd
```markdown
---
title: "How to Reproduce the A/B Overlays"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

# Overview
Follow this checklist whenever you need to regenerate the short-horizon OFF→ON overlays (firm, bank, wage). The process always happens from the repository root and relies on the deterministic Decider stub plus the Python 2 simulation harness.

## Step 1 — Launch the Decider stub
Run the stub in its own terminal so the simulation can retrieve deterministic responses. Leave the process running until the OFF/ON run completes.

```bash
python3 tools/decider/server.py --stub
```

- Health check (optional): `curl http://127.0.0.1:8000/healthz` → `{ "status": "ok" }`.
- Stop the stub with `Ctrl+C` after you finish rendering the docs.

## Step 2 — Call the A/B runner
Open a second terminal and invoke `run_ab_demo` via Python 2. The helper returns a manifest with the OFF/ON artifact paths and appends the toggle snapshot plus counter lines to `timing.log`.

```bash
python2 - <<'PY'
from pprint import pprint
from code.timing import run_ab_demo

result = run_ab_demo(run_id=0, mode='ab')
print("OFF artifacts:")
pprint(result['off']['artifacts'])
print("ON artifacts:")
pprint(result['on']['artifacts'])
print("Counters appended to timing.log at:", result['meta']['timing_log'])
PY
```

Tips:

- Set `Parameter.ncycle = 200` (or pass `ncycle=200`) to match the short-horizon overlays if you override defaults.
- Use `parameter_overrides={'firm_guard_preset': 'tight'}` (or similar) when testing guard presets; the helper applies overrides to both runs unless you move them into `llm_overrides`.

## Step 3 — Render the documentation
Once the artifacts land under `artifacts/ab_demo/run_<seed>/`, rebuild the Quarto site so the overlay pages embed the refreshed PNGs and tables.

```bash
quarto render docs
```

- `docs/_site/ab_overview.html` aggregates the three overlays.
- The block pages (`firm_ab.qmd`, `bank_ab.qmd`, `wage_ab.qmd`) pull their tables from the CSV outputs listed in the `run_ab_demo` return value.

## Cleanup checklist
- Stop the Decider stub (`Ctrl+C`).
- (Optional) Remove temporary artifacts once you have copied the CSV/PNG files into `data/` and `figs/` for manuscript use.
- Keep `timing.log` out of version control; regenerate it for each run if you need fresh counter evidence.
```

## docs/index.qmd (Milestone M6 section)
```markdown
## Milestone M6 — A/B runner & overlays

- [A/B overlay overview](ab_overview.qmd) — collects the firm, bank, and wage overlays (OFF dashed, ON solid, final 50 ticks shaded) produced from the `run_id=0`, `ncycle=200` runs.
- [How to reproduce A/B overlays](howto_ab.qmd) — three-step checklist (stub, `run_ab_demo`, Quarto render) for regenerating the OFF→ON artifacts.
```

# Verification Checklist for Sign-off
1. Open the rendered overview (`docs/_site/ab_overview.html`). Confirm each caption states `run_id=0`, `ncycle=200`, references the correct figure IDs, and that the three overlays render (use the SHA256 hashes above if you need to confirm integrity).
2. Open the rendered how-to page (`docs/_site/howto_ab.html`). Confirm the three steps are present (stub launch, Python 2 `run_ab_demo`, Quarto render) plus tips and cleanup notes.
3. Open the landing page (`docs/_site/index.html`) and scroll to “Milestone M6 — A/B runner & overlays”. Confirm both links resolve.
4. (Optional) Run a smoke test by following Step 2 in the how-to, overriding `ncycle=20`, and verifying `timing.log` appends the toggle snapshot; no repository modifications required for sign-off.

# Recent Quarto Render (abridged)
```
quarto render docs
[ 1/32] ab_overview.qmd
[ 2/32] bank_ab.qmd
...
[32/32] wage_ab.qmd
Output created: _site/index.html
```

# Suggested Sign-off Comment Template
```
M6 ✅ — A/B overlays and repro checklist approved.

- Overview: docs/_site/ab_overview.html (firm/bank/wage overlays share run_id=0, ncycle=200; captions reference fig-firm-ab / fig-bank-ab / fig-wage-ab).
- How-to: docs/_site/howto_ab.html (stub → python2 run_ab_demo → quarto render docs + cleanup tips).
- Landing page links updated under Milestone M6.

No blockers remaining; proceed to downstream milestones.
```
