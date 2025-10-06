---
title: "Decider Live Mode (OpenRouter)"
date: last-modified
format:
  html:
    toc: true
    toc-depth: 2
---

This page documents the Milestone **M6 live mode** for the Decider server. The Python 3 service can now proxy firm, bank, and wage decisions through the [OpenRouter](https://openrouter.ai/) Chat Completions API while preserving the guardrails, fallback ladder, and telemetry needed by the legacy Caiani simulation.

## Quickstart

```bash
# Minimal invocation (assumes OPENROUTER_API_KEY is exported)
python3 tools/decider/server.py \
  --mode live \
  --openrouter-model-primary openrouter/openai/gpt-5-nano \
  --openrouter-model-fallback openrouter/google/gemini-2.5-flash-lite
```

- `--mode live` switches from deterministic stub replies to the OpenRouter adapter (default remains `stub`).
- Provide the primary slug through `--openrouter-model-primary` or `OPENROUTER_MODEL_PRIMARY`; the fallback slug is optional but strongly recommended.
- Additional headers are picked up from the environment: `OPENROUTER_HTTP_REFERER` and `OPENROUTER_TITLE` are forwarded to satisfy OpenRouter’s usage policy.
- The server verifies both slugs using `GET https://openrouter.ai/api/v1/models` on boot. If a slug is missing the server exits with a `model_not_found` error.
- On startup the server issues a `GET https://openrouter.ai/api/v1/key` call and logs the remaining credits/limits. Disable it with `--skip-openrouter-credit-check` or `OPENROUTER_SKIP_CREDIT_PREFLIGHT=1`.
- Run with `--deadline-ms` (default 200 ms) to cap per-request latency. The adapter subtracts a small buffer before calling OpenRouter so the overall request still honours the server deadline.

## Authentication & Headers

| Purpose | Env var / flag | Notes |
| --- | --- | --- |
| API key | `OPENROUTER_API_KEY` | Required. Loaded automatically by `OpenRouterAdapter`; missing key raises on startup. |
| Primary model | `--openrouter-model-primary` / `OPENROUTER_MODEL_PRIMARY` | Mandatory in live mode. |
| Fallback model | `--openrouter-model-fallback` / `OPENROUTER_MODEL_FALLBACK` | Optional secondary slug; retried once after a primary failure. |
| HTTP Referer | `OPENROUTER_HTTP_REFERER` | Optional; forwarded as `HTTP-Referer` header. |
| Request title | `OPENROUTER_TITLE` | Optional; forwarded as `X-Title`. |
| User-Agent | hard-coded `absfcllmpy2-decider` | Matches project telemetry. |
| Credit preflight opt-out | `--skip-openrouter-credit-check` / `OPENROUTER_SKIP_CREDIT_PREFLIGHT` | Skips the startup `GET /key` credit snapshot (enabled by default). |

All live calls hit `POST https://openrouter.ai/api/v1/chat/completions`. The adapter constructs:

```json
{
  "model": "<slug>",
  "temperature": 0.0,
  "messages": [
    {"role": "system", "content": "…"},
    {"role": "user", "content": "…"}
  ],
  "response_format": { ... },
  "seed": <optional>,
  "timeout": <derived from --deadline-ms>
}
```

## Prompt & Schema Catalogue

| Endpoint | Prompt source | Response schema | Key fields |
| --- | --- | --- | --- |
| `POST /decide/firm` | `tools/decider/prompts/firm_live.json` | `tools/decider/schemas/firm_live_response.schema.json` | `direction ∈ {raise, hold, cut}`, `price_step`, `expectation_bias`, `why[]`, `confidence`, optional `comment`. |
| `POST /decide/bank` | `tools/decider/prompts/bank_live.json` | `tools/decider/schemas/bank_live_response.schema.json` | `approve`, `credit_limit_ratio`, `spread_bps`, `why[]`, `confidence`, optional `comment`. |
| `POST /decide/wage` | `tools/decider/prompts/wage_live.json` | _(none — falls back to `json_object`)_ | `direction`, `wage_step`, `why[]`, `confidence`, optional `comment`. |

Each prompt keeps a fully in-character persona, leaning on the baseline heuristics while respecting hard clamps:

- **Firm:** pricing strategist honouring buffer-stock logic and unit-cost floors.
- **Bank:** senior credit officer enforcing monotonic risk pricing and a 50–500 bps spread corridor.
- **Wage:** national arbitrator bound by the wage accord and unemployment-sensitive bargaining weights.

The guardrails described in [Fallback Semantics](fallbacks.qmd) still apply — incoming decisions are validated against the schema, clamped, and rejected if any field violates the contract.

## Structured Outputs & Schema Detection

`OpenRouterAdapter` caches the `/models` response and records whether each slug advertises structured-output support. For every call the router:

1. Checks the cache (`supports_structured_outputs(slug)`).
2. If supported, requests `response_format={"type": "json_schema", …}` using the corresponding schema.
3. On HTTP 400/404/415/422 (or error bodies mentioning “schema/structured”), the adapter falls back to `{"type": "json_object"}` and records the slug as schema-unsupported.
4. Wage decisions always use `json_object` because there is no dedicated response schema.

## Timeout & Failover Ladder

Per endpoint request:

1. **Primary attempt:** call the primary slug with the configured response format. Structured mode is preferred when available.
2. **Structured fallback:** if the model rejects JSON Schema, retry immediately in `json_object` mode (no additional prompt cost).
3. **Model fallback:** on transport failures (`timeout`, `http_error`, etc.) retry once using the fallback slug (if provided).
4. **Baseline fallback:** when both models fail (or no fallback is configured) the server returns `503 llm_live_failed`. The Python 2 hooks log the reason and apply the baseline heuristic.

Test coverage (`tests/test_decider_server_live.py`) exercises all three branches: structured retries, primary→fallback recovery, and baseline fallback when both attempts fail.

## Telemetry & Logging

Every live attempt writes to `timing.log` in addition to the existing `[LLM block] counters` entries:

```
[LLM firm] usage run=17 tick=42 model=openrouter/primary attempt=primary mode=structured usage_prompt_tokens=905 usage_completion_tokens=58 elapsed_ms=121.4
[LLM firm] usage_error run=17 tick=42 model=openrouter/primary attempt=primary reason=timeout status=n/a usage_prompt_tokens=0 usage_completion_tokens=0 elapsed_ms=0.0
```

When the credit preflight is enabled, startup logs include an informational line summarising the remaining balance, for example:

```
INFO OpenRouter credit snapshot payload={"credits": 12.5, "limit_remaining": 90, "usage_remaining": 900} elapsed_ms=8.5
```

- `usage` lines appear on success and capture model slug, attempt label (`primary` or `fallback`), mode (`structured` vs `json`), token counts, and latency.
- `usage_error` lines are emitted for every failed attempt (timeouts, HTTP errors, schema violations) with zeroed token counts so log parsers can align failures with costs.
- These entries are appended from `LiveModeRouter._log_usage_line/_log_usage_error`; tests patch the log path to keep the format stable.

## Reproducibility Checklist

1. **Set credentials:** `export OPENROUTER_API_KEY=sk-...` and any optional headers (`OPENROUTER_HTTP_REFERER`, `OPENROUTER_TITLE`).
2. **Confirm model access:** `python3 tools/decider/server.py --mode live --openrouter-model-primary <slug> --check`. The run performs the `/models` lookup and emits the credit snapshot log (unless skipped).
3. **Run live mode:** keep the server running while the Python 2 simulation executes (`python2 code/timing.py`). Toggle the LLM flags in `code/parameter.py` as needed.
4. **Inspect telemetry:** open `timing.log` to correlate token usage, latency, and fallback reasons with simulation outputs.
5. **Automated tests:** `python3 -m unittest tests.test_decider_server_live` covers structured-output detection, primary/fallback retries, and baseline fallbacks.

Cross-reference the stub details in [Decider Stub](decider.md), the Python 2 client contract in [Py2 HTTP client](py2_client.md), and the guardrail taxonomy in [Fallback Semantics](fallbacks.qmd) for the full operational picture.
