# Issue #151 · Writer Brief — Live Prompt Refresh (M6-LIVE)

## Mission
We need production-ready, roleplay-heavy prompts for the **firm**, **bank**, and **wage** live decision endpoints. The copy must lean into the agent’s persona, invoke the legacy heuristics the Caiani simulation already encodes, and instruct the LLM to stay inside the guardrails (price/spread/wage caps). Outputs must follow the structured JSON schemas below so the Decider can validate responses before applying guard clamps.

Deliver everything as Markdown snippets (ready to paste into the repo) plus a table that maps each `why` code to a short narrative gloss.

---

## Runtime context (Python 2 simulation + Python 3 Decider)
- The simulation calls the Decider with rich state payloads. If the LLM answer fails schema validation or violates guardrails, the agent falls back to its legacy heuristic.
- Guards are derived from `code/llm_runtime.py` presets:
  - **Firm** guards: `max_price_step = 0.04`, `max_expectation_bias = 0.04`, `price_floor = unit_cost / φ`.
  - **Bank** guards: baseline spread window `min_bps = 50`, `max_bps = 500` (tight/loose presets shift this by ±50%). Credit limit ratio must stay in `[0, 1]`.
  - **Wage** guards: `max_wage_step = 0.04` (scaled by preset), wage floor equals the firm’s minimum feasible wage.
- Live mode targets OpenRouter models with `temperature = 0`, strict deadlines (~200 ms), and deterministic caching. Prompts must make the LLM comfortable deferring to baseline heuristics when uncertain (`llm_uncertain`).

---

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

### Bank response schema (new — enforce in upcoming executor task)
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
4. **Why-code storytelling.** Provide cues for each enum so the generated `why` array acts as an interpretable rationale. You’ll also draft a rationale table (see below).
5. **Structured output only.** Reiterate “respond with JSON only” and emphasise compliance with the schema.
6. **Latent heuristics nod.** Reference the idea that the LLM has absorbed economic playbooks during training—prompt it to channel that expertise while respecting constraints.

---

## Deliverables (Markdown)
1. **Prompts section**
   - For each endpoint, supply a code block with the final system + user prompt text. Prefer Markdown fences labelled `text`.
   - If you need to reference the schema inline, do so concisely (no need to repeat the full JSON).
2. **Why-code rationale table**
   - Table columns: `Endpoint`, `Why Code`, `Human Gloss`, `When to use` (1–2 sentences).
   - Cover all enumerated codes listed above (firm, bank, wage).
3. **Assumptions / open questions** (optional) — call out anything the executor should confirm (e.g., additional guard values, new why codes).

Return everything in a single Markdown document attached to Issue #151. No code edits required from you.

---

## Additional references
- **Guard presets:** `code/llm_runtime.py` (firm/wage delta caps, bank spread window & epsilon).
- **Fallback semantics:** `docs/methods/fallbacks.qmd` — explains how the simulation logs fallbacks when validation fails.
- **Live mode overview:** `docs/methods/decider.md` — describes the live CLI and existing telemetry (prompt/completion tokens, elapsed time).

Ping the executor via Issue #151 if you need clarification on guard values or heuristics. The goal is evocative copy that keeps the LLM inside safety bounds while extracting the best of its macro-finance intuition.
