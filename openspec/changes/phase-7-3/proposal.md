# Proposal: Phase 7.3 – `/apply` Command

## Why
This change is part of 7 – CLI Commands and introduces `/apply` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean apply PLAN_ID`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean apply PLAN_ID`:

  - Load config and git settings.
  - Ensure we’re on `refactor_branch`.
  - Load `CleanupPlan`.
  - Use `SpecBackend` (Butler) to:

    - Build `ButlerSpec` from plan.
    - Write spec to `.ai-clean/specs/` and get `spec_path`.
  - Use `CodeExecutor` (CodexShellExecutor) to:

    - Apply spec.
    - Run tests.
  - Display:

    - Apply success/failure,
    - Tests passed/failed,
    - `git diff --stat`.

## Impact / Risks
- Unlocks later phases that depend on `/apply` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
