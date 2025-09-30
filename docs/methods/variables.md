---
title: "Variable Dictionary"
description: "A concise dictionary mapping manuscript metrics to their source CSV columns, detailing their computation, inputs, and context within the AB-SFC model."
format:
  html:
    toc: true
    toc-depth: 3
---

# Variable Dictionary {#methods-variables}

This document defines the core metrics used to evaluate simulation outcomes in the manuscript. It details how each metric is computed within the simulation (`code/aggregator.py`) and identifies the corresponding columns in the output datasets.

## Data Sources and Computation {#sec-variables-sources}

The metrics described here are derived from the simulation output. The primary artifact for analysis is:

- **Canonical Baseline Data:** `data/core_metrics.csv`. This file contains scalar metrics computed over the full 240-tick horizon for baseline (LLM OFF) and LLM-enhanced (LLM ON) scenarios.

  ```csv
  # Sample from data/core_metrics.csv
  scenario,metric,value
  llm_on,price_dispersion,0.16932996561384545
  baseline,price_dispersion,0.16932996561384545
  ...
  ```

Metrics are computed in two stages by the aggregator:

1. **Tick-level Series Construction:** Intermediate variables are calculated at each time step based on the aggregate state of agents.
2. **Aggregation into Scalars:** The time series are aggregated (e.g., averaged or standard deviation calculated) over the simulation horizon to produce the final scalar metrics. Standard statistical definitions (mean and standard deviation) are used, with appropriate guardrails implemented.

::: {.callout-tip}
## Using the Preview Bundle
For quick previews and validation, a 20-tick baseline run (LLM hooks disabled) is available in the `docs/stubs/` directory. This bundle includes:

- `docs/stubs/micro_run_core_metrics.csv`: Scalar metrics for the 20-tick run.
- `docs/stubs/micro_run_metric_series.csv`: Tick-level time series data used to compute the scalars.

These files can be used to trace the computations described below.
:::

## Metric Definitions {#sec-variables-definitions}

The following sections detail the metrics organized by macroeconomic domain. In the source CSV files, metrics are identified by the `metric` column, and their final scalar value is in the `value` column.

### Price Dynamics (Inflation and Dispersion) {#sec-variables-price}

These metrics capture the stability and heterogeneity of prices across the monetary union, driven by firm pricing decisions (LLM-augmented via Eq. 12–14).

| Metric | Source CSV Column | Computation | Notes/Agents |
| :--- | :--- | :--- | :--- |
| **`inflation_volatility`** | `value` where `metric == "inflation_volatility"` | Standard deviation across ticks of the country-average inflation rate. <br><br> 1. **Tick-level:** Compute average inflation across all countries: `avg_inflation = sum(McountryInflation) / len(Lcountry)`. <br> 2. **Scalar:** Compute the standard deviation of the `avg_inflation` time series (`std(series['inflation'])`). <br><br> **Guardrails:** Standard deviation calculation includes a zero guard on variance (`math.sqrt(max(variance, 0.0))`) to ensure a real result. | Inputs supplied by **Firms** (pricing decisions) aggregated at the country level. Captures the temporal stability of the overall price level. |
| **`price_dispersion`** | `value` where `metric == "price_dispersion"` | Time-average of the sales-weighted price dispersion across all firms. <br><br> 1. **Tick-level:** Compute the sales-weighted variance of prices across firms; take the square root to obtain dispersion. <br> 2. **Scalar:** Compute the mean of the `price_dispersion` time series (`mean(series['price_dispersion'])`). <br><br> **Guardrails:** Variance calculation includes a zero guard (`math.sqrt(max(variance_price, 0.0))`) to handle floating-point noise. | Inputs supplied by **Firms** (prices and sales volumes). Measures the cross-sectional heterogeneity of prices, reflecting competition and market structure. |

### Labor Market (Wages and Employment) {#sec-variables-labor}

These metrics assess labor-market outcomes, focusing on wage heterogeneity and the efficiency of matching between workers and firms (LLM-augmented via Eq. 1 and 15).

| Metric | Source CSV Column | Computation | Notes/Agents |
| :--- | :--- | :--- | :--- |
| **`wage_dispersion`** | `value` where `metric == "wage_dispersion"` | Time-average of the employment-weighted wage dispersion. <br><br> 1. **Tick-level:** Compute the employment-weighted variance of wages; take the square root. <br> 2. **Scalar:** Compute the mean of the `wage_dispersion` time series (`mean(series['wage_dispersion'])`). <br><br> **Guardrails:** Variance calculation includes a zero guard (`math.sqrt(max(variance_wage, 0.0))`). | Inputs supplied by **Firms** (offered wages) and **Workers** (reservation wages) during matching. Measures cross-sectional wage heterogeneity. |
| **`fill_rate`** | `value` where `metric == "fill_rate"` | Time-average of the vacancy fill rate. <br><br> 1. **Tick-level:** Ratio of total employed labor to total desired labor: `fill_employed_total / float(fill_desired_total)`. Defaults to 1.0 if desired labor is zero. <br> 2. **Scalar:** Compute the mean of the `fill_rate` time series (`mean(series['fill_rate'])`). <br><br> **Guardrails:** Tick-level rate defaults to 1.0 when demand is zero; the scalar mean defaults to 1.0 if the series is empty. | Inputs supplied by **Firms** (desired labor demand) and the matching outcome from `maLaborCapital`. Indicates how effectively vacancies are filled. |

### Credit and Finance {#sec-variables-credit}

These metrics track the cost and intensity of credit within the economy, driven by bank lending decisions (LLM-augmented via Eq. 26–27).

| Metric | Source CSV Column | Computation | Notes/Agents |
| :--- | :--- | :--- | :--- |
| **`avg_spread`** | `value` where `metric == "avg_spread"` | Time-average of the loan-volume-weighted interest rate spread. <br><br> 1. **Tick-level:** Weighted average spread charged by banks over the policy rate: `spread_weighted_sum / float(spread_loan_sum)`. Defaults to 0.0 if no loans are granted. <br> 2. **Scalar:** Compute the mean of the `avg_spread` time series (`mean(series['avg_spread'])`). | Inputs supplied by **Banks** (spread setting) and loan volumes during credit-market matching. Reflects perceived credit risk and borrowing costs. |
| **`loan_output_ratio`** | `value` where `metric == "loan_output_ratio"` | Time-average of the ratio of total credit stock to total output. <br><br> 1. **Tick-level:** Ratio of total outstanding credit to aggregate output: `credit_total / float(total_output)`. Defaults to 0.0 if output is zero. <br> 2. **Scalar:** Compute the mean of the `loan_output_ratio` time series (`mean(series['loan_output_ratio'])`). | Inputs derived from **Banks** (credit totals) and **Firms** (aggregate output). Measures the economy’s financial leverage. |

## Reference Implementation Snippet {#sec-variables-snippet}

```python
# code/aggregator.py (abbreviated for reference)
self._metric_series = {
    'inflation': [],
    'price_dispersion': [],
    'total_credit': [],
    'avg_spread': [],
    'wage_dispersion': [],
    'fill_rate': [],
    'loan_output_ratio': [],
}

avg_inflation = sum(self.McountryInflation[c] for c in self.Lcountry) / len(self.Lcountry)
self._metric_series['inflation'].append(avg_inflation)

mean_price = price_sum_total / price_weight_total
variance_price = price_sq_sum_total / price_weight_total - (mean_price ** 2)
price_dispersion = math.sqrt(max(variance_price, 0.0))
self._metric_series['price_dispersion'].append(price_dispersion)

mean_wage = wage_sum_total / wage_weight_total
variance_wage = wage_sq_sum_total / wage_weight_total - (mean_wage ** 2)
wage_dispersion = math.sqrt(max(variance_wage, 0.0))
self._metric_series['wage_dispersion'].append(wage_dispersion)

fill_rate_value = 1.0
if fill_desired_total > 0:
    fill_rate_value = fill_employed_total / float(fill_desired_total)
self._metric_series['fill_rate'].append(fill_rate_value)

self._metric_series['total_credit'].append(credit_total)
total_output = totalY
if total_output > 0:
    ratio = credit_total / float(total_output)
else:
    ratio = 0.0
self._metric_series['loan_output_ratio'].append(ratio)

avg_spread = spread_weighted_sum / float(spread_loan_sum) if spread_loan_sum > 0 else 0.0
self._metric_series['avg_spread'].append(avg_spread)

core_metrics = {
    'inflation_volatility': std(self._metric_series['inflation']),
    'price_dispersion': mean(self._metric_series['price_dispersion']),
    'avg_spread': mean(self._metric_series['avg_spread']),
    'loan_output_ratio': mean(self._metric_series['loan_output_ratio']),
    'wage_dispersion': mean(self._metric_series['wage_dispersion']),
    'fill_rate': mean(self._metric_series['fill_rate'], default=1.0),
}
```

Use the snippet above to cross-check the definitions in the table. Each metric in `data/core_metrics.csv` corresponds directly to the time-aggregated series captured by `self._metric_series`.
