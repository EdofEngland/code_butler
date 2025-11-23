# Proposal: Phase 7.1 – `/analyze` Command

## Why
This change is part of 7 – CLI Commands and introduces `/analyze` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean analyze [PATH]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean analyze [PATH]`:

  - Runs analyzer orchestrator.
  - Prints each `Finding`:

    - ID,
    - Category,
    - Short description,
    - Location summary.

- Read-only; no plans/specs created.

## Impact / Risks
- Unlocks later phases that depend on `/analyze` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
