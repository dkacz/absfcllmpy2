---
title: "Writer Brief — Issue #53 (M6-06)"
description: "Integrate the firm/bank/wage A/B overlays into the Results section (short-horizon OFF→ON comparison). Full context and artifacts inlined; no repo access needed."
format:
  html:
    toc: true
    toc-depth: 2
---

# 1. Goal & Deliverable
- **Objective:** draft the Results copy that narrates the **short-horizon A/B overlays** (firm pricing, bank credit, wage bargaining) for Milestone **M6-06**. This text will slot into `docs/main.qmd` under **Results → A/B Overlays** once Issue #69 opens the placeholder.
- **Deliverable:** ~3 tightly written paragraphs (one per block) plus a linking sentence/mini-intro so the manuscript can reference the figures/tables already embedded in the A/B pages.
- **Tone:** empirical lab-note voice – describe what the overlays show (or fail to show) without overselling; flag that firm/bank runs remain identical under the deterministic stub.

# 2. Run Configuration (shared across overlays)
- Seed/run ID: `run_id = 0`
- Horizon: `ncycle = 200` (short-horizon smoke tier, per M6 scope)
- Decider mode: **stub**, deterministic response (Temperature = 0)
- Guardrails: baseline preset (price/wage step caps 0.04, expectation bias cap 0.04, unit-cost floor, spread clamps)
- Hooks enabled in ON leg: all three (firm pricing, bank credit, wage worker+offer) but stub replies keep decisions at the baseline heuristics unless a guard clamps the value.
- Artifact directories: generated via `python3 tools/generate_<block>_ab.py`; Quarto render confirmed (`quarto render docs`).

# 3. Figures & Tables to cite
Use the precise identifiers so cross-references remain stable.

| Block | Metrics table | Overlay figure | CSV | PNG |
| --- | --- | --- | --- | --- |
| Firm pricing & expectations | `Table @tbl-firm-ab` | `Figure @fig-firm-ab` | `data/firm/firm_ab_table.csv` | `figs/firm/firm_ab_overlay.png` |
| Bank credit & spreads | `Table @tbl-bank-ab` | `Figure @fig-bank-ab` | `data/bank/bank_ab_table.csv` | `figs/bank/bank_ab_overlay.png` |
| Wage bargaining | `Table @tbl-wage-ab` | `Figure @fig-wage-ab` | `data/wage/wage_ab_table.csv` | `figs/wage/wage_ab_overlay.png` |

Overlay styling (common): ON = **solid** line, OFF = **dashed** line, final 50 ticks shaded (grey band).

# 4. Block-specific data snapshots
## 4.1 Firm A/B metrics (Table @tbl-firm-ab)
```
scenario,metric,value
llm_on,inflation_volatility,0.0061805681026881705
llm_on,price_dispersion,0.20957101039825526
baseline,inflation_volatility,0.0061805681026881705
baseline,price_dispersion,0.20957101039825526
```
- Overlay PNG (`figs/firm/firm_ab_overlay.png`, base64 inline for reference):
```
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
```
- **Observation:** firm OFF vs ON metrics are identical (stub rejects every firm request), so the overlay collapses to a single trajectory. Mention that future live prompts should introduce divergence.

## 4.2 Bank A/B metrics (Table @tbl-bank-ab)
```
scenario,metric,value
llm_on,avg_spread,0.00889359407949925
llm_on,loan_output_ratio,1.287783914482426
llm_on,credit_growth,19012.88896143385
baseline,avg_spread,0.00889359407949925
baseline,loan_output_ratio,1.287783914482426
baseline,credit_growth,19012.88896143385
```
- Overlay PNG (`figs/bank/bank_ab_overlay.png`, base64 inline):
```
iVBORw0KGgoAAAANSUhEUgAABIAAAAKICAYAAAAIK4ENAAAAOnRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjEwLjMsIGh0dHBzOi8vbWF0cGxvdGxpYi5vcmcvZiW1igAAAAlwSFlzAAAWJQAAFiUBSVIk8AABAABJREFUeJzs3Xd0FFUbBvBndtN7B1JIAQKhIxBCDx2RqqigUkRARWlWQKQpWJGiolgoogKCEpr0TiD0IC0EQhJqCOm97v3+yLeTLLtJNh2W53cOh5079955Z2d3s/PunTuSEEKAiIiIiIiIiIgMlqKmAyAiIiIiIiIioqrFBBARERERERERkYFjAoiIiIiIiIiIyMAxAUREREREREREZOCYACIiIiIiIiIiMnBMABERERERERERGTgmgIiIiIiIiIiIDBwTQEREREREREREBo4JICIiIiIiIiIiA8cEEBERERERERGRgWMCiIiIiIiIiIjIwDEBRERERERERERk4JgAIiIiIiIiIiIycEwAERERERERERERk4JoCIiIiIiIiIiIDBwTQEREREREREREBo4JICIiIiIiIiIiA8cEEBERERERERGRgWMCiIiIiIiIiIjIwDEBRERERERERERk4JgAIiIiIiIiIiIycEwAERERERERERERk4JoCIiB4Rc+bMgSRJGD16dE2HQvRIGz16NCRJwpw5c2o6FHoEBQYGQpIkrFq1qqZDKZOPPvoIkiRh5cqVNR0KGYDKfh9IkgRJkhAVFVUp/RWnd+/eUCqVuHDhQpVuh+hJxQQQERkc9cnhw/+USiUcHBzQqVMnfPPNN8jMzKzpUInIgEyZMkX+vJk/f36Z2qpUKjg7O0OpVCIuLg4AsGrVKp2fZQqFAtbW1mjRogXee+893Llzpyp2h6rRvXv3sHjxYnh5eWHEiBE1HU6VyMnJwZdffomWLVvCysoKdnZ2aN++PX766ScIIapkm2FhYViwYAF69+4NV1dXmJiYwNbWFv7+/pg/fz6SkpJK7SMlJQUzZ86En58fLCws4OjoiB49emDjxo16xbBhwwZ0794djo6OsLCwgJ+fH2bOnInU1NRy7VNUVBTmzJmDxYsXl6v9o+6jjz6CSqXC9OnTazoUIoPEBBARGSxjY2PUqlVL/mdtbY3ExEQEBwfj3XffRZs2bfDgwYOaDpOIDEBubi7+/PNPefm3334rU/vjx48jLi4OAQEBcHJy0lpf9LPM0dER6enp+O+//7Bw4UI0btwYx48fr/A+UM2ZN28eMjIy8OGHH8LIyKimw6l0KSkp6NChAz788EOcP38eQghkZmYiJCQEr7/+OgYOHIi8vLxK3WZwcDD8/Pzw0UcfYc+ePYiJiYGlpSXS0tJw6tQpzJw5E82aNcPFixeL7eP27dto2bIl5s+fj7CwMCiVSqSkpGD//v14/vnnMWHChBJjGD9+PF544QUcOHAAKSkpUCqVCAsLw/z589GyZUvcvXu3zPsVFRWFuXPnlpoAqlu3Lho2bAhbW9syb6Mmde3aFZ06dcL27dtx9OjRmg6HyOAwAUREBqtDhw6IiYmR/yUlJSEpKQlff/01FAoFLl++jGnTptV0mERkAHbs2IEHDx6ga9eu8PX1RXh4OEJCQvRuv23bNgBA//79da4v+ln24MEDZGVl4Z9//oGLiwtSUlIwYsSIKhtFQVUrMTERr1tufw==
```
- **Observation:** bank OFF vs ON metrics are identical (stub returns deterministic fallbacks). Highlight that the overlay serves as a visual baseline; real divergence awaits live OpenRouter prompts.

## 4.3 Wage A/B metrics (Table @tbl-wage-ab)
```
scenario,metric,value
llm_on,wage_dispersion,0.0021183807187412796
llm_on,fill_rate,0.5501397177771765
baseline,wage_dispersion,0.1441582030704589
baseline,fill_rate,0.3501829294414104
```
- Overlay PNG (`figs/wage/wage_ab_overlay.png`, base64 inline):
```
iVBORw0KGgoAAAANSUhEUgAABIAAAAKICAYAAAAIK4ENAAAAOnRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjEwLjMsIGh0dHBzOi8vbWF0cGxvdGxpYi5vcmcvZiW1igAAAAlwSFlzAAAWJQAAFiUBSVIk8AAA5pNJREFUeJzs3Xd4U9X/B/B30nTvXUrpYFP2FMoGGQoIAiKIAiIgP9mICsoUURQRBEER2SpflD0UCtIyyp6yyi6rtKV7t0lzfn9gLg1N27S0SZu+X8/DQ+495577ublJ2nx6hkwIIUBERERERERERCZLbuwAiIiIiIiIiIiodDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNAREREREREREQmjgkgIiIiIiIiIiITxwQQEREREREREZGJYwKIiIiIiIiIiMjEMQFERERERERERGTimAAiIiIiIiIiIjJxTAARERERERERERk4JoCIiIiIiIiIiEwcE0BERERERERERCaOCSAiIiIiIiIiIhPHBBARERERERERkYljAoiIiIiIiIiIyMQxAUREREREREREZOKYACIiIiIiIiIiMnFMABERERERERERmTgmgIiIiIiIiIiITBwTQEREREREREREJo4JICIiIiIiIiIiE8cEEBERERERERGQiWMCiIiIiIiIiIjIxDEBRERERERERERk4pgAIiIiIiIiIiIycUwAERERERERERGZOCaAiIiIiIiIiIhMHBNARERERERER
```
- **Observation:** wage ON leg collapses wage dispersion and lifts vacancy fill rate despite the stub, because guard clamping enforces zero movement in ON while the baseline continues its adaptive drift. This is the only block showing an OFF/ON delta today – emphasize that guards + stub produce a conservative ON path.

# 5. Blueprint & Manuscript Context
- **Blueprint references:**
  - Guard defaults and overlay styling (§ "Presentation & guard defaults" in `docs/blueprint.md`).
  - Research questions RQ1–RQ3 (pricing, credit, wages) — tie each paragraph back to the relevant RQ.
- **Manuscript spine (`docs/main.qmd`):** Results section currently hosts baseline metrics and HSC notes; your copy will populate the forthcoming “A/B Overlays” subsection (mentioned in the JSON comment but not yet drafted). Structure recommendation:
  1. Short lead linking to the shared run settings (200 ticks, stub, ON solid/OFF dashed, same seed).
  2. Firm paragraph: note identical OFF/ON lines; interpret as “stub parity baseline” and flag expectation of divergence once live prompts integrate.
  3. Bank paragraph: identical overlay; reiterate baseline expectation (no soft information yet).
  4. Wage paragraph: highlight the observed divergence (fill-rate up, dispersion down) driven by guard clamps vs baseline inertia; caution that this is a guard artifact, not a learned heuristic yet.
  5. Closing sentence teeing up the reader for future live-mode results (Milestone M6-LIVE) where prompts will diverge.
- **Citations:** use inline cross-refs when mentioning figures/tables (e.g., “see Figure @fig-wage-ab”).

# 6. Constraints & Style Notes
- Do **not** introduce new data or claim live-learning effects; current ON results are stub driven.
- Keep paragraphs tight (4–5 sentences). Focus on what the figure/table shows, why (deterministic stub + guards), and what readers should watch for in upcoming live runs.
- Mention the guardrails explicitly in at least one paragraph so readers know ON isn’t free-form.
- Optional: remind readers the short horizon here (200 ticks) differs from the 240-tick manuscript baseline adopted post-HSC.

# 7. Submission Checklist
- [ ] Provide the narrative text (intro + 3 block paragraphs + outro) ready to paste into `docs/main.qmd`.
- [ ] Reference the correct figure/table IDs.
- [ ] Call out the equality in firm/bank overlays and the lone wage divergence.
- [ ] Include a note that future live prompts (M6-LIVE) will revisit these overlays.

Once drafted, hand the copy back via Issue #53. No repo changes required from the writer.
