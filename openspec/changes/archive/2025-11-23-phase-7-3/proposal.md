# Proposal: Phase 7.3 – `/apply` Command

## Why
This change is part of 7 – CLI Commands and introduces `/apply` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean apply PLAN_ID`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean apply PLAN_ID` end-to-end flow:

  - Load config + git settings deterministically.
  - Enforce git safety: ensure `refactor_branch` via helpers; no commits/pushes.
  - Single-plan execution: load the specified `CleanupPlan` only; reject missing/extra args.
  - Spec generation: convert plan → ButlerSpec and write to `.ai-clean/specs/{id}.butler.yaml` (echo the path).
  - Execution: run CodexShellExecutor apply, then tests; keep stdout/stderr/exit codes intact.
  - Reporting: print apply success/failure, tests_passed state (including skipped), and `git diff --stat` summary.
  - Failure surfacing: stop with clear messages when plan load, spec build/write, apply, tests, or git helpers fail.

- Constraints / non-goals:

  - No batch apply, no interactive prompts.
  - No auto-commit/merge/push; caller decides next git steps.
  - Deterministic working dir and output ordering for re-runs.

## Impact / Risks
- Unlocks later phases that depend on `/apply` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
