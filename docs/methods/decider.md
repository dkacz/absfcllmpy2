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

## Roadmap

With schemas in place, upcoming M1 issues extend this stub as follows:

1. **M1-02 (Schemas):** JSON schema validation and friendly error messages.
2. **M1-03 (Cache):** Deterministic cache keyed by state hash.
3. **M1-04 (Timeout/Budget):** Server-side deadline and per-tick call budget enforcement.

Each addition will update this page so the quickstart in `AGENTS.md` always points to accurate instructions.
