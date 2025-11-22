# Proposal: Phase 3.2 – Planner for Large Files & Long Functions

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Large Files & Long Functions so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on For `large_file`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- For `large_file`:

  - Intent: Split into 2–3 logical modules.
  - Steps:

    - Group code by responsibility.
    - Create new modules.
    - Move code and adjust imports.
  - Constraints:

    - Preserve public API, using re-exports if needed.

- For `long_function`:

  - Intent: Extract helpers to reduce length.
  - Steps:

    - Identify logical sub-blocks.
    - Extract into helpers.
    - Call helpers from original function.
  - Constraints:

    - Scope limited to the single function or very close neighbors.

## Impact / Risks
- Unlocks later phases that depend on Planner for Large Files & Long Functions.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
