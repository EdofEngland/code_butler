# Proposal: Phase 3.1 – Planner for Duplicate Blocks

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Duplicate Blocks so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on For each `duplicate_block` finding, create a `CleanupPlan`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- For each `duplicate_block` finding, create a `CleanupPlan`:

  - Intent:

    - Extract reusable helper and replace duplicates.

  - Steps:

    - Decide helper location.
    - Create helper function/class.
    - Replace duplicate blocks with calls.

  - Constraints:

    - No external behavior changes.
    - No public API changes.

  - Tests:

    - Default test command from config.

- Keep each plan **small**:

  - If a finding has many occurrences, split into multiple plans.

## Impact / Risks
- Unlocks later phases that depend on Planner for Duplicate Blocks.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
