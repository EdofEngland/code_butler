# Proposal: Phase 7.2 – `/plan` Command

## Why
This change is part of 7 – CLI Commands and introduces `/plan` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean plan FINDING_ID [--path PATH]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean plan FINDING_ID [--path PATH]`:

  - Run analyzers (or load cached findings).
  - Locate `Finding` by ID.
  - Create `CleanupPlan` via planner.
  - Save plan to `.ai-clean/plans/`.
  - Print:

    - Plan ID, title, intent, steps, constraints, tests_to_run.

## Impact / Risks
- Unlocks later phases that depend on `/plan` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
