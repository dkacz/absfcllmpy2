---
title: "Python 2 HTTP client"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

This page documents the **Python 2** client that calls the local Decider service. The legacy Caiani simulation stays in Python 2, so we ship a thin wrapper around ``urllib2`` that knows how to talk to the Python 3 server, parse JSON, and signal when the caller should fall back to the baseline heuristic.

## Quickstart

```python
from code.llm_bridge_client import LLMBridgeClient

client = LLMBridgeClient("http://127.0.0.1:8000", timeout=0.2)
state = {"inventory": 120, "backlog": 6}

decision, error = client.decide_firm(state)
if decision is None:
    # Baseline fallback path: log the reason, keep legacy heuristic.
    LOGGER.warning("firm LLM fallback: %s", error)
    apply_baseline_firm_rule(state)
else:
    apply_llm_firm_rule(decision)
```

- The client normalises the base URL (trims trailing slashes) and sets the ``Content-Type: application/json`` header for every request.
- ``timeout`` defaults to ``0.2`` seconds (200 ms) to match the M1 run logistics agreement. Pass ``None`` to use the ``urllib2`` global default.
- Every call returns ``(decision_dict, error_info)``. When ``decision_dict`` is ``None`` you *must* fall back to the legacy baseline rule.

## Available helpers

| Method | Endpoint | Notes |
| --- | --- | --- |
| ``decide_firm(payload)`` | ``POST /decide/firm`` | Pricing & expectations decision |
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
payload = {"leverage": 3.2, "credit_request": 100.0}
decision, error = client.decide_bank(payload)
if decision is None:
    # Tell the logs that we hit the fallback path.
    LOGGER.info("bank LLM fallback (%s): %s", error['reason'], error.get('detail'))
    approve, spread = baseline_bank_decision(payload)
else:
    approve = decision.get("approve", False)
    spread = decision.get("spread_bps", 150)
```

The helper methods never raise on network failures so the simulation can keep running; only programmer errors (e.g., passing a non-dict payload) raise immediately.

## Local testing recipe

1. Start the Decider stub in another terminal:

   ```bash
   python3 tools/decider/server.py --stub
   ```

2. Run a short Python 2 REPL snippet:

   ```python
   >>> from code.llm_bridge_client import LLMBridgeClient
   >>> client = LLMBridgeClient("http://127.0.0.1:8000")
   >>> client.decide_wage({"unemployment": 0.04})
   ({'direction': 'hold', 'wage_step': 0.0, 'explanation': 'stub: no wage adjustment'}, None)
   ```

3. Stop the server and re-run the call to see the fallback output:

   ```python
   >>> client.decide_wage({"unemployment": 0.04})
   (None, {'reason': 'connection_error', 'detail': '[Errno 111] Connection refused'})
   ```

When you wire the client into the simulation, keep the tuples intact so the fallback logic can log the reason (timeout vs HTTP error vs invalid JSON) before applying the baseline heuristic.
