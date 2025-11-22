# Proposal: Phase 7.7 – `/cleanup-advanced` Command

## Why
This change is part of 7 – CLI Commands and introduces `/cleanup-advanced` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean cleanup-advanced [PATH]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean cleanup-advanced [PATH]`:

  - Run advanced Codex-powered analyzer.

  - Show limited `advanced_cleanup` findings.

  - For each:

    - Generate a `CleanupPlan`.
    - Do **not** auto-apply; the user can call `/apply PLAN_ID` after review.

## Impact / Risks
- Unlocks later phases that depend on `/cleanup-advanced` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
