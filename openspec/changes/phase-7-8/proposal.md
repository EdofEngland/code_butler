# Proposal: Phase 7.8 – `/changes-review` Command

## Why
This change is part of 7 – CLI Commands and introduces `/changes-review` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean changes-review PLAN_ID`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean changes-review PLAN_ID`:

  - Locate associated:

    - `CleanupPlan`,
    - `ButlerSpec`,
    - `ExecutionResult`,
    - `git diff` for changes.

  - Use `ReviewExecutor` (Codex) to produce a review of the change.

  - Display:

    - Summary,
    - Risks,
    - Manual QA suggestions.

## Impact / Risks
- Unlocks later phases that depend on `/changes-review` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
