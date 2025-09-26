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

3. **Render the Quarto docs.**

   ```bash
   quarto render docs
   ```

   - Output site lives under `docs/_site/`; cite figures from `figs/` and tables from `data/` in the manuscript pages.
