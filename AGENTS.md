## Backlog Source of Truth (GitHub Issues Only)

- All planning, priorities, and dependencies now live in GitHub milestones and issues.
- Review progress via GitHub milestones (`gh issue list --milestone <name>`) and the milestone tab in the repo UI.
- The kickoff YAML only seeded the backlog; all later updates (like run logistics or provider choices) must be captured on GitHub issues and mirrored into `docs/blueprint.md` / `papers/assumptions_and_open_questions.md`.
- When adding a dependency, comment `Blocked by #<id>` on the blocked issue and mention the dependency on the parent issue.

### GitHub CLI quick actions
- `gh` is already authenticated for this repository; confirm with `gh auth status` if needed.
- Common queries: `gh issue list`, `gh issue view <number>`, `gh issue edit <number>`.
- Keep credentials out of commits; if re-auth is required follow the interactive `gh auth login` prompts.

## Contribution Discipline (Summary)
- Branch format: `task/<ISSUE-ID>--<slug>`.
- Commits: Conventional Commits, atomic, and always reference `#<ISSUE-ID>`.
- Check the issue’s `role:*` label before starting; if it’s `role:writer` or `role:signoff`, leave a status comment with any supporting artifacts/configs and hand it off instead of coding through it.
- Working an issue: comment “Start work”, produce required artifacts (`data/` or `figs/`), update relevant `.qmd`, run `quarto render docs`, open PR with “<ISSUE-ID> — <title>` + `Closes #<ISSUE-ID>`.
- Stay on task continuously; only pause for operator input when **(1)** a PR is waiting on merge, **(2)** you need the operator to launch the Decider server in another terminal (you may try running by yourself first, but always set timeout), **(3)** a writer/signoff action is required *and* you have already provided a complete Markdown brief with all context, or **(4)** you have exhausted at least five concrete approaches and still cannot see a path forward.
- After merge: comment “DoD: delivered” with artifact paths, close the issue, and notify dependents with “Unblocked by #<id>`.
- Manuscript-first: every task should move the Quarto manuscript forward; update **AGENTS.md** in the same PR whenever toggles/CLI/workflows change and call it out in the PR body.
- Baseline reference: `ssrn-3118643.qmd` captures the original Caiani article—consult it when aligning new manuscript sections or validating outputs.
- Strategic context: see `docs/blueprint.md` for the full manuscript blueprint, planned figures/tables, and Quarto page layout.

## Quickstart — Py2 Sim + Py3 Decider + Quarto

Run these from the repo root; keep the Decider stub in its own terminal while the sim executes.

1. **Start the Decider stub (Python 3).**

   ```bash
   python3 tools/decider/server.py --stub
   ```

   - Health check: `curl http://127.0.0.1:8000/healthz` should return `{ "status": "ok" }`.
   - Logs appear on stdout (and will later mirror into `logs/decider_stub.log`). Leave this process running.

2. **Kick a short baseline run (Python 2).**

   ```bash
   python2 code/timing.py
   ```

- Default parameters cover 1001 ticks; for smoke tests temporarily set `Parameter.ncycle = 200` *locally* (do **not** commit) or switch to the demo runner from #19 once it lands.
- Aggregates land in `data/`; runtime notes (and future LLM fallback counts) append to `timing.log`.
- Longer simulation or demo runs should be executed by the operator; ask for handoff before scheduling any extended run.

3. **Render the Quarto docs.**

   ```bash
   quarto render docs
   ```

   - Output site lives under `docs/_site/`; cite figures from `figs/` and tables from `data/` in the manuscript pages.

### LLM toggles & defaults
- All toggles live in `code/parameter.py`. Defaults keep the legacy heuristics (`use_llm_* = False`).
- `Parameter.llm_server_url` → default `http://127.0.0.1:8000` (matches the stub server).
- `Parameter.llm_timeout_ms` → default `200` (ms); convert to seconds for the Py2 client (`timeout = ms / 1000.0`).
- `Parameter.llm_batch` → default `False`; batch mode is a future milestone, leave off for now.
- On every run `code/timing.py` appends the current toggle state to `timing.log` (and prints it to stdout) so artifacts show which configuration produced them.

### Live Mode — OpenRouter Quickstart (M6)

1. **Set credentials & headers.** Export the required key and (optional) headers before launching the Decider:

   ```bash
   export OPENROUTER_API_KEY=sk-...
   export OPENROUTER_MODEL_PRIMARY=openrouter/openai/gpt-5-nano                # required
   export OPENROUTER_MODEL_FALLBACK=openrouter/google/gemini-2.5-flash-lite    # optional but recommended
   export OPENROUTER_HTTP_REFERER="https://absfcllmpy2.local"                 # optional
   export OPENROUTER_TITLE="absfcllmpy2 live dev"                             # optional
   ```

2. **Credit snapshot (automatic + optional manual).** When live mode starts the Decider issues `GET /api/v1/key` and logs the remaining credits/limits. Leave the log line in place for your run notes. You can still capture an explicit snapshot with `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/key` if you want to paste the JSON into `timing.log`.

3. **Model check (one-shot).**

   ```bash
   python3 tools/decider/server.py \
     --mode live \
     --openrouter-model-primary "$OPENROUTER_MODEL_PRIMARY" \
     --openrouter-model-fallback "$OPENROUTER_MODEL_FALLBACK" \
     --deadline-ms 200 \
     --check
   ```

   This verifies both slugs via `GET /api/v1/models`, pings `/healthz`, prints the status, and exits. Fix any `model_not_found` or auth errors before continuing.

4. **Run the live Decider (terminal #1).**

   ```bash
   python3 tools/decider/server.py \
     --mode live \
     --openrouter-model-primary "$OPENROUTER_MODEL_PRIMARY" \
     --openrouter-model-fallback "$OPENROUTER_MODEL_FALLBACK"
   ```

   The server proxies firm, bank, and wage calls through OpenRouter while honouring the guard stack (`δ = 0.04`, unit-cost floor, spread clamps). Model swapping happens entirely inside the Decider; the Python 2 simulation code remains unchanged.
   - To skip the automatic credit snapshot, pass `--skip-openrouter-credit-check` or export `OPENROUTER_SKIP_CREDIT_PREFLIGHT=1` before launching the server.

5. **Run the simulation (terminal #2).** Enable the relevant `use_llm_*` toggles (via `code/parameter.py` or runner scripts) and execute `python2 code/timing.py` or the appropriate `tools/generate_*_ab.py`. Keep the Decider window open until the run completes.

6. **Inspect telemetry.** `timing.log` now includes `[LLM block] usage` / `usage_error` lines (prompt tokens, completion tokens, elapsed ms, model slug). Append the credit snapshot and note any fallback reasons when sharing artifacts.

Additional implementation details live in `docs/methods/decider_live_openrouter.md`. Capture any provider changes or new prompts via GitHub issues so the backlog stays authoritative.

### Long runs & manual scheduling

Longer simulations should be coordinated with the operator so they can keep an eye on runtime and logs. Use the commands below as reference points when planning Monte Carlo or sensitivity sweeps.

| Scenario | Command (run from repo root) | Horizon / seeds | Expected wall-clock | Notes |
| --- | --- | --- | --- | --- |
| Full baseline sweep | `python2 code/timing.py` | `ncycle=1001`, `Lrun=0..49` (defaults) | ~45–60 min | Writes seed folders under `code/data/…`, appends toggle snapshot + counters to `timing.log`. Ask before launching; consumes a full core. |
| A/B overlay refresh | `python3 tools/generate_firm_ab.py`<br>`python3 tools/generate_bank_ab.py`<br>`python3 tools/generate_wage_ab.py` | `run_id=0`, `ncycle=200` | ~6–8 min each | Helper auto-starts the stub, runs OFF/ON, emits CSV + overlay PNG. Safe for local smoke tests. |
| Experiment demos (M7) | `python3 tools/generate_exp_a_demo.py`<br>`python3 tools/generate_exp_b_demo.py`<br>`python3 tools/generate_exp_c_demo.py` | `run_id=0`, `ncycle=250`, policy at `t0=50` | ~12–15 min each | Requires stub in a separate terminal (script reuses it). Produces `data/exp*_demo/` CSVs and wage-overlay plots. |
| Sensitivity stubs (coming in M8) | `python3 tools/generate_*` runners (to be added) | See issue briefs | 15–30 min | Coordinate before launching once the scripts land; many sweeps collect multiple OFF/ON pairs. |

**Coordination checklist**

- Before scheduling any run expected to exceed ~15 minutes, drop a quick note in the issue or to the operator confirming start/stop plans.
- Keep the Decider stub (or live server) in a dedicated terminal. For multi-run batches, restart the stub if it starts logging timeouts.
- Always capture the relevant log snippets: toggle snapshot lines from `timing.log`, usage counters, and any `usage_error` entries for live runs.
- After a long run completes, note the runtime band and any deviations in the issue comment so future operators can plan accordingly.
