# Issue #151 · Writer Brief — Live Prompt Refresh (M6-LIVE)

## Mission
We need production-ready, roleplay-heavy prompts for the **firm**, **bank**, and **wage** live decision endpoints. The copy must lean into the agent’s persona, invoke the legacy heuristics the Caiani simulation already encodes, and instruct the LLM to stay inside the guardrails (price/spread/wage caps). Outputs must follow the structured JSON schemas below so the Decider can validate responses before applying guard clamps.

Deliver everything as Markdown snippets (ready to paste into the repo) plus a table that maps each `why` code to a short narrative gloss.

---

## Runtime context (Python 2 simulation + Python 3 Decider)
- The simulation calls the Decider with rich state payloads. If the LLM answer fails schema validation or violates guardrails, the agent falls back to its legacy heuristic.
- Guards are derived from `code/llm_runtime.py` presets (full file below).
- **Firms** use `max_price_step` 0.04 and `max_expectation_bias` 0.04; price cannot drop below the unit-cost floor `p >= w/φ`.
- **Banks** start with spread bounds 50–500 bps (`bank_guard_bounds` can tighten/loosen this window). Credit limit ratios must remain in `[0,1]`.
- **Wage** hooks clamp `wage_step` to ±0.04 (scaled by preset) and enforce wage floors.
- Live mode targets OpenRouter models with `temperature = 0`, strict deadlines (~200 ms), and deterministic caching. Prompts must make the LLM comfortable deferring to baseline heuristics when uncertain (`llm_uncertain`).

---

### Full guard preset source (`code/llm_runtime.py`)
```python
# -*- coding: utf-8 -*-
"""Shared LLM runtime context for the Python 2 simulation."""

from __future__ import absolute_import

try:
    from llm_bridge_client import LLMBridgeClient
except ImportError:  # pragma: no cover - package import fallback
    from .llm_bridge_client import LLMBridgeClient

_CONTEXT = {
    'parameter': None,
    'client': None,
    'counters': {},
}

_COUNTER_TEMPLATE = {
    'calls': 0,
    'fallbacks': 0,
    'timeouts': 0,
}

_GUARD_PRESET_FACTORS = {
    'baseline': 1.0,
    'tight': 0.5,
    'loose': 1.5,
}

_BANK_GUARD_EPSILON = {
    'baseline': 1e-6,
    'tight': 0.0,
    'loose': 1e-6,
}


def configure(parameter):
    """Register the active ``Parameter`` instance for downstream hooks."""

    _CONTEXT['parameter'] = parameter
    _CONTEXT['client'] = None
    _CONTEXT['counters'] = {}


def get_parameter():
    return _CONTEXT.get('parameter')


def get_client():
    parameter = get_parameter()
    if not parameter:
        return None
    client = _CONTEXT.get('client')
    if client is None:
        timeout = parameter.llm_timeout_ms or 0
        timeout = float(timeout) / 1000.0
        client = LLMBridgeClient(parameter.llm_server_url, timeout=timeout)
        _CONTEXT['client'] = client
    return client


def firm_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_firm_pricing)


def bank_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_bank_credit)


def wage_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_wage)


def log_fallback(block, reason, detail=None):
    _register_fallback(block, reason)
    message = '[LLM %s] fallback: %s' % (block, reason)
    if detail:
        message = message + ' (%s)' % detail
    print message


def log_llm_call(block):
    _ensure_block_counter(block)['calls'] += 1


def reset_counters(block=None):
    if block is None:
        _CONTEXT['counters'] = {}
        return
    counters = _CONTEXT.get('counters')
    if counters is None:
        _CONTEXT['counters'] = {}
        counters = _CONTEXT['counters']
    counters[str(block)] = _COUNTER_TEMPLATE.copy()


def ensure_counter(block):
    return _ensure_block_counter(block)


def get_counters_snapshot():
    counters = _CONTEXT.get('counters') or {}
    snapshot = {}
    for block, values in counters.items():
        if values is None:
            continue
        snapshot[block] = values.copy()
    return snapshot


def get_firm_guard_caps():
    """Return effective guard caps for firm price/expectation decisions."""

    parameter = get_parameter()
    if parameter:
        custom = getattr(parameter, 'firm_guard_caps', None)
        if isinstance(custom, dict):
            return _sanitise_firm_caps(custom)

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'firm_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)
    base = {
        'max_price_step': 0.04,
        'max_expectation_bias': 0.04,
    }
    return _scale_caps(base, factor)


def get_wage_guard_caps():
    """Return guard caps for wage decisions shared by workers and firms."""

    parameter = get_parameter()

    if parameter:
        custom = getattr(parameter, 'wage_guard_caps', None)
        if isinstance(custom, dict):
            return _sanitise_wage_caps(custom, parameter)

    base_delta = _default_wage_delta(parameter)

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'wage_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)

    return {
        'max_wage_step': base_delta * factor,
    }


def get_bank_guard_config():
    """Return spread guard bounds (bps) and epsilon."""

    base_min = 50.0
    base_max = 500.0
    parameter = get_parameter()

    if parameter:
        custom_bounds = getattr(parameter, 'bank_guard_bounds', None)
        bounds = _sanitise_bank_bounds(custom_bounds)
        if bounds is not None:
            base_min, base_max = bounds

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'bank_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)

    min_bps = base_min
    if preset == 'tight':
        min_bps = base_min + 50.0

    window = max(0.0, base_max - base_min)
    max_bps = min_bps + window * factor
    if max_bps < min_bps:
        max_bps = min_bps

    epsilon = _BANK_GUARD_EPSILON.get(preset, 1e-6)
    if parameter:
        custom_eps = getattr(parameter, 'bank_guard_epsilon', None)
        try:
            if custom_eps is not None:
                epsilon = max(0.0, float(custom_eps))
        except (TypeError, ValueError):
            pass

    return {
        'min_bps': min_bps,
        'max_bps': max_bps,
        'epsilon': epsilon,
    }


def _resolve_guard_preset(parameter, attribute):
    value = getattr(parameter, attribute, None)
    if value:
        return _normalise_preset(value)
    fallback = getattr(parameter, 'llm_guard_preset', None)
    if fallback:
        return _normalise_preset(fallback)
    return 'baseline'


def _normalise_preset(value):
    text = str(value).strip().lower()
    if text in _GUARD_PRESET_FACTORS:
        return text
    return 'baseline'


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
            'max_price_step': 0.04,
            'max_expectation_bias': 0.04,
        }

    caps = {}
    for key in ('max_price_step', 'max_expectation_bias'):
        value = custom.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric < 0.0:
            numeric = 0.0
        caps[key] = numeric
    if 'max_price_step' not in caps:
        caps['max_price_step'] = 0.04
    if 'max_expectation_bias' not in caps:
        caps['max_expectation_bias'] = 0.04
    return caps


def _sanitise_wage_caps(custom, parameter):
    base_delta = _default_wage_delta(parameter)

    if not isinstance(custom, dict):
        return {
            'max_wage_step': base_delta,
        }

    value = custom.get('max_wage_step')
    if value is None:
        return {
            'max_wage_step': base_delta,
        }

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = base_delta

    if numeric < 0.0:
        numeric = 0.0

    return {
        'max_wage_step': numeric,
    }


def _default_wage_delta(parameter):
    base = 0.04
    if parameter:
        try:
            base = float(getattr(parameter, 'delta', base))
        except (TypeError, ValueError):
            base = 0.04
    if base < 0.0:
        base = 0.0
    return base


def _sanitise_bank_bounds(value):
    if not value:
        return None
    try:
        minimum, maximum = value
        minimum = float(minimum)
        maximum = float(maximum)
    except (TypeError, ValueError, IndexError):
        return None
    if minimum < 0.0:
        minimum = 0.0
    if maximum < 0.0:
        maximum = 0.0
    if maximum < minimum:
        minimum, maximum = maximum, minimum
    return (minimum, maximum)


def _ensure_block_counter(block):
    counters = _CONTEXT.get('counters')
    if counters is None:
        counters = {}
        _CONTEXT['counters'] = counters
    key = str(block)
    current = counters.get(key)
    if current is None:
        current = _COUNTER_TEMPLATE.copy()
        counters[key] = current
    return current


def _register_fallback(block, reason):
    counter = _ensure_block_counter(block)
    counter['fallbacks'] += 1
    if str(reason) == 'timeout':
        counter['timeouts'] += 1


__all__ = [
    'configure',
    'get_client',
    'get_parameter',
    'firm_enabled',
    'bank_enabled',
    'wage_enabled',
    'log_fallback',
    'log_llm_call',
    'reset_counters',
    'ensure_counter',
    'get_counters_snapshot',
    'get_firm_guard_caps',
    'get_wage_guard_caps',
    'get_bank_guard_config',
]
```
## Current prompt placeholders
These are the existing stubs the executor just shipped. They are serviceable but bland—your job is to replace them with persuasive copy that evokes real-world decision makers.

### Firm (tools/decider/prompts/firm_live.json)
```json
{
  "system": "You are the firm pricing strategist for the Caiani AB-SFC simulation. Always obey the guard rails supplied in the payload. Output ONLY valid JSON conforming to the provided schema. Never include prose outside JSON.",
  "user_template": "The simulation captured the following firm state, baseline heuristic, and guard limits (JSON):\n{payload_json}\n\nDecide whether to raise, hold, or cut the price. Honour max_price_step, expectation bias caps, and the price floor. Choose one or more why-codes that explain the move (see schema enum). Confidence should be a probability in [0,1]. Return JSON only.",
  "response_schema": "firm_live_response.schema.json"
}
```

### Bank (current default inside `server.py`, before your rewrite)
```text
System: You are the bank credit decision service for the Caiani AB-SFC model. Respond with JSON containing approve (boolean), credit_limit_ratio (number), spread_bps (number), and why_code (string summarising the choice).
User: Bank state, applicant metrics, and guard rails (JSON):
{payload_json}

Return JSON only.
```

### Wage (current default inside `server.py`)
```text
System: You are the wage negotiation decision service for the Caiani AB-SFC model. Return JSON with direction (string), wage_step (number), and why_code (string).
User: Worker and firm wage context (JSON):
{payload_json}

Return JSON only.
```

---

## Required output schemas
### Firm response schema (already live)
```json
{
  "direction": "raise" | "hold" | "cut",
  "price_step": number in [-0.04, 0.04],
  "expectation_bias": number in [-0.04, 0.04],
  "why": [ "baseline_guard" | "demand_softening" | "demand_spike" | "cost_push" | "credit_constraint" | "inventory_pressure" | "llm_uncertain" ],
  "confidence": number in [0, 1],
  "comment"?: string (≤280 chars)
}
```

### Bank response schema (executor will enforce after your rewrite)
```json
{
  "approve": boolean,
  "credit_limit_ratio": number in [0, 1],
  "spread_bps": number within guard window (typically 50–500 bps),
  "why": [ "baseline_guard" | "capital_buffer_low" | "capital_buffer_high" | "liquidity_pressure" | "borrower_risk" | "policy_rate_shift" | "llm_uncertain" ],
  "confidence": number in [0, 1],
  "comment"?: string (≤280 chars)
}
```

### Wage response schema (target spec — executor will implement after your copy lands)
```json
{
  "direction": "raise" | "hold" | "cut",
  "wage_step": number in [-0.04, 0.04],
  "why": [ "baseline_guard" | "inflation_pressure" | "productivity_gap" | "labour_shortage" | "unemployment_pressure" | "llm_uncertain" ],
  "confidence": number in [0, 1],
  "comment"?: string (≤280 chars)
}
```

---

## Expectations for your rewrite
1. **Role-play the persona.** Make the system prompts sound like a veteran **pricing strategist**, **credit officer**, or **labour negotiator** who knows the Caiani model. Encourage the LLM to surface implicit heuristics (“what would a cautious central banker do?”).
2. **Reinforce guardrails.** Remind the model to stay within caps, honour price floors, and respect spread bounds. Encourage it to *decline* or defer when unsure (`llm_uncertain`).
3. **Baseline heuristics awareness.** Mention legacy logic (e.g., exponential approval decay with leverage, markup rules, collective bargaining inertia) so the LLM can align with expected behaviours.
4. **Why-code storytelling.** Provide cues for each enum so the generated `why` array acts as an interpretable rationale. Draft a rationale table with glosses.
5. **Structured output only.** Reiterate “respond with JSON only” and emphasise schema compliance.
6. **Latent heuristics nod.** Reference that the LLM has absorbed macro-finance playbooks during training—prompt it to channel that expertise while respecting constraints.

---

## Deliverables (Markdown)
1. **Prompts section** — For each endpoint, supply a `text`-fenced code block with the final system + user prompts.
2. **Why-code rationale table** — Columns: `Endpoint`, `Why Code`, `Human Gloss`, `When to use` (1–2 sentences). Cover all enums listed above.
3. **Assumptions / open questions** (optional) — Flag anything needing executor confirmation.

Post everything as a single Markdown comment on Issue #151. No repo access or code changes required.

---

## Additional references (full text)
### `docs/methods/fallbacks.qmd`
```markdown
---
title: "Baseline vs LLM Fallback Semantics"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 3
---

# Baseline vs LLM Fallback Semantics {#sec-fallbacks}

This page explains how the Python 2 Caiani simulation decides whether to keep a Large Language Model (LLM) suggestion or revert to the legacy baseline heuristics. The same guardrails that protect stock-flow consistency also ensure the bridge remains a drop-in augmentation: whenever the LLM is unavailable, slow, or proposes an invalid adjustment, the baseline path continues to drive the simulation.

## Bridge architecture

- **Processes.** The simulation runs in Python 2, while the Decider service is a Python 3 microservice. The thin bridge client in `code/llm_bridge_client.py` serialises agent state to JSON, posts it to the Decider, and returns a `(decision, error)` tuple to the caller.
- **Toggles.** The `Parameter` object (`code/parameter.py`) controls whether each block (firm, bank, wage) delegates to the LLM. All `use_llm_*` flags default to `False`, so the model behaves exactly like the baseline until an experiment enables them.
- **Stub service.** During development the Decider runs in stub mode:

```bash
python3 tools/decider/server.py --stub
```

  The stub enforces per-request deadlines, schema validation, and optional call budgets so we can test failure paths deterministically.

## Configuration and timeouts

`code/llm_runtime.py` initialises the shared bridge client using the configured server URL (default `http://127.0.0.1:8000`) and converts `llm_timeout_ms` into seconds. The default timeout is 200 ms, matching the Milestone M1 agreement. When a request exceeds the deadline, `LLMBridgeClient` returns `(None, {"reason": "timeout", ...})`, the agent logs the fallback, and baseline heuristics execute for that tick. Other runtime knobs, such as guard presets, are also resolved here so they remain consistent across agents.

## Guardrails and presets

Guardrails ensure LLM suggestions remain inside the stock-flow safe region before state updates occur.

- **Firms.** Price moves are capped by `max_price_step` (default 0.04) and expectation bias by `max_expectation_bias` (default 0.04). Every decision is checked against the unit-cost floor `p >= w/phi`.
- **Banks.** Spread decisions are clamped between minimum and maximum basis points; credit limits cannot exceed either the loan request or the bank-specific limit.
- **Wages.** Wage steps share the 0.04 cap.

Guard presets (`llm_guard_preset`, `firm_guard_preset`, etc.) scale those caps: `baseline` keeps the defaults (1.0x), `tight` halves them, and `loose` applies a 1.5x factor. Even when a decision survives validation, guard clamps may still trim it to the safe region; the agent records that trim and continues.

## Fallback pipeline

Agent hooks follow the same decision tree for every LLM call. The code excerpts in `code/firm.py` and `code/bank.py` show the pattern.

1. **LLM disabled or client unavailable.** If the relevant `use_llm_*` flag is off, or if `get_client()` cannot create a bridge client, the hook logs `client_unavailable` and applies the baseline result computed earlier in the tick.
2. **Feature packing errors.** Payload builders (for example `Firm._build_llm_payload`) refuse to call the Decider if required inputs are missing or non-finite. The hook logs `feature_pack_missing` and keeps the baseline.
3. **Network and transport errors.** `LLMBridgeClient._post_json` catches timeouts, connection failures, HTTP status codes other than 200, JSON decode errors, and any other exception. Each error becomes a tuple `(None, error_dict)` that includes a `reason` key. The hook logs the reason and runs the baseline logic.
4. **Invalid response schema.** After a successful request, the agent validates the response (e.g., `Bank._validate_llm_decision`). If the schema check fails (missing keys, wrong types)-the hook logs `invalid_response` and applies the baseline values.
5. **Guard clamps.** When the decision is valid but exceeds guard caps, the hook clamps the values, logs the specific clamp (e.g., `price_step_clamped`), and proceeds with the guarded version.

### Error reasons returned by the bridge client

| Reason | Description |
| --- | --- |
| `timeout` | Request exceeded `llm_timeout_ms`; common when the server or LLM is slow. |
| `connection_error` | Network failure establishing the connection (server offline, refused). |
| `http_error` | Decider returned a non-200 status (e.g., schema rejection, tick-budget enforcement). |
| `decode_error` | Response body could not be parsed as JSON. |
| `unexpected_error` | Catch-all for any other exception during the request lifecycle. |

## Logging and telemetry

`code/llm_runtime.py` exposes `log_fallback(block, reason, detail=None)`, which prints standardized messages such as:

```
[LLM firm] fallback: timeout (request to http://127.0.0.1:8000/decide/firm exceeded the configured timeout)
[LLM bank] fallback: invalid_response
```

These messages give test harnesses and notebooks a lightweight way to count fallbacks. Agents such as the bank also persist structured state (`_llm_bank_last_decision`) so downstream analysis can tell whether the LLM was applied (`used_llm`) and why a fallback occurred (`fallback_reason`). Additionally, every simulation run appends the active toggle configuration to `timing.log`, making it easy to reconstruct the execution context for each artifact.

## Testing the fallback paths

The Decider stub exposes switches that let you exercise each fallback without touching production code:

1. **Connection errors.** Do not start the stub and run a short simulation. Every LLM call produces a `connection_error` fallback.
2. **Timeouts.** Add artificial latency greater than the configured timeout:

   ```bash
   python3 tools/decider/server.py --stub --stub-delay-ms 300
   ```

   The client reports `timeout`, and the simulation keeps the baseline decision.

3. **Tick budgets and HTTP errors.** Start the stub with a per-tick budget:

   ```bash
   python3 tools/decider/server.py --stub --tick-budget 5
   ```

   Additional calls in the same `(run_id, tick)` pair receive HTTP 503 responses, which the client reports as `http_error` fallbacks.

4. **Schema violations.** Edit the stub to return an invalid field (for example, drop `approve` from the bank decision). The agent logs `invalid_response` and reverts to baseline.

Follow the smoke-run and A/B demo commands in `docs/repro_manual.qmd` to regenerate artifacts after each test. Finish by running `quarto render docs` so the new page and logs appear in the rendered site.
```
### `docs/methods/decider.md`
```markdown
---
title: "Decider Stub Server"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

This page describes the local **Decider** stub used during Milestone M1. The Python 3 server runs on localhost and returns deterministic placeholder decisions for the firm, bank, and wage endpoints. All request payloads are validated against JSON Schemas before the stub replies so we can catch malformed inputs early.

## Start the server

Run the server from the repository root:

```bash
python3 tools/decider/server.py --stub
```

- Default bind: `127.0.0.1:8000`. Override with `--host` / `--port` if needed.
- The process logs requests to stdout. Leave it running while the Python 2 simulation calls it.
- To verify the binary without keeping it alive, add `--check` (starts the server in the background, hits `/healthz`, prints the result, and exits):

```bash
python3 tools/decider/server.py --stub --check
```

Additional flags relevant for later milestones:

- `--deadline-ms <int>` — per-request deadline (defaults to **200 ms**; use `<=0` to disable).
- `--tick-budget <int>` — maximum calls allowed per `(run_id, tick)` pair (defaults to unlimited).
- `--stub-delay-ms <int>` — testing helper that adds artificial latency to stub replies so you can exercise timeout behaviour.

### Live mode (OpenRouter)

Milestone M6 introduces a live mode that routes the same endpoints through OpenRouter:

```bash
OPENROUTER_API_KEY=sk-... \
python3 tools/decider/server.py \
  --mode live \
  --openrouter-model-primary openrouter/your-model \
  --openrouter-model-fallback openrouter/backup-model
```

- `--mode live` switches the handler to the OpenRouter adapter; the default remains `stub` so accidental runs stay cost-free.
- Provide the primary model slug via the flag or the `OPENROUTER_MODEL_PRIMARY` environment variable. The fallback slug is optional but recommended.
- The server verifies both slugs with `/api/v1/models` on startup and logs the selected provider, prompt/response token counts, elapsed time, and any `why_code` the model returns.
- Live requests honour the same `--deadline-ms` budget; the adapter subtracts a small buffer before calling OpenRouter so the overall request still respects the server deadline. Any timeout or schema violation is surfaced back to the simulation as an HTTP error, triggering the baseline fallback path.

> **Guardrail:** keep the stub workflow for day-to-day smoke tests. Only start live mode when you explicitly want to hit OpenRouter and have confirmed your API key, model slugs, and run budget.

## Health endpoint

```bash
curl -s http://127.0.0.1:8000/healthz | jq
```

Expected response:

```json
{
  "status": "ok"
}
```

## Request schemas & stub decision endpoints

Each endpoint validates its request against the schema stored under `tools/decider/schemas/`. The same files will be consumed by the Python 2 caller (for tests) and documented in the manuscript appendix.

| Endpoint | Schema file | Description |
| --- | --- | --- |
| `POST /decide/firm` | `tools/decider/schemas/firm_request.schema.json` | Firm pricing & expectations decision |
| `POST /decide/bank` | `tools/decider/schemas/bank_request.schema.json` | Bank loan approval & spread |
| `POST /decide/wage` | `tools/decider/schemas/wage_request.schema.json` | Worker reservation / firm wage offer |

> **Tip** — start from the schema when constructing payloads; the stub ignores the contents beyond validation, but the live Decider will rely on the same structure.

| Endpoint | Description | Example response |
| --- | --- | --- |
| `POST /decide/firm` | Firm pricing & expectations decision | `{ "direction": "hold", "price_step": 0.0, "expectation_bias": 0.0, "explanation": "stub: hold price; baseline heuristic" }` |
| `POST /decide/bank` | Bank loan approval & spread | `{ "approve": true, "credit_limit_ratio": 1.0, "spread_bps": 150, "explanation": "stub: approve with default spread" }` |
| `POST /decide/wage` | Worker reservation / firm wage offer | `{ "direction": "hold", "wage_step": 0.0, "explanation": "stub: no wage adjustment" }` |

### Example: firm request

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "schema_version": "1.0",
        "run_id": 0,
        "tick": 0,
        "country_id": 0,
        "firm_id": "F0n0",
        "price": 1.05,
        "unit_cost": 1.0,
        "inventory": 2.5,
        "inventory_value": 2.5,
        "production_effective": 3.0,
        "baseline": {
          "price": 1.05,
          "expected_demand": 3.2,
          "producing": 2.8
        },
        "guards": {
          "max_price_step": 0.04,
          "max_expectation_bias": 0.04,
          "price_floor": 1.0
        }
      }' \
  http://127.0.0.1:8000/decide/firm | jq
```

### Friendly validation errors

Malformed payloads return HTTP 400 with a short list of failing paths. Example (trimmed) response:

```bash
curl -s -X POST -H "Content-Type: application/json" -d '{}' \
  http://127.0.0.1:8000/decide/firm | jq
```

```json
{
  "error": "invalid_request",
  "detail": [
    { "path": ["baseline"], "message": "'baseline' is a required property" },
    { "path": ["guards"], "message": "'guards' is a required property" }
  ]
}
```

## Deterministic cache

- Module: `tools/decider/cache.py`
- Key = SHA‐256 of `{endpoint, payload, temperature=0.0}` (the server refuses any other temperature so cached decisions stay deterministic).
- Responses are deep-copied on the way in/out so callers cannot mutate the stored values.
- Log lines show hits and misses, for example:

  ```text
  INFO cache hit /decide/firm key=4f6c5a2b
  ```

  The `key` prefix (first 8 hex chars) is enough to correlate with logs when debugging.

On every request the server checks the cache before generating a response. The first call produces a `cache miss …` debug entry; subsequent identical requests (same endpoint + payload) reuse the cached payload and skip the downstream call. Clearing the cache is as simple as restarting the stub (later milestones will expose an explicit CLI flag when live mode ships).

## Deadline & per-tick budget safeguards

The stub enforces two guardrails so the live Decider cannot starve the Python 2 simulation:

1. **Per-request deadline.** When `--deadline-ms` is positive, the handler returns HTTP 504 with code `{ "error": "deadline_exceeded" }` once the elapsed time crosses that bound. Use `--stub-delay-ms` to simulate slow replies during testing:

   ```bash
   # Terminal A — run the stub with a 10 ms deadline and a 20 ms artificial delay
   python3 tools/decider/server.py --stub --port 8200 --deadline-ms 10 --stub-delay-ms 20
   ```

   ```bash
   # Terminal B — trigger the timeout with a firm request
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{
           "schema_version": "1.0",
           "run_id": 0,
           "tick": 0,
           "country_id": 0,
           "firm_id": "F0n0",
           "price": 1.0,
           "unit_cost": 1.0,
           "inventory": 0,
           "inventory_value": 0,
           "production_effective": 0,
           "production_capacity": 10.0,
           "sales_last_period": 0,
           "loan_demand": 0,
           "loan_received": 0,
           "net_worth": 10,
           "expected_wage": 1.0,
           "markup": 0.0,
           "min_markup": 0.0,
           "guards": {
             "max_price_step": 0.04,
             "max_expectation_bias": 0.04,
             "price_floor": 1.0
           }
         }' \
     http://127.0.0.1:8200/decide/firm | jq
   ```

   Example response:

   ```json
   {
     "error": "deadline_exceeded",
     "detail": { "elapsed_ms": 21, "deadline_ms": 10 }
   }
   ```

2. **Per-tick call budget.** When `--tick-budget` is greater than zero, the server tracks how many calls arrive for each `(run_id, tick)` pair and stops accepting new ones after the limit is reached. The over-budget request receives HTTP 429 with code `{ "error": "tick_budget_exceeded" }`:

   ```bash
   # Terminal A — limit to one call per tick
   python3 tools/decider/server.py --stub --port 8200 --tick-budget 1
   ```

   ```bash
   # Terminal B — first call succeeds, second call exceeds the budget
   # (payload.json contains the firm request JSON from the example above)
   curl -s -X POST -H "Content-Type: application/json" -d @payload.json \
     http://127.0.0.1:8200/decide/firm > /dev/null
   curl -s -X POST -H "Content-Type: application/json" -d @payload.json \
     -o - -w "\nstatus=%{http_code}\n" http://127.0.0.1:8200/decide/firm
   ```

   Example body (status `429`):

   ```json
   {
     "error": "tick_budget_exceeded",
     "detail": { "run_id": 0, "tick": 0, "limit": 1, "observed": 1 }
   }
   ```

Resetting the stub (Ctrl+C then relaunch) clears the per-tick counters and the deterministic cache.

## Batch decision endpoints

When you need to amortise HTTP overhead, the stub exposes three batch routes that mirror the single-call endpoints:

| Batch endpoint | Underlying single endpoint |
| --- | --- |
| `POST /firm.decide.batch` | `POST /decide/firm` |
| `POST /bank.decide.batch` | `POST /decide/bank` |
| `POST /wage.decide.batch` | `POST /decide/wage` |

Constraints and behaviour:

- Maximum **16** items per request; anything larger returns HTTP 400 (`batch_limit_exceeded`).
- Payload schema is the same as the single-call version; the server validates every entry and stops on the first failure.
- Deadlines and tick budgets apply to each item; if a single call would have timed out or tripped the budget, the batch returns the corresponding 504/429 with the failing index noted.
- Responses reuse the deterministic cache, so repeated batches with the same payloads stay fast.

Example: batch firm request (two items) and response

```bash
cat > firm_batch.json <<'JSON'
{
  "requests": [
    {
      "schema_version": "1.0",
      "run_id": 0,
      "tick": 0,
      "country_id": 0,
      "firm_id": "F0n0",
      "price": 1.0,
      "unit_cost": 1.0,
      "inventory": 0,
      "inventory_value": 0,
      "production_effective": 0,
      "production_capacity": 10.0,
      "sales_last_period": 0,
      "loan_demand": 0,
      "loan_received": 0,
      "net_worth": 10,
      "expected_wage": 1.0,
      "markup": 0.0,
      "min_markup": 0.0,
      "baseline": {
        "price": 1.0,
        "expected_demand": 0.0
      },
      "guards": {
        "max_price_step": 0.04,
        "max_expectation_bias": 0.04,
        "price_floor": 1.0
      }
    },
    {
      "schema_version": "1.0",
      "run_id": 0,
      "tick": 0,
      "country_id": 0,
      "firm_id": "F0n1",
      "price": 1.1,
      "unit_cost": 1.0,
      "inventory": 2.0,
      "inventory_value": 2.2,
      "production_effective": 1.0,
      "production_capacity": 9.5,
      "sales_last_period": 0.8,
      "loan_demand": 0,
      "loan_received": 0,
      "net_worth": 11,
      "expected_wage": 1.0,
      "markup": 0.1,
      "min_markup": 0.0,
      "baseline": {
        "price": 1.05,
        "expected_demand": 0.9
      },
      "guards": {
        "max_price_step": 0.04,
        "max_expectation_bias": 0.04,
        "price_floor": 1.0
      }
    }
  ]
}
JSON

curl -s -X POST -H "Content-Type: application/json" \
  --data @firm_batch.json \
  http://127.0.0.1:8000/firm.decide.batch | python3 -m json.tool
```

Expected response:

```json
{
  "count": 2,
  "results": [
    {
      "direction": "hold",
      "expectation_bias": 0.0,
      "explanation": "stub: hold price; baseline heuristic",
      "price_step": 0.0
    },
    {
      "direction": "hold",
      "expectation_bias": 0.0,
      "explanation": "stub: hold price; baseline heuristic",
      "price_step": 0.0
    }
  ]
}
```

Errors bubble up with the index of the failing entry; for example, exceeding the 16-item limit returns:

```json
{
  "error": "batch_limit_exceeded",
  "detail": { "limit": 16, "observed": 17 }
}
```

## Roadmap

With schemas in place, upcoming M1 issues extend this stub as follows:

1. **M1-02 (Schemas):** JSON schema validation and friendly error messages.
2. **M1-03 (Cache):** Deterministic cache keyed by state hash.
3. **M1-04 (Timeout/Budget):** Server-side deadline and per-tick call budget enforcement.

Each addition will update this page so the quickstart in `AGENTS.md` always points to accurate instructions.
```
