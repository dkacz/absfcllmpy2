---
title: "Model Overview"
description: "A non-technical summary of the Caiani AB-SFC model structure, agents, markets, and the integration of live LLM decisions as instrumented in this repository."
format:
  html:
    toc: true
    toc-depth: 3
---

# Model Overview {#methods-model-overview}

This page provides a high-level overview of the Agent-Based Stock-Flow Consistent (AB-SFC) macroeconomic model used in this project, originally developed by Caiani et al. (2017), and adapted here to incorporate live Large Language Model (LLM) behavioral hooks.

::: {.callout-important}
## Scope Disclaimer
This repository treats the existing Python 2 codebase as a sandbox for a **methods contribution**. The parameters and simulation outcomes differ from the original Caiani calibration; we do not attempt to replicate the original paper’s results. The focus is on demonstrating a pattern for safely integrating live LLM decisions.
:::

## The Baseline AB-SFC Framework {#sec-overview-baseline}

The model simulates a monetary union composed of multiple countries (five in the default configuration). It is characterized by decentralized interactions among heterogeneous agents, imperfect information, and adaptive behavior.

### Agents and Markets {#sec-overview-agents}

The simulation includes several classes of agents:

- **Households/Workers:** Supply labor, consume goods, and hold equity. They set reservation wages and search for employment.
- **Firms:** Produce goods (tradable or non-tradable), hire workers, set prices, form expectations, and invest in R&D to improve productivity.
- **Banks:** Accept deposits and provide credit to firms. They evaluate loan applications, set credit limits, and determine interest rate spreads based on borrower leverage.
- **Government Sector:** Collects taxes and provides public spending (lump-sum transfers) within each country, adhering to deficit-to-GDP ratio targets.
- **Central Banks:** A Union Central Bank sets the policy rate (using a Taylor rule), while National Central Banks provide liquidity to commercial banks and absorb residual government bonds.

These agents interact across several markets:

- **Consumption Goods Market:** Uses a Hotelling matching protocol, where consumers balance price and product variety when choosing suppliers.
- **Labor Market:** Decentralized matching where firms offer wages and workers accept based on their reservation wages. Bargaining power is influenced by the aggregate unemployment rate.
- **Credit Market:** Firms seek loans to finance production and R&D. Banks may ration credit based on balance sheet constraints and applicant risk.
- **Bond and Deposit Markets:** Manage savings and government financing.

### Accounting and Consistency

A core feature of the model is its adherence to **Stock-Flow Consistency (SFC)**. Every financial flow comes from somewhere and goes somewhere, and all stocks (assets and liabilities) are rigorously tracked via ledgers (`lebalance.py`). This ensures that the macroeconomic accounting is sound and prevents "black holes" where money disappears or appears arbitrarily.

## Simulation Loop and Timing {#sec-overview-timing}

The simulation proceeds in discrete time steps (ticks). The order of operations within each tick is crucial for causality and consistency:

1. **Bargaining and Expectations:** Labor market bargaining begins (`maLaborCapital.bargaining()`). Firms update their expectations, set prices (`firm.learning()`), and determine desired production levels (`firm.productionDesired()`).
2. **Credit Market:** Firms request loans, and banks evaluate applications and set terms (`maCredit.creditNetworkEvolution()`).
3. **Production and Sales:** Firms hire workers (`maLaborCapital.working()`) and produce goods, followed by interactions on the consumption market (`firm.effectiveSelling()`).
4. **Income and Policy:** Households receive income (`consumer.income()`); governments calculate taxes, set spending, and issue bonds (`etat.expectingTaxation()`, `poli.implementingPolicy()`).
5. **Innovation and Dynamics:** R&D outcomes and technological spillovers occur (`gloInnovation.spillover()`). Firms and banks may exit if insolvent, and new agents may enter (`firm.existence()`).
6. **Aggregation and Monetary Policy:** Macroeconomic aggregates are computed, consistency checks are performed (e.g., `aggrega.checkNetWorth()`), and the Union Central Bank updates the policy rate (`centralBankUnion.taylorRule1()`).

## Live LLM Integration {#sec-overview-llm}

This project modifies the baseline model by interposing live LLM decisions at specific behavioral functions within the simulation loop. The LLM acts as a microservice (the "Decider") that provides qualitative cues based on local agent states.

### LLM Hooks

The LLM influences decisions in three key areas during steps 1 and 2 of the simulation loop:

1. **Firm Pricing and Expectations (Eq. 12–14):** Determining the direction (up/down/hold) and step size for price adjustments and expectation biases.
2. **Bank Credit Decisions (Eq. 26–27):** Influencing loan approval, setting credit limits, and determining the interest rate spread (in basis points).
3. **Wage Setting (Eq. 1, 15):** Determining the direction and step size for worker reservation wages and firm offered wages.

### Safety and Workflow

The integration is designed with strict safety protocols to preserve the model's SFC properties and ensure stability. The Python 2 simulation communicates with the Python 3 Decider service via HTTP.

- **Guards and Bounds:** All LLM-suggested values are strictly bounded in the Python 2 client *before* state updates. This includes caps on price/wage steps (default 0.04), expectation bias caps (0.04), enforcing a unit-cost price floor (`p ≥ w/φ`), spread clamps, and leverage monotonicity checks.
- **Timeouts and Fallbacks:** Hard timeouts are enforced. If the LLM fails to respond, returns invalid JSON, or suggests values outside the acceptable bounds, the system immediately reverts to the baseline numeric heuristics.

## Where to Look Next {#sec-overview-next}

For more detailed information on the implementation, refer to the following Methods pages:

- [**Decider Stub**](decider.md): Details on the LLM microservice design, API schema, and configuration.
- [**Py2 Client**](py2_client.md): Description of the Python 2 HTTP client contract and error handling.
- [**Fallback Semantics**](fallbacks.qmd): A deep dive into the fallback pipeline, guardrails, and logging mechanisms.
- @ref(methods-variables): Precise definitions and computation details for all core metrics used in the manuscript.
