# Proposal: Phase 3.5 – Planner for Advanced Cleanup

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Advanced Cleanup so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on For `advanced_cleanup`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- For `advanced_cleanup`:

  - Intent: Implement a single, small Codex-suggested improvement.

  - Examples:

    - Simplify conditional.
    - Standardize naming within module.
    - Remove obviously dead code in a narrow scope.

  - Constraints:

    - Local change only (small patch).
    - Limit number of files + total changed lines.

- Plans should be **review-friendly**: small, self-contained.

## Impact / Risks
- Unlocks later phases that depend on Planner for Advanced Cleanup.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
