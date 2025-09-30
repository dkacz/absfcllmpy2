---
title: "Writer Brief — Issue #30 (M3-07)"
description: "Context packet for the firm LLM methods snippet (300–500 words)."
format:
  html:
    toc: true
    toc-depth: 2
---

# Assignment
- **Milestone:** M3 — Firm Pricing & Expectations (eqs. 12–14)
- **Issue:** #30 (role: writer)
- **Deliverable:** 300–500 word prose block for the Methods section describing the *live* firm pricing & expectations hook. The prose will drop into the manuscript’s Methods chapter (ultimately referenced from `docs/main.qmd`).
- **Audience:** research readers; assume familiarity with Caiani AB‑SFC baseline.
- **Voice:** formal, methods-focused, with citations to in-repo figures/tables where relevant (`@tbl-firm-ab`, `@fig-firm-ab`).

# Story beats to cover
1. **Legacy baseline** – remind the reader what eqs. 12–14 do in the original Caiani code (Pricing: adjust via backlog/markup; Expectations: update `xE`).
2. **Hook pathway** – Python 2 simulation → `code/firm.py` → payload (feature pack + guard caps) → Python 3 Decider.
3. **Guardrails & fallbacks** – price step cap 0.04, expectation bias cap 0.04, price floor (`p ≥ w/φ`), min markup, baseline fallback triggers (`firm_enabled`, `_apply_baseline`). Reference the simple JSON contract `(decision, error)` from `code/llm_bridge_client.py`.
4. **Runtime instrumentation** – counters (`log_llm_call`, fallbacks logged) + `timing.log` snapshots (see example below).
5. **Artifacts for manuscript** – mention the OFF/ON overlay + table (`docs/firm_ab.qmd`, `data/firm/firm_ab_table.csv`, `figs/firm/firm_ab_overlay.png`). Explain why OFF and ON presently coincide (Decider stub rejects requests; live prompts forthcoming).
6. **Future live mode** – summarize architect’s spec (OpenRouter adapter, JSON schema prompts, fallback ladder). Make clear that current implementation still uses the stub but infrastructure is ready.

# Key artifacts & excerpts
## Firm Quarto page (results)
```markdown
---
title: "Firm A/B Comparison"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

# Overview
This page tracks the firm pricing & expectations experiment for Milestone M3. Both runs use `run_id = 0` over a 200-tick horizon with the Decider stub responding deterministically. The CSV and overlay below are generated via `python3 tools/generate_firm_ab.py` and surface the raw metrics exported by `code/timing.py`.

Because the stub currently rejects every firm request, the OFF and ON scenarios are identical. We keep the artifacts in place so later prompt work can drop in updated values without changing the page structure.

## Core metrics
The table aggregates inflation volatility and price dispersion for the baseline (`OFF`) and LLM-enabled (`ON`) runs. Values are rounded to two decimals per the manuscript convention.

```{python}
#| label: tbl-firm-ab
#| tbl-cap: "Firm A/B metrics (run 0, 200 ticks)."
import pandas as pd
from pathlib import Path

source = Path("../data/firm/firm_ab_table.csv")
df = pd.read_csv(source)
ordered = (
    df.pivot(index="scenario", columns="metric", values="value")
      .reindex(["baseline", "llm_on"])
      [["inflation_volatility", "price_dispersion"]]
      .rename(columns={
          "inflation_volatility": "Inflation volatility",
          "price_dispersion": "Price dispersion",
      })
)
formatted = ordered.applymap(lambda x: f"{x:,.2f}")
formatted
```

## Price-dispersion overlay
Figure @fig-firm-ab overlays the OFF and ON time series. The OFF path is dashed, the ON path is solid, and the final 50 ticks are shaded to highlight the comparison window used in the manuscript.

![Firm price dispersion overlay (OFF dashed, ON solid; final 50 ticks shaded)](../figs/firm/firm_ab_overlay.png){#fig-firm-ab}

## Notes
- Artifact paths: `data/firm/firm_ab_table.csv`, `figs/firm/firm_ab_overlay.png`.
- Stub behaviour yields identical OFF/ON metrics; expect differences once live prompts replace the stub.
```

## Guarded application in `code/firm.py`
```python
             new_price=previous_price
          else:
             new_price=baseline_price
          if new_price<price_floor:
             log_fallback('firm','price_floor_enforced')
             new_price=price_floor
          self.price=new_price
          self.mind.pSelling=self.price

          max_bias=max(0.0,float(guard_caps.get('max_expectation_bias',max_step)))
          bias=decision.get('expectation_bias',0.0)
          if bias>max_bias:
             log_fallback('firm','expectation_bias_clamped_high')
             bias=max_bias
          if bias<-max_bias:
             log_fallback('firm','expectation_bias_clamped_low')
             bias=-max_bias
          baseline_expected=baseline.get('expected_demand',0.0)
          target_expected=baseline_expected*(1.0+bias)
          if target_expected<0.0:
             target_expected=0.0
          self.mind.xE=target_expected
          theta=getattr(self.mind,'theta',0.0)
          inventory=self.inventory
          new_producing=target_expected*(1+theta)-inventory
          if new_producing<0.0:
             new_producing=0.0
          self.mind.xProducing=new_producing

      def _unit_cost(self):
          if self.phi==0:
             return 0.0
          return self.w/float(self.phi)

      def _compute_feature_pack(self,previous_price,baseline_price,expected,production_effective):
          inventory=max(0.0,getattr(self,'inventory',0.0))
          offered=getattr(self,'xOfferedEffective',production_effective+inventory)
          offered=max(0.0,offered)
          inv_ratio=0.0
          if expected>0:
             inv_ratio=inventory/expected
          backlog=max(0.0,expected-offered)
          delta_price_comp=baseline_price-previous_price
          last_sales=max(0.0,getattr(self,'xSold',0.0))
          capacity=max(0.0,production_effective)
          liquidity=self._safe_numeric(getattr(self,'ResourceAvailable',0.0))
          if liquidity is None:
             liquidity=self._safe_numeric(getattr(self,'sellingMoney',0.0))
          unit_cost=self._safe_numeric(self._unit_cost())
          inv_ratio=self._safe_numeric(inv_ratio)
          backlog=self._safe_numeric(backlog)
          delta_price_comp=self._safe_numeric(delta_price_comp)
          last_sales=self._safe_numeric(last_sales)
          capacity=self._safe_numeric(capacity)
          sector_code=self._resolve_sector_code()
          numeric_map={
              'unit_cost':unit_cost,
              'inv_ratio':inv_ratio,
              'backlog':backlog,
              'delta_price_comp':delta_price_comp,
              'last_sales':last_sales,
              'capacity':capacity,
              'liquidity':liquidity,
          }
          missing=[label for (label,value) in numeric_map.items() if value is None]
          if sector_code is None:
             missing.append('sector_code')
          if missing:
             return {}, missing
          return {
              'unit_cost':numeric_map['unit_cost'],
              'inv_ratio':numeric_map['inv_ratio'],
              'backlog':numeric_map['backlog'],
              'delta_price_comp':numeric_map['delta_price_comp'],
              'last_sales':numeric_map['last_sales'],
              'capacity':numeric_map['capacity'],
              'liquidity':numeric_map['liquidity'],
              'sector_code':sector_code,
          }, []

      def _resolve_sector_code(self):
          category=getattr(self,'tradable',None)
          if category=='yes':
             return 'tradable'
          if category=='no':
             return 'non_tradable'
          return None

      def _safe_numeric(self,value):
          try:
             numeric=float(value)
          except (TypeError,ValueError):
             return None
          if math.isnan(numeric) or math.isinf(numeric):
             return None
          return numeric

      def changingInventory(self):
          if self.xOfferedEffective>=self.xSold:
             self.pastInventory=self.inventory
```

## Client contract (`code/llm_bridge_client.py` excerpt)
```python
# -*- coding: utf-8 -*-
"""HTTP client for the local Decider service (Python 2).

This module provides a minimal wrapper around ``urllib2`` so the legacy Caiani
simulation (Python 2) can talk to the Python 3 Decider server.  The client
exposes helper methods for the three decision endpoints and surfaces a tuple of
``(response_dict, error_info)`` to the caller.  ``response_dict`` is returned on
HTTP 200 with valid JSON; otherwise ``None`` is returned together with a short
error descriptor that the simulation can log before falling back to the baseline
heuristic.
"""

from __future__ import absolute_import

import json
import logging
import socket
import urllib2

LOGGER = logging.getLogger(__name__)

try:  # Python 2 only
    text_type = unicode  # type: ignore  # noqa: F821 - defined at runtime
except NameError:  # pragma: no cover - Python 3 fallback for tooling
    text_type = str

try:
    bytes_type = bytes
except NameError:  # pragma: no cover - legacy Python fallback
    bytes_type = str

_DECISION_ENDPOINTS = {
    'firm': '/decide/firm',
    'bank': '/decide/bank',
    'wage': '/decide/wage',
}


class LLMBridgeClient(object):
    """Minimal HTTP client for the Decider stub/live service."""

    def __init__(self, base_url, timeout=0.2, headers=None):
        if not base_url:
            raise ValueError('base_url is required')
        # Normalise whitespace and trailing slashes so path joins are predictable.
        base_url = base_url.strip()
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.timeout = float(timeout) if timeout is not None else None
        self.headers = {'Content-Type': 'application/json'}
        if headers:
            self.headers.update(headers)

    def decide_firm(self, payload):
        """Call the firm endpoint.

        Returns ``(response_dict, error_info)``.
        """

        return self._post_json(_DECISION_ENDPOINTS['firm'], payload)

    def decide_bank(self, payload):
        """Call the bank endpoint (loan approval & spread)."""

        return self._post_json(_DECISION_ENDPOINTS['bank'], payload)

    def decide_wage(self, payload):
        """Call the wage endpoint (worker reservation / firm offer)."""

        return self._post_json(_DECISION_ENDPOINTS['wage'], payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post_json(self, path, payload):
        """POST ``payload`` (dict) to ``path`` and return ``(data, error)``.

        ``data`` is a Python object parsed from JSON when the response is 200
        and well-formed.  Otherwise ``None`` is returned along with ``error``, a
        dict containing at least a ``reason`` key.  The caller can log this and
        fall back to the baseline decision logic.
        """

        if not isinstance(payload, dict):
            raise TypeError('payload must be a dict (got %r)' % type(payload))

        url = self._build_url(path)
        data = json.dumps(payload)
        request = urllib2.Request(url, data=data, headers=self.headers)

        try:
            response = urllib2.urlopen(request, timeout=self.timeout)
        except urllib2.HTTPError as exc:
            error_body = exc.read()
            parsed = self._safe_json(error_body)
            return None, {
                'reason': 'http_error',
                'status': exc.code,
                'body': parsed,
            }
        except urllib2.URLError as exc:
            # ``URLError`` wraps a variety of socket issues.  Timeouts may be
            # surfaced either as ``socket.timeout`` or via ``str(reason)``.
            if isinstance(exc.reason, socket.timeout):
                return None, self._timeout_error(url)
            return None, {
                'reason': 'connection_error',
                'detail': str(exc.reason),
            }
        except socket.timeout:
            return None, self._timeout_error(url)
        except Exception as exc:  # pragma: no cover - defensive catch-all
            return None, {
                'reason': 'unexpected_error',
                'detail': str(exc),
            }

        status = getattr(response, 'code', None) or response.getcode()
        body = response.read()
        if status != 200:
            parsed = self._safe_json(body)
            return None, {
                'reason': 'http_error',
                'status': status,
                'body': parsed,
            }

        try:
            text = self._ensure_text(body)
            return json.loads(text), None
        except ValueError as exc:
            return None, {
                'reason': 'decode_error',
                'detail': 'invalid JSON response: %s' % exc,
            }

    def _build_url(self, path):
        if not path:
            raise ValueError('path is required')
        if not path.startswith('/'):
            path = '/' + path
        return self.base_url + path

    @staticmethod
    def _safe_json(raw_body):
        if raw_body is None:
            return None
        try:
            text = LLMBridgeClient._ensure_text(raw_body)
            return json.loads(text)
        except (TypeError, ValueError):
            return raw_body

    @staticmethod
    def _ensure_text(raw):
        if isinstance(raw, text_type):
            return raw
        if isinstance(raw, bytes_type):
            try:
                return raw.decode('utf-8')
            except AttributeError:
                return raw
        return raw

    @staticmethod
    def _timeout_error(url):
        return {
            'reason': 'timeout',
            'detail': 'request to %s exceeded the configured timeout' % url,
        }


__all__ = ['LLMBridgeClient']
```

## Runtime counters in `code/timing.py`
```python
# timing.py

#    This is the code behind the paper The Effects of Fiscal Targets in a Monetary Union: a Multi-Country Agent Based-Stock Flow Consistent Model
#    Copyright (C) 2017  Alessandro Caiani, Ermanno Catullo, Mauro Gallegati.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# flake8: noqa
from parameter import *
from initialize import *
from firm import *
from consumer import *
from matchingConsumption import *
from matchingLaborCapital import *
from enterExit import *
from aggregator import *
#from aggregatorAle import *
from time import *
import random
import os
import glob
import csv
from bank import *
from matchingCredit import *
from matchingBonds import *
from matchingDeposit import *
from globalInnovation import *
from printParameters import *
from centralBankUnion import *
from policy import *
from llm_runtime import (
    configure as configure_llm,
    ensure_counter as ensure_llm_counter,
    get_counters_snapshot as get_llm_counters_snapshot,
    reset_counters as reset_llm_counters,
)


_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'timing.log'))


def _flag(value):
    return 'on' if value else 'off'


def _log_llm_counter_line(parameter, run_id, counters):
    counters = counters or {}
    calls = int(counters.get('calls', 0))
    fallbacks = int(counters.get('fallbacks', 0))
    timeouts = int(counters.get('timeouts', 0))
    line = (
        '[LLM firm] counters name=%s run=%s llm=%s calls=%d fallbacks=%d timeouts=%d\n'
        % (
            getattr(parameter, 'name', 'n/a'),
            run_id,
            _flag(getattr(parameter, 'use_llm_firm_pricing', False)),
            calls,
            fallbacks,
            timeouts,
        )
    )
    try:
        handle = open(_LOG_PATH, 'a')
        handle.write(line)
        handle.close()
    except Exception as exc:
        print 'Warning: failed to write firm counter log (%s)' % exc
    print line.strip()


def log_llm_toggles(parameter):
    """Append the current LLM toggle configuration to timing.log."""

    timestamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
    line = (
        '[%s] LLM toggles server=%s timeout_ms=%s batch=%s firm=%s bank=%s wage=%s\n'
        % (
            timestamp,
            parameter.llm_server_url,
            parameter.llm_timeout_ms,
            _flag(parameter.llm_batch),
            _flag(parameter.use_llm_firm_pricing),
            _flag(parameter.use_llm_bank_credit),
            _flag(parameter.use_llm_wage),
        )
    )
    try:
        handle = open(_LOG_PATH, 'a')
        handle.write(line)
        handle.close()
    except Exception as exc:
        print 'Warning: failed to write LLM toggle log (%s)' % exc
    print line.strip()



def run_simulation(parameter=None, progress=True):
    # parameter
    para = parameter or Parameter()
    para.directory()
    log_llm_toggles(para)
    printPa=PrintParameters(para.name,para.folder)
    configure_llm(para)

    run_counters = {}

    for run in para.Lrun:
        if para.weSeedRun=='yes':
           random.seed(run) 
        reset_llm_counters()
        ensure_llm_counter('firm')
        # initialization
        printPa.printingPara(para,run)
        ite=Initialize(para.ncountry,para.nconsumer,para.A,para.phi,\
                       para.beta,para.folder,para.name,run,para.delta,\
                       para.taxRatio,para.rDiscount,para.G,\
                       para.cDisposableIncome,para.cWealth,para.liqPref,para.rDeposit,para.rBonds,\
                       para.upsilon,para.maxPublicDeficit,para.xiBonds,para.ls,para.taxRatioMin,\
                       para.taxRatioMax,para.gMin,para.gMax,para.w0,para.wBar,para.upsilon2) 
        ite.createCentralBank()
        ite.createConsumer() 
        ite.createBasic()
        ite.createEtat()  
        name=para.name+'r'+str(run)
        gloInnovation=GlobalInnovation(ite.Lcountry,para.phi)

        enEx=enterExit(ite.Lcountry,ite.McountryFirmMaxNumber,\
                      para.folder,para.name,run,para.delta,para.A,\
                      ite.McountryBankMaxNumber,para.probBank,para.minReserve,\
```

## `timing.log` sample (stub run)
```
[2025-09-30 10:20:49] LLM toggles server=http://127.0.0.1:8000 timeout_ms=200 batch=off firm=on bank=off wage=off
[LLM firm] counters name=muxSnCo5upsilon20.7polModPolVar0.512 run=0 llm=on calls=94139 fallbacks=94139 timeouts=0
```

## Architect live-mode spec (summary points)
```markdown
- OpenRouter adapter (Chat Completions) with JSON output enforcement.
- Primary/fallback model slugs (executor to verify via `/api/v1/models`).
- Endpoint-specific prompts & JSON Schemas (firm/bank/wage) with guard-aware ranges.
- Deterministic settings: `temperature=0`, optional `seed`, deadline 200 ms, fallback ladder → baseline.
- Additional docs: upcoming `docs/methods/decider_live_openrouter.md`, AGENTS quickstart for live mode.
```

# Metrics & overlays
- CSV (raw values): `data/firm/firm_ab_table.csv`
  ```csv
scenario,metric,value
llm_on,inflation_volatility,0.0061805681026881705
llm_on,price_dispersion,0.20957101039825526
baseline,inflation_volatility,0.0061805681026881705
baseline,price_dispersion,0.20957101039825526
  ```
- Overlay figure: `figs/firm/firm_ab_overlay.png` (OFF dashed, ON solid, final 50 ticks shaded).

# Writing guidance
- Target 3–4 paragraphs; lead with baseline context, then the hook mechanics, then runtime logging & manuscript artefacts, closing with the live-mode path.
- Cite figures/tables using Quarto notation: `@tbl-firm-ab`, `@fig-firm-ab`.
- Call out guard magnitudes numerically. Mention fallback reasons (timeouts, validation failures, stub 400s).
- Note that current OFF/ON overlays are identical because the stub rejects extra features; tee up future work using architect spec.
- Avoid code-level minutiae beyond what’s necessary for narrative clarity.

# Deliverable packaging
- Submit the prose block (Markdown) back on Issue #30.
- Include a short bullet list of any assumptions or open questions the writer needs clarified.
