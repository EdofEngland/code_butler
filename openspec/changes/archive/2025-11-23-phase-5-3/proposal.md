# Proposal: Phase 5.3 – ReviewExecutor: Codex-Powered Changes Review

## Why
This change is part of 5 – Executors (Codex + Review) and introduces ReviewExecutor: Codex-Powered Changes Review so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a `ReviewExecutor` for `/changes-review`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a `ReviewExecutor` for `/changes-review`:

  - Input:

    - `CleanupPlan` object or `plan_id` loader (fail fast if neither is available),
    - Associated `git diff` snapshot for the plan (explicitly passed, no implicit Git calls),
    - Latest `ExecutionResult` (apply + test info) to ground the review context.

  - Use Codex in “review mode” with a bounded prompt:

    - Prompt template: “Summarize these changes, flag risks, and ensure plan constraints are respected. Provide advisory notes only. Do NOT propose or apply code modifications.”
    - Keep tokens small and deterministic: no chained instructions, no API redesigns, no broad refactors; stick to the provided plan/diff/result.

  - Output:

    - Review text or structured review containing:

      - Summary of changes,
      - Risk assessment with a simple grading,
      - Suggested manual checks,
      - Optional constraint validation notes.

- Guardrails: review-only behavior (no patch generation), single-plan scope, explicit inputs only, and deterministic formatting so downstream tools can parse/display consistently.

## Impact / Risks
- Unlocks later phases that depend on ReviewExecutor: Codex-Powered Changes Review.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
