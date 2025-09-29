# Writer Brief - Baseline vs LLM fallback semantics (Issue #13)

This brief contains everything you need to draft the fallback semantics page. You do not need repository access; all relevant sources are embedded below.

## Scope & Deliverable

- **Issue:** #13 - Docs - Baseline vs LLM fallback semantics (1 page).
- **Audience:** Methods section of the manuscript; readers need to understand exactly when the Caiani Py2 simulation keeps the LLM decision versus when it falls back to legacy heuristics.
- **Expected output:** One Quarto page (suggested path `docs/methods/fallbacks.qmd`) that:
  1. Explains the bridge architecture (Py3 Decider stub + Py2 client).
  2. Summarises guardrails and timeout configuration (`llm_timeout_ms`, guard presets).
  3. Details the fallback pipeline for each block (firm, bank, wage): when the client returns `None`, validation fails, guard clamps fire, etc.
  4. Enumerates logging/telemetry hooks (`log_fallback`, `timing.log`) and how test harnesses should interpret them.
  5. References reusable commands (stub start, smoke run) from `docs/repro_manual.qmd` as appropriate.
- **Style:** Formal methods prose (3-5 subsections), include inline code fences where necessary. Anchor the page so manuscript sections can cite it (e.g., `{#sec-fallbacks}`).

## Key Design Facts

- LLM toggles live in `code/parameter.py` (`use_llm_*`, `llm_timeout_ms`, guard presets). Defaults keep the bridge off until explicitly activated.
- The Python 2 bridge client (`code/llm_bridge_client.py`) normalises URLs, enforces JSON headers, and returns `(decision, error)` tuples. Any error triggers a fallback path handled in the agent code.
- Runtime context (`code/llm_runtime.py`) caches the client and prints `[LLM <block>] fallback: ... ` messages when guardrails or network conditions force baseline behaviour.
- Agent hooks (e.g., `Firm.learning`, `Bank.credit_decision`) call `log_fallback` on:
  * missing client (server offline or toggle disabled)
  * timeouts, connection errors, invalid JSON
  * schema validation failures / guard clamps / invalid payloads
- The Decider stub (`tools/decider/server.py`) enforces deadlines, request schemas, and exposes deterministic stub outputs; exceeding deadlines or budgets surfaces as client timeouts or HTTP 503/429, which the bridge reports.

## Embedded Sources (verbatim)

### `docs/methods/py2_client.md`

<pre><code>---
title: &quot;Python 2 HTTP client&quot;
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

This page documents the **Python 2** client that calls the local Decider service. The legacy Caiani simulation stays in Python 2, so we ship a thin wrapper around ``urllib2`` that knows how to talk to the Python 3 server, parse JSON, and signal when the caller should fall back to the baseline heuristic.

## Quickstart

```python
from code.llm_bridge_client import LLMBridgeClient

client = LLMBridgeClient(&quot;http://127.0.0.1:8000&quot;, timeout=0.2)
state = {&quot;inventory&quot;: 120, &quot;backlog&quot;: 6}

decision, error = client.decide_firm(state)
if decision is None:
    # Baseline fallback path: log the reason, keep legacy heuristic.
    LOGGER.warning(&quot;firm LLM fallback: %s&quot;, error)
    apply_baseline_firm_rule(state)
else:
    apply_llm_firm_rule(decision)
```

- The client normalises the base URL (trims trailing slashes) and sets the ``Content-Type: application/json`` header for every request.
- ``timeout`` defaults to ``0.2`` seconds (200 ms) to match the M1 run logistics agreement. Pass ``None`` to use the ``urllib2`` global default.
- Every call returns ``(decision_dict, error_info)``. When ``decision_dict`` is ``None`` you *must* fall back to the legacy baseline rule.

## Available helpers

| Method | Endpoint | Notes |
| --- | --- | --- |
| ``decide_firm(payload)`` | ``POST /decide/firm`` | Pricing &amp; expectations decision |
| ``decide_bank(payload)`` | ``POST /decide/bank`` | Loan approval + spread (basis points) |
| ``decide_wage(payload)`` | ``POST /decide/wage`` | Worker reservation / firm offer |

Each helper validates that ``payload`` is a ``dict`` and serialises it with ``json.dumps`` before issuing the POST.

## Error signalling

When a request fails, ``None`` is returned along with a short diagnostic dictionary. The caller is responsible for logging it (or counting for telemetry) before taking the baseline path. The ``reason`` field is always present:

| Reason | Trigger | Extra fields |
| --- | --- | --- |
| ``timeout`` | Socket timeout (client side) | ``detail``: string message |
| ``connection_error`` | ``urllib2.URLError`` other than timeout | ``detail``: string message |
| ``http_error`` | HTTP status other than 200 | ``status`` (int), ``body`` (parsed JSON or raw string) |
| ``decode_error`` | Response body not valid JSON | ``detail``: string message |
| ``unexpected_error`` | Catch-all for any other exception | ``detail``: string message |

Example handling:

```python
payload = {&quot;leverage&quot;: 3.2, &quot;credit_request&quot;: 100.0}
decision, error = client.decide_bank(payload)
if decision is None:
    # Tell the logs that we hit the fallback path.
    LOGGER.info(&quot;bank LLM fallback (%s): %s&quot;, error[&#x27;reason&#x27;], error.get(&#x27;detail&#x27;))
    approve, spread = baseline_bank_decision(payload)
else:
    approve = decision.get(&quot;approve&quot;, False)
    spread = decision.get(&quot;spread_bps&quot;, 150)
```

The helper methods never raise on network failures so the simulation can keep running; only programmer errors (e.g., passing a non-dict payload) raise immediately.

## Local testing recipe

1. Start the Decider stub in another terminal:

   ```bash
   python3 tools/decider/server.py --stub
   ```

2. Run a short Python 2 REPL snippet:

   ```python
   &gt;&gt;&gt; from code.llm_bridge_client import LLMBridgeClient
   &gt;&gt;&gt; client = LLMBridgeClient(&quot;http://127.0.0.1:8000&quot;)
   &gt;&gt;&gt; client.decide_wage({&quot;unemployment&quot;: 0.04})
   ({&#x27;direction&#x27;: &#x27;hold&#x27;, &#x27;wage_step&#x27;: 0.0, &#x27;explanation&#x27;: &#x27;stub: no wage adjustment&#x27;}, None)
   ```

3. Stop the server and re-run the call to see the fallback output:

   ```python
   &gt;&gt;&gt; client.decide_wage({&quot;unemployment&quot;: 0.04})
   (None, {&#x27;reason&#x27;: &#x27;connection_error&#x27;, &#x27;detail&#x27;: &#x27;[Errno 111] Connection refused&#x27;})
   ```

When you wire the client into the simulation, keep the tuples intact so the fallback logic can log the reason (timeout vs HTTP error vs invalid JSON) before applying the baseline heuristic.
</code></pre>

### `code/llm_bridge_client.py`

<pre><code># -*- coding: utf-8 -*-
&quot;&quot;&quot;HTTP client for the local Decider service (Python 2).

This module provides a minimal wrapper around ``urllib2`` so the legacy Caiani
simulation (Python 2) can talk to the Python 3 Decider server.  The client
exposes helper methods for the three decision endpoints and surfaces a tuple of
``(response_dict, error_info)`` to the caller.  ``response_dict`` is returned on
HTTP 200 with valid JSON; otherwise ``None`` is returned together with a short
error descriptor that the simulation can log before falling back to the baseline
heuristic.
&quot;&quot;&quot;

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
    &#x27;firm&#x27;: &#x27;/decide/firm&#x27;,
    &#x27;bank&#x27;: &#x27;/decide/bank&#x27;,
    &#x27;wage&#x27;: &#x27;/decide/wage&#x27;,
}


class LLMBridgeClient(object):
    &quot;&quot;&quot;Minimal HTTP client for the Decider stub/live service.&quot;&quot;&quot;

    def __init__(self, base_url, timeout=0.2, headers=None):
        if not base_url:
            raise ValueError(&#x27;base_url is required&#x27;)
        # Normalise whitespace and trailing slashes so path joins are predictable.
        base_url = base_url.strip()
        if base_url.endswith(&#x27;/&#x27;):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.timeout = float(timeout) if timeout is not None else None
        self.headers = {&#x27;Content-Type&#x27;: &#x27;application/json&#x27;}
        if headers:
            self.headers.update(headers)

    def decide_firm(self, payload):
        &quot;&quot;&quot;Call the firm endpoint.

        Returns ``(response_dict, error_info)``.
        &quot;&quot;&quot;

        return self._post_json(_DECISION_ENDPOINTS[&#x27;firm&#x27;], payload)

    def decide_bank(self, payload):
        &quot;&quot;&quot;Call the bank endpoint (loan approval &amp; spread).&quot;&quot;&quot;

        return self._post_json(_DECISION_ENDPOINTS[&#x27;bank&#x27;], payload)

    def decide_wage(self, payload):
        &quot;&quot;&quot;Call the wage endpoint (worker reservation / firm offer).&quot;&quot;&quot;

        return self._post_json(_DECISION_ENDPOINTS[&#x27;wage&#x27;], payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post_json(self, path, payload):
        &quot;&quot;&quot;POST ``payload`` (dict) to ``path`` and return ``(data, error)``.

        ``data`` is a Python object parsed from JSON when the response is 200
        and well-formed.  Otherwise ``None`` is returned along with ``error``, a
        dict containing at least a ``reason`` key.  The caller can log this and
        fall back to the baseline decision logic.
        &quot;&quot;&quot;

        if not isinstance(payload, dict):
            raise TypeError(&#x27;payload must be a dict (got %r)&#x27; % type(payload))

        url = self._build_url(path)
        data = json.dumps(payload)
        request = urllib2.Request(url, data=data, headers=self.headers)

        try:
            response = urllib2.urlopen(request, timeout=self.timeout)
        except urllib2.HTTPError as exc:
            error_body = exc.read()
            parsed = self._safe_json(error_body)
            return None, {
                &#x27;reason&#x27;: &#x27;http_error&#x27;,
                &#x27;status&#x27;: exc.code,
                &#x27;body&#x27;: parsed,
            }
        except urllib2.URLError as exc:
            # ``URLError`` wraps a variety of socket issues.  Timeouts may be
            # surfaced either as ``socket.timeout`` or via ``str(reason)``.
            if isinstance(exc.reason, socket.timeout):
                return None, self._timeout_error(url)
            return None, {
                &#x27;reason&#x27;: &#x27;connection_error&#x27;,
                &#x27;detail&#x27;: str(exc.reason),
            }
        except socket.timeout:
            return None, self._timeout_error(url)
        except Exception as exc:  # pragma: no cover - defensive catch-all
            return None, {
                &#x27;reason&#x27;: &#x27;unexpected_error&#x27;,
                &#x27;detail&#x27;: str(exc),
            }

        status = getattr(response, &#x27;code&#x27;, None) or response.getcode()
        body = response.read()
        if status != 200:
            parsed = self._safe_json(body)
            return None, {
                &#x27;reason&#x27;: &#x27;http_error&#x27;,
                &#x27;status&#x27;: status,
                &#x27;body&#x27;: parsed,
            }

        try:
            text = self._ensure_text(body)
            return json.loads(text), None
        except ValueError as exc:
            return None, {
                &#x27;reason&#x27;: &#x27;decode_error&#x27;,
                &#x27;detail&#x27;: &#x27;invalid JSON response: %s&#x27; % exc,
            }

    def _build_url(self, path):
        if not path:
            raise ValueError(&#x27;path is required&#x27;)
        if not path.startswith(&#x27;/&#x27;):
            path = &#x27;/&#x27; + path
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
                return raw.decode(&#x27;utf-8&#x27;)
            except AttributeError:
                return raw
        return raw

    @staticmethod
    def _timeout_error(url):
        return {
            &#x27;reason&#x27;: &#x27;timeout&#x27;,
            &#x27;detail&#x27;: &#x27;request to %s exceeded the configured timeout&#x27; % url,
        }


__all__ = [&#x27;LLMBridgeClient&#x27;]
</code></pre>

### `code/llm_runtime.py`

<pre><code># -*- coding: utf-8 -*-
&quot;&quot;&quot;Shared LLM runtime context for the Python 2 simulation.&quot;&quot;&quot;

from __future__ import absolute_import

try:
    from llm_bridge_client import LLMBridgeClient
except ImportError:  # pragma: no cover - package import fallback
    from .llm_bridge_client import LLMBridgeClient

_CONTEXT = {
    &#x27;parameter&#x27;: None,
    &#x27;client&#x27;: None,
}

_GUARD_PRESET_FACTORS = {
    &#x27;baseline&#x27;: 1.0,
    &#x27;tight&#x27;: 0.5,
    &#x27;loose&#x27;: 1.5,
}


def configure(parameter):
    &quot;&quot;&quot;Register the active ``Parameter`` instance for downstream hooks.&quot;&quot;&quot;

    _CONTEXT[&#x27;parameter&#x27;] = parameter
    _CONTEXT[&#x27;client&#x27;] = None


def get_parameter():
    return _CONTEXT.get(&#x27;parameter&#x27;)


def get_client():
    parameter = get_parameter()
    if not parameter:
        return None
    client = _CONTEXT.get(&#x27;client&#x27;)
    if client is None:
        timeout = parameter.llm_timeout_ms or 0
        timeout = float(timeout) / 1000.0
        client = LLMBridgeClient(parameter.llm_server_url, timeout=timeout)
        _CONTEXT[&#x27;client&#x27;] = client
    return client


def firm_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_firm_pricing)


def bank_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_bank_credit)


def log_fallback(block, reason, detail=None):
    message = &#x27;[LLM %s] fallback: %s&#x27; % (block, reason)
    if detail:
        message = message + &#x27; (%s)&#x27; % detail
    print message


def get_firm_guard_caps():
    &quot;&quot;&quot;Return effective guard caps for firm price/expectation decisions.&quot;&quot;&quot;

    parameter = get_parameter()
    if parameter:
        custom = getattr(parameter, &#x27;firm_guard_caps&#x27;, None)
        if isinstance(custom, dict):
            return _sanitise_firm_caps(custom)

    preset = &#x27;baseline&#x27;
    if parameter:
        preset = _resolve_guard_preset(parameter, &#x27;firm_guard_preset&#x27;)
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)
    base = {
        &#x27;max_price_step&#x27;: 0.04,
        &#x27;max_expectation_bias&#x27;: 0.04,
    }
    return _scale_caps(base, factor)


def _resolve_guard_preset(parameter, attribute):
    value = getattr(parameter, attribute, None)
    if value:
        return _normalise_preset(value)
    fallback = getattr(parameter, &#x27;llm_guard_preset&#x27;, None)
    if fallback:
        return _normalise_preset(fallback)
    return &#x27;baseline&#x27;


def _normalise_preset(value):
    text = str(value).strip().lower()
    if text in _GUARD_PRESET_FACTORS:
        return text
    return &#x27;baseline&#x27;


def _scale_caps(base_caps, factor):
    scaled = {}
    for key, value in base_caps.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        scaled[key] = max(0.0, numeric * factor)
    return scaled


def _sanitise_firm_caps(custom):
    if not isinstance(custom, dict):
        return {
            &#x27;max_price_step&#x27;: 0.04,
            &#x27;max_expectation_bias&#x27;: 0.04,
        }

    caps = {}
    for key in (&#x27;max_price_step&#x27;, &#x27;max_expectation_bias&#x27;):
        value = custom.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric &lt; 0.0:
            numeric = 0.0
        caps[key] = numeric
    if &#x27;max_price_step&#x27; not in caps:
        caps[&#x27;max_price_step&#x27;] = 0.04
    if &#x27;max_expectation_bias&#x27; not in caps:
        caps[&#x27;max_expectation_bias&#x27;] = 0.04
    return caps


__all__ = [&#x27;configure&#x27;, &#x27;get_client&#x27;, &#x27;get_parameter&#x27;, &#x27;firm_enabled&#x27;, &#x27;bank_enabled&#x27;, &#x27;log_fallback&#x27;, &#x27;get_firm_guard_caps&#x27;]
</code></pre>

### Firm hook (excerpt)

<pre><code>              self.LpastEmployment.append(0)
          self.memPastEmployment=0    
          self.loanEffReceived=0  
          #self.LpastEmployment=[0,0,0,0] 
          #self.LpastEmployment=[0,0,0,0,0,0,0,0,0,0]    
          
          
      def learning(self):       
          # Eq. 12-14 (Caiani et al. 2016): pricing/expec update pre-LLM.
          if self.closing!=&#x27;no&#x27;:
             return

          previous_price=self.price
          baseline=self._baseline_pricing_update()
          guard_caps=get_firm_guard_caps()

          if not firm_enabled():
             return

          client=get_client()
          if client is None:
             log_fallback(&#x27;firm&#x27;,&#x27;client_unavailable&#x27;)
             self._apply_baseline(baseline)
             return

          payload, feature_error=self._build_llm_payload(previous_price,baseline,guard_caps)
          if payload is None:
             log_fallback(&#x27;firm&#x27;,&#x27;feature_pack_missing&#x27;,feature_error)
             self._apply_baseline(baseline)
             return
          decision,error=client.decide_firm(payload)
          if error:
             reason=&#x27;error&#x27;
             detail=None
             if isinstance(error,dict):
                reason=error.get(&#x27;reason&#x27;,&#x27;error&#x27;)
                detail=error.get(&#x27;detail&#x27;)
             log_fallback(&#x27;firm&#x27;,reason,detail)
             self._apply_baseline(baseline)
             return

          if not self._validate_llm_decision(decision):
             log_fallback(&#x27;firm&#x27;,&#x27;invalid_response&#x27;)
             self._apply_baseline(baseline)
             return

          self._apply_llm_decision(previous_price,baseline,decision,guard_caps)

      def _baseline_pricing_update(self):
          self.mind.alphaParameterSmooth16(self.phi,self.w,self.inventory,self.pastInventory,\
                                           self.price,self.productionEffective,self.xSold)
          self.pastPrice=self.price
          self.price=self.mind.pSelling
          unit_cost=self._unit_cost()
          price_floor=max(unit_cost,(1.0+self.minMarkUp)*unit_cost)
          return {
              &#x27;price&#x27;: self.price,
              &#x27;expected_demand&#x27;: getattr(self.mind,&#x27;xE&#x27;,0.0),
              &#x27;producing&#x27;: getattr(self.mind,&#x27;xProducing&#x27;,0.0),
              &#x27;price_floor&#x27;: price_floor,
          }

      def _apply_baseline(self,baseline):
          self.price=baseline.get(&#x27;price&#x27;,self.price)
          self.mind.pSelling=self.price
          self.mind.xE=baseline.get(&#x27;expected_demand&#x27;,self.mind.xE)
          self.mind.xProducing=baseline.get(&#x27;producing&#x27;,getattr(self.mind,&#x27;xProducing&#x27;,0.0))

      def _build_llm_payload(self,previous_price,baseline,guard_caps):
          &quot;&quot;&quot;Construct the Decider payload including guard caps and feature pack.

          Feature ranges (pre-decision state):
              - ``inv_ratio`` >= 0: inventory / max(expected demand, 1e-9).
              - ``backlog`` >= 0: max(0, expected demand - offered supply).
              - ``delta_price_comp`` in R: baseline price - last-period price.
              - ``last_sales`` >= 0: quantity sold in the previous tick.
              - ``capacity`` >= 0: effective production carried from the last tick.
              - ``liquidity`` in R: working capital flagged by the accounting block.
              - ``sector_code`` in {``tradable``, ``non_tradable``}.
          Missing/non-finite values trigger a baseline fallback.
          &quot;&quot;&quot;

          unit_cost=self._unit_cost()
          price_floor=baseline.get(&#x27;price_floor&#x27;,unit_cost)
          production_effective=getattr(self,&#x27;productionEffective&#x27;,0.0)
          expected=self._safe_numeric(baseline.get(&#x27;expected_demand&#x27;,0.0))
          if expected is None:
             expected=0.0
          max_step=guard_caps.get(&#x27;max_price_step&#x27;,0.04)
          max_bias=guard_caps.get(&#x27;max_expectation_bias&#x27;,0.04)
          baseline_price=baseline.get(&#x27;price&#x27;,previous_price)
          features,missing=self._compute_feature_pack(previous_price,baseline_price,expected,production_effective)
          if missing:
             return None, &#x27;,&#x27;.join(missing)
          payload={
              &#x27;schema_version&#x27;:&#x27;1.0&#x27;,
              &#x27;run_id&#x27;:getattr(self,&#x27;run&#x27;,0),
              &#x27;tick&#x27;:getattr(self,&#x27;llm_tick&#x27;,0),
              &#x27;country_id&#x27;:self.country,
              &#x27;firm_id&#x27;:self.ide,
              &#x27;price&#x27;:previous_price,
              &#x27;unit_cost&#x27;:features[&#x27;unit_cost&#x27;],
              &#x27;inventory&#x27;:self.inventory,
              &#x27;inventory_value&#x27;:getattr(self,&#x27;inventoryValue&#x27;,0.0),
              &#x27;production_effective&#x27;:production_effective,
              &#x27;baseline&#x27;:{
                  &#x27;price&#x27;:baseline_price,
                  &#x27;expected_demand&#x27;:expected,
              },
              &#x27;guards&#x27;:{
                  &#x27;max_price_step&#x27;:max_step,
                  &#x27;max_expectation_bias&#x27;:max_bias,
                  &#x27;price_floor&#x27;:price_floor,
              },
          }
          payload.update({
              &#x27;inv_ratio&#x27;:features[&#x27;inv_ratio&#x27;],
              &#x27;backlog&#x27;:features[&#x27;backlog&#x27;],
              &#x27;delta_price_comp&#x27;:features[&#x27;delta_price_comp&#x27;],
              &#x27;last_sales&#x27;:features[&#x27;last_sales&#x27;],
              &#x27;capacity&#x27;:features[&#x27;capacity&#x27;],</code></pre>

### Bank hook (excerpt)

<pre><code>          # Eq. 26 (Caiani et al. 2016): loan approval probability before LLM override.
          probLoan=math.exp(-1*self.iota*leverage)
          if relPhi&lt;=1.0:
             probLoan=math.exp(-1*self.iotaRelPhi*leverage)
          return probLoan

      def credit_decision(self,firm_obj,leverage,relPhi,loan_request,loan_supply,max_loan_firm):
          try:
             loan_request=float(loan_request or 0.0)
          except (TypeError,ValueError):
             loan_request=0.0
          try:
             loan_supply=float(loan_supply or 0.0)
          except (TypeError,ValueError):
             loan_supply=0.0
          try:
             max_loan_firm=float(max_loan_firm or 0.0)
          except (TypeError,ValueError):
             max_loan_firm=0.0
          baseline=self._baseline_credit_decision(leverage,relPhi,loan_request,loan_supply,max_loan_firm)
          state=baseline.copy()
          state.update({
              &#x27;baseline&#x27;:baseline,
              &#x27;decision&#x27;:None,
              &#x27;used_llm&#x27;:False,
              &#x27;fallback&#x27;:False,
              &#x27;fallback_reason&#x27;:None,
          })
          self._llm_bank_last_decision=state
          if not bank_enabled():
             return state

          client=get_client()
          if client is None:
             log_fallback(&#x27;bank&#x27;,&#x27;client_unavailable&#x27;)
             state[&#x27;fallback&#x27;]=True
             state[&#x27;fallback_reason&#x27;]=&#x27;client_unavailable&#x27;
             self._llm_bank_last_decision=state
             return state

          payload=self._build_llm_payload(firm_obj,leverage,relPhi,loan_request,loan_supply,baseline)
          decision,error=client.decide_bank(payload)
          if error:
             reason=&#x27;error&#x27;
             detail=None
             if isinstance(error,dict):
                reason=error.get(&#x27;reason&#x27;,&#x27;error&#x27;)
                detail=error.get(&#x27;detail&#x27;)
             log_fallback(&#x27;bank&#x27;,reason,detail)
             state[&#x27;fallback&#x27;]=True
             state[&#x27;fallback_reason&#x27;]=reason
             self._llm_bank_last_decision=state
             return state

          if not self._validate_llm_decision(decision):
             log_fallback(&#x27;bank&#x27;,&#x27;invalid_response&#x27;)
             state[&#x27;fallback&#x27;]=True
             state[&#x27;fallback_reason&#x27;]=&#x27;invalid_response&#x27;
             self._llm_bank_last_decision=state
             return state

          applied=self._apply_llm_decision(decision,baseline,loan_request)
          applied.update({
              &#x27;baseline&#x27;:baseline,
              &#x27;decision&#x27;:decision,
              &#x27;used_llm&#x27;:True,
              &#x27;fallback&#x27;:False,
              &#x27;fallback_reason&#x27;:None,
          })
          self._llm_bank_last_decision=applied
          return applied

      def _baseline_credit_decision(self,leverage,relPhi,loan_request,loan_supply,max_loan_firm):
          probability=self.computeProbProvidingLoan(leverage,relPhi)
          if probability&lt;0.0:
             probability=0.0
          if probability&gt;1.0:
             probability=1.0
          limit=min(max_loan_firm,loan_supply)
          if limit&gt;loan_request:
             limit=loan_request
          if limit&lt;0.0:
             limit=0.0
          interest=self.computeInterestRate(leverage)
          spread=max(0.0,(interest-self.rDiscount)*10000.0)
          baseline={
             &#x27;approve&#x27;:True,
             &#x27;probability&#x27;:probability,
             &#x27;credit_limit&#x27;:limit,
             &#x27;interest_rate&#x27;:interest,
             &#x27;spread_bps&#x27;:spread,
          }
          return baseline

      def _build_llm_payload(self,firm_obj,leverage,relPhi,loan_request,loan_supply,baseline):
          guards=self._spread_guard_bounds()
          payload={
              &#x27;schema_version&#x27;:&#x27;1.0&#x27;,
              &#x27;run_id&#x27;:getattr(self,&#x27;run&#x27;,0),
              &#x27;tick&#x27;:getattr(self,&#x27;llm_tick&#x27;,0),
              &#x27;bank_id&#x27;:self.ide,
              &#x27;country_id&#x27;:self.country,
              &#x27;capital&#x27;:getattr(self,&#x27;A&#x27;,0.0),
              &#x27;loan_supply&#x27;:loan_supply,
              &#x27;reserves&#x27;:getattr(self,&#x27;Reserves&#x27;,0.0),
              &#x27;loan_book_value&#x27;:getattr(self,&#x27;Loan&#x27;,0.0),
              &#x27;deposits&#x27;:getattr(self,&#x27;Deposit&#x27;,0.0),
              &#x27;non_allocated_money&#x27;:getattr(self,&#x27;nonAllocatedMoney&#x27;,0.0),
              &#x27;borrower&#x27;:{
                  &#x27;firm_id&#x27;:getattr(firm_obj,&#x27;ide&#x27;,&#x27;&#x27;),
                  &#x27;country_id&#x27;:getattr(firm_obj,&#x27;country&#x27;,0),
                  &#x27;loan_request&#x27;:loan_request,
                  &#x27;leverage&#x27;:leverage,
                  &#x27;relative_productivity&#x27;:relPhi,
                  &#x27;profit_rate&#x27;:getattr(firm_obj,&#x27;profitRate&#x27;,0.0),
              },
              &#x27;guards&#x27;:{
                  &#x27;spread_min_bps&#x27;:guards[0],
                  &#x27;spread_max_bps&#x27;:guards[1],
              },
              &#x27;baseline&#x27;:{
                  &#x27;probability&#x27;:baseline.get(&#x27;probability&#x27;),
                  &#x27;credit_limit&#x27;:baseline.get(&#x27;credit_limit&#x27;),
                  &#x27;spread_bps&#x27;:baseline.get(&#x27;spread_bps&#x27;),
              },
          }
          return payload

      def _validate_llm_decision(self,decision):
          if not isinstance(decision,dict):
             return False
          try:
             approve=decision.get(&#x27;approve&#x27;,True)
             decision[&#x27;approve&#x27;]=bool(approve)
          except Exception:
             return False
          try:
             ratio=float(decision.get(&#x27;credit_limit_ratio&#x27;,1.0))
          except (TypeError,ValueError):
             return False
          if ratio&lt;0.0:</code></pre>

### Parameter toggles (excerpt)

<pre><code>import csv
import os
import math

#mu5.8

class Parameter:
      def __init__(self):                         
          self.name=&#x27;muxSnCo5upsilon20.7polModPolVar0.512&#x27;#1.625&#x27;#2.876&#x27;#2.231#1.625&#x27;#1.053#0.512&#x27;
          self.folder=&#x27;/home/ermanno/Desktop/mu/mu7.1/data/data&#x27;+self.name
          #self.folder=&#x27;/home/ermanno/mu/mu7.1/data/data&#x27;+self.name
          #Monte Carlo runs
          firstrun=0#
          lastrun=49#
          self.Lrun=range(firstrun,lastrun+1)
          self.weSeedRun=&#x27;yes&#x27;      
          # LLM bridge configuration (defaults keep legacy heuristics)
          self.use_llm_firm_pricing = False
          self.use_llm_bank_credit = False
          self.use_llm_wage = False
          self.llm_server_url = &#x27;http://127.0.0.1:8000&#x27;
          self.llm_timeout_ms = 200
          self.llm_batch = False
          # space and time
          self.ncycle=1001
          self.ncountry=5 #(K)
          self.nconsumer=500#1000 #(H)
          self.propTradable=0.4#0.4#(c_T)           
          # firms
          self.A=10#(A^0)
          self.upsilon=1.625#1.0# (upsilon)
          self.upsilon2=0.7#(upsilon2)  
          self.phi=1.0 # (phi_0)
          self.delta=0.04#0.03 (delta) 
          self.dividendRate=0.95#0.95# (rho)   
          self.gamma=0.03#(gamma)
          self.ni=0.8#1.0#(ni) 
          self.deltaInnovation=0.04# (delta) 
          self.Fcost=1.0# (F)
          self.minMarkUp=0.0#0.0# (minimum mark-up)
          self.theta=0.2
          self.jobDuration=0#self.ncycle#40
          #consumers         
          self.bound=10# # (psi)  n. matching       
          self.cDisposableIncome=0.9# (c_y)
          self.cWealth=0.1# (c_D)
          self.liqPref=0.1# (lambda) 
          self.beta=2.0#2.0#0.25#2.0#(beta)
          self.ls=1.0 #(l^S) 
          self.wBar=0.1 #(w bar)
          self.w0=1.0 #(w_0)          
          #bank
          self.probBank=0.1#0.1(eta)
          self.sigma=4.0 
          self.minReserve=0.1  #(mu_2)        
          self.xi=0.003#0.003# (chi)     
          self.rDeposit=0.001# (r_re)  
          self.mu1=20.0#12.0#(mu_1)
          self.iota=0.5#0.5#1.0#(iota_l)
          self.iotaE=0.1#(iota_b) 
          #etat
          self.taxRatio=0.4 #(tau_0)
          self.G=0.4*self.nconsumer  #(G)              
          self.xiBonds=self.xi#(chi_B)   
          self.maxPublicDeficit=0.03#(d^max)  
          self.taxRatioMin=0.35#0.35 #(tau_{min})
          self.taxRatioMax=0.45#0.45 #(tau_{max})
          self.gMin=0.4 #(g_min)
          self.gMax=0.6#float(&#x27;inf&#x27;)# #(g_max)       
          #central bank initial discount value
          self.rDiscount=0.001 #(r_ {re})
          self.rBonds=0.001 #(r_{b0})   
          self.zeta=0.1 #(zeta) 
          self.rBar=0.0075 #(rBar)
          self.csi=0.8 #(xi)
          self.csiDP=2.0#(xiDP)  
          self.inflationTarget=0.005#(DeltaP) 
          # policy
          self.policyKind=&#x27;Mod&#x27;#&#x27;nn&#x27;#&#x27;ModAll&#x27;#&#x27;Mod&#x27;
          self.startingPolicy=500#(policy starting time)</code></pre>

### Decider stub (excerpt)

<pre><code>#!/usr/bin/env python3
&quot;&quot;&quot;Local Decider stub server.

This module exposes a minimal HTTP server that mimics the future LLM-powered
&quot;Decider&quot; microservice.  For Milestone M1-01 we only implement deterministic
stub responses and a `/healthz` endpoint; later milestones will extend this file
with schema validation, caching, and timeouts.

Usage (from the repo root):

    python3 tools/decider/server.py --stub

Optional flags:
    --host / --port   Bind address (defaults to 127.0.0.1:8000)
    --log-level       Python logging level (defaults to INFO)
    --check           Boot the server, hit /healthz once, print the status, exit
&quot;&quot;&quot;

from __future__ import annotations

import argparse
import http.client
import json
import logging
import signal
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import jsonschema

try:  # pragma: no cover - import style depends on execution context
    from cache import DecisionCache
except ImportError:  # pragma: no cover
    from .cache import DecisionCache  # type: ignore

LOGGER = logging.getLogger(&quot;decider.server&quot;)

STUB_RESPONSES: Dict[str, Dict[str, Any]] = {
    &quot;/decide/firm&quot;: {
        &quot;direction&quot;: &quot;hold&quot;,
        &quot;price_step&quot;: 0.0,
        &quot;expectation_bias&quot;: 0.0,
        &quot;explanation&quot;: &quot;stub: hold price; baseline heuristic&quot;
    },
    &quot;/decide/bank&quot;: {
        &quot;approve&quot;: True,
        &quot;credit_limit_ratio&quot;: 1.0,
        &quot;spread_bps&quot;: 150,
        &quot;explanation&quot;: &quot;stub: approve with default spread&quot;
    },
    &quot;/decide/wage&quot;: {
        &quot;direction&quot;: &quot;hold&quot;,
        &quot;wage_step&quot;: 0.0,
        &quot;explanation&quot;: &quot;stub: no wage adjustment&quot;
    },
}

BATCH_ENDPOINTS: Dict[str, str] = {
    &quot;/firm.decide.batch&quot;: &quot;/decide/firm&quot;,
    &quot;/bank.decide.batch&quot;: &quot;/decide/bank&quot;,
    &quot;/wage.decide.batch&quot;: &quot;/decide/wage&quot;,
}

BATCH_MAX_ITEMS = 16

SCHEMA_DIR = Path(__file__).with_name(&quot;schemas&quot;)
SCHEMA_FILES = {
    &quot;/decide/firm&quot;: &quot;firm_request.schema.json&quot;,
    &quot;/decide/bank&quot;: &quot;bank_request.schema.json&quot;,
    &quot;/decide/wage&quot;: &quot;wage_request.schema.json&quot;,
}


def _load_validators() -&gt; Dict[str, jsonschema.Draft7Validator]:
    validators: Dict[str, jsonschema.Draft7Validator] = {}
    for endpoint, filename in SCHEMA_FILES.items():
        schema_path = SCHEMA_DIR / filename
        with open(schema_path, &quot;r&quot;) as handle:
            schema = json.load(handle)
        validators[endpoint] = jsonschema.Draft7Validator(schema)
    return validators


VALIDATORS = _load_validators()
CACHE = DecisionCache()


class TickBudgetTracker:
    &quot;&quot;&quot;Track per-tick call budgets in a thread-safe manner.&quot;&quot;&quot;

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self._counts: Dict[Tuple[int, int], int] = {}
        self._lock = threading.Lock()

    def register(self, run_id: int, tick: int) -&gt; Tuple[bool, int]:
        &quot;&quot;&quot;Record a call for ``(run_id, tick)`` and return allowance status.

        Returns a tuple ``(allowed, count)`` where ``count`` is the recorded
        number of calls for the pair *after* the increment. When the budget is
        disabled (``max_calls &lt;= 0``) the method short-circuits and reports
        success.
        &quot;&quot;&quot;

        if self.max_calls &lt;= 0:
            return True, 0

        key = (run_id, tick)
        with self._lock:
            count = self._counts.get(key, 0)
            if count &gt;= self.max_calls:
                return False, count
            count += 1
            self._counts[key] = count
            return True, count


def parse_args() -&gt; argparse.Namespace:
    parser = argparse.ArgumentParser(description=&quot;Local Decider stub server&quot;)
    parser.add_argument(&quot;--host&quot;, default=&quot;127.0.0.1&quot;, help=&quot;Bind host (default: 127.0.0.1)&quot;)
    parser.add_argument(&quot;--port&quot;, type=int, default=8000, help=&quot;Bind port (default: 8000)&quot;)
    parser.add_argument(
        &quot;--log-level&quot;,
        default=&quot;INFO&quot;,
        choices=[&quot;CRITICAL&quot;, &quot;ERROR&quot;, &quot;WARNING&quot;, &quot;INFO&quot;, &quot;DEBUG&quot;],
        help=&quot;Logging verbosity&quot;
    )
    parser.add_argument(
        &quot;--stub&quot;,
        action=&quot;store_true&quot;,
        help=&quot;Serve deterministic stub responses (default behaviour).&quot;
    )
    parser.add_argument(
        &quot;--deadline-ms&quot;,
        type=int,
        default=200,
        help=&quot;Per-request deadline in milliseconds (&lt;=0 disables the check).&quot;
    )
    parser.add_argument(
        &quot;--tick-budget&quot;,
        type=int,
        default=0,
        help=&quot;Maximum calls allowed per run/tick pair (0 disables the budget).&quot;
    )
    parser.add_argument(
        &quot;--stub-delay-ms&quot;,
        type=int,
        default=0,
        help=&quot;Testing helper: add artificial latency to stub replies (milliseconds).&quot;
    )
    parser.add_argument(
        &quot;--check&quot;,
        action=&quot;store_true&quot;,
        help=&quot;Run a one-shot health check and exit.&quot;
    )
    args = parser.parse_args()</code></pre>

## Writing Checklist

- [ ] Introduce the bridge architecture and reference the Decider stub start command (`python3 tools/decider/server.py --stub`).
- [ ] Document the tuple return contract `(decision, error)` and enumerate `error['reason']` values (timeout, connection_error, http_error, decode_error, unexpected_error).
- [ ] Explain how each agent logs fallback reasons and reverts to baseline heuristics; cite guard caps (price/wage 0.04) and spread clamps.
- [ ] Clarify logging/telemetry: `[LLM block] fallback... ` messages, `timing.log`, and how upcoming instrumentation can hook into those counters.
- [ ] Close with guidance for future milestones (e.g., guard presets `tight`/`loose`, batch endpoints not yet enabled).

After drafting, run `quarto render docs` (executors will handle integration) and signal the artifact path in the issue comment.
