---
title: "Equation Map - LLM Hook Anchors"
format:
  html:
    toc: false
---

This quick-reference page ties the Caiani equation numbers to the exact Python call sites we modify with LLM hooks. Each anchor points at a code comment that begins with `Eq.` so you can jump straight to the baseline heuristic before layering in LLM behavior.

| Equation | Behavioral rule | Code anchor | Notes |
| --- | --- | --- | --- |
| Eq. 1 | Worker reservation wage | `code/consumer.py` -> `Consumer.laborSupply` (`# Eq. 1 ...`) | Reservation wage clamp + direction choice prior to any LLM override. |
| Eq. 12-14 | Firm pricing & expectations | `code/firm.py` -> `Firm.learning` (`# Eq. 12-14 ...`) | Calls `Mind.alphaParameterSmooth16` to update price/expected demand. |
| Eq. 15 | Firm offered wage | `code/firm.py` -> `Firm.wageOffered` (`# Eq. 15 ...`) | Baseline wage offer before bargaining and upcoming LLM guardrails. |
| Eq. 26 | Loan approval probability | `code/bank.py` -> `Bank.computeProbProvidingLoan` (`# Eq. 26 ...`) | Maps leverage/phi signal to approval odds; upstream of `matchingCredit.matchCreditOpen`. |
| Eq. 27 | Loan spread setting | `code/bank.py` -> `Bank.computeInterestRate` (`# Eq. 27 ...`) | Linear leverage-to-spread rule feeding the credit match. |

For more context on how the manuscript cites these anchors, see `docs/appendix_eq_map.qmd` once the appendix draft lands.
