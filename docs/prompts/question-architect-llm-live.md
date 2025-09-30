---
title: "Question for Architect — Live LLM Prompt Integration"
description: "Clarify where live LLM prompts and service calls fit into the milestone plan."
format:
  html:
    toc: false
---

# Context
- Current backlog (via `gh issue list --state open --limit 200`) spans Milestones **M3–M11**. None of the open issues mention drafting production prompts, selecting an inference provider, or pointing the Decider at anything beyond the stub.
- Milestone descriptions in `docs/blueprint.md` and existing method docs (`docs/methods/decider.md`) assume the **stub** continues to reply deterministically. Example: M3 focuses on firm hooks + overlays, M4 on bank hooks, M5 on wage hooks, and subsequent milestones cover manuscript integration, robustness demos, and sign-offs.
- The Decider schema files (`tools/decider/schemas/*.json`) and runtime tooling (`tools/generate_firm_ab.py`, `code/llm_runtime.py`) remain stub-oriented; there is no configuration knob for real providers, API keys, or prompt templates.
- No closed issue references a milestone for live prompts; searching GitHub issues for “prompt” only hits the blueprint sign-off (#6) and the main manuscript “spine” (#71), both already completed and confined to documentation artifacts.

# Question for Architect
Given the roadmap above, **where (if anywhere) are we planning to author the actual LLM prompts and swap the Decider stub for live model calls?**

- Should this work land in a future milestone (e.g., after M5 wage hooks) or is it intentionally out-of-scope for the manuscript deliverable?
- If live prompts are expected, what provider constraints (models, latency budget, cost) and validation steps should we account for?

Please advise so we can schedule the necessary tasks or explicitly mark them out-of-scope.
