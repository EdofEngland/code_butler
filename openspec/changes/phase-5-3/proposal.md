# Proposal: Phase 5.3 – ReviewExecutor: Codex-Powered Changes Review

## Why
This change is part of 5 – Executors (Codex + Review) and introduces ReviewExecutor: Codex-Powered Changes Review so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a `ReviewExecutor` for `/changes-review`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a `ReviewExecutor` for `/changes-review`:

  - Input:

    - `CleanupPlan` (or `plan_id` to load it),
    - Associated `git diff` for the plan,
    - Latest `ExecutionResult` (apply + test info).

  - Use Codex in “review mode”:

    - Prompt: “Summarize these changes, flag risks, respect constraints.”

  - Output:

    - Review text or structured review:

      - Summary of changes,
      - Risk assessment,
      - Suggested manual checks.

- No code modifications here—review only.

## Impact / Risks
- Unlocks later phases that depend on ReviewExecutor: Codex-Powered Changes Review.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
