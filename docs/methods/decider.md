---
title: "Decider Stub Server"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

This page describes the local **Decider** stub used during Milestone M1. The Python 3 server runs on localhost and returns deterministic placeholder decisions for the firm, bank, and wage endpoints while enforcing request validation via JSON Schemas.

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

## Stub decision endpoints

The stub mode implements three deterministic `POST` routes. Each endpoint expects a JSON payload that matches the schema stored under `tools/decider/schemas_*.json`. The schemas only require the fields we know the Py2 simulation can emit (for example `firm_id`, `tick`, the baseline numeric decision, and the guard bounds when available). When a payload is malformed the server replies with **HTTP 400** plus a list of validation errors.

| Endpoint | Description | Example response |
| --- | --- | --- |
| `POST /decide/firm` | Firm pricing & expectations decision | `{ "direction": "hold", "price_step": 0.0, "expectation_bias": 0.0, "explanation": "stub: hold price; baseline heuristic" }` |
| `POST /decide/bank` | Bank loan approval & spread | `{ "approve": true, "credit_limit_ratio": 1.0, "spread_bps": 150, "explanation": "stub: approve with default spread" }` |
| `POST /decide/wage` | Worker reservation / firm wage offer | `{ "direction": "hold", "wage_step": 0.0, "explanation": "stub: no wage adjustment" }` |

Example call (firm endpoint):

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "demo-001",
    "tick": 42,
    "firm_id": 7,
    "state": {
      "price": 1.05,
      "unit_cost": 0.98,
      "inventory": 120,
      "backlog": 4
    },
    "bounds": {
      "price_step_min": 0.0,
      "price_step_max": 0.04,
      "expectation_bias_min": -0.1,
      "expectation_bias_max": 0.1,
      "price_floor": 0.95
    },
    "baseline": {
      "direction": "hold",
      "price_step": 0.0,
      "expectation_bias": 0.0
    }
  }' \
  http://127.0.0.1:8000/decide/firm
```

_Response (line-wrapped for readability):_

```json
{"direction": "hold", "price_step": 0.0, "expectation_bias": 0.0, "explanation": "stub: hold price; baseline heuristic"}
```

### Schema validation & friendly errors

Missing or mistyped fields trigger a structured error. Example (payload omits `firm_id`):

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"request_id": "oops", "tick": 2, "state": {}, "bounds": {}, "baseline": {}}' \
  http://127.0.0.1:8000/decide/firm | jq
```

```json
{
  "error": "invalid_payload",
  "messages": [
    "payload.firm_id is required",
    "payload.state.price is required",
    "payload.state.unit_cost is required",
    "payload.state.inventory is required",
    "payload.state.backlog is required",
    "payload.bounds.price_step_min is required",
    "payload.bounds.price_step_max is required",
    "payload.bounds.expectation_bias_min is required",
    "payload.bounds.expectation_bias_max is required",
    "payload.bounds.price_floor is required",
    "payload.baseline.direction is required",
    "payload.baseline.price_step is required",
    "payload.baseline.expectation_bias is required"
  ]
}
```

## Roadmap

Upcoming M1 issues extend this stub:

1. **M1-02 (Schemas):** JSON schema validation and friendly error messages.
2. **M1-03 (Cache):** Deterministic cache keyed by state hash.
3. **M1-04 (Timeout/Budget):** Server-side deadline and per-tick call budget enforcement.

Each addition will update this page so the quickstart in `AGENTS.md` always points to accurate instructions.
