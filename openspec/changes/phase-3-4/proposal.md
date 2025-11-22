# Proposal: Phase 3.4 – Planner for Organize Candidates

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Organize Candidates so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on For `organize_candidate`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- For `organize_candidate`:

  - Intent: Move a small group of files into a better folder.

  - Steps:

    - Create folder if needed.
    - Move files.
    - Update imports and add re-exports as necessary.

  - Constraints:

    - No changes to function bodies.
    - Avoid deep nesting.

- Each `CleanupPlan` moves only a **small set** of files.

## Impact / Risks
- Unlocks later phases that depend on Planner for Organize Candidates.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
