# Proposal: Phase 7.8 – `/changes-review` Command

## Why
This change is part of 7 – CLI Commands and introduces a `/changes-review` command so the ButlerSpec-governed ai-clean workflow keeps momentum after a change has been applied.
It focuses on `ai-clean changes-review PLAN_ID`, with Codex as the execution engine and ButlerSpec metadata as the authoritative plan, while keeping the command strictly review-only and deterministic.

## What Changes
- Add an `ai-clean changes-review PLAN_ID` CLI command that:

  - Resolves `PLAN_ID` to its associated artifacts, limited to the single plan:

    - `CleanupPlan`,
    - `ButlerSpec`,
    - `ExecutionResult` (apply + tests),
    - `git diff` for the plan’s changes.

  - Invokes a `ReviewExecutor` (Codex) in **review-only mode** using a bounded, advisory prompt:

    - Summarize the change in terms of the plan and diff.
    - Flag visible risks and regressions based only on the provided artifacts.
    - Confirm whether stated plan / ButlerSpec constraints appear to have been respected.
    - **Do not** propose edits, refactors, patches, or new tasks.

  - Renders a deterministic, human-friendly report with the following sections in a fixed order:

    1. Summary of Changes
    2. Risk Assessment
    3. Manual QA Suggestions
    4. Constraint Validation Notes (optional when constraints are implicit)

  - Handles missing or partial artifacts with clear, bounded behavior (e.g., show a gap, avoid overconfident conclusions, and skip Codex when required inputs are absent).

## Review Prompt Contract (Review-Only)
The `ReviewExecutor` (Codex) MUST be invoked with a prompt that:

- Treats the review as advisory only:
  - Focuses on summarizing observed behavior, risks, and constraints adherence.
  - Uses language like “Consider checking…” rather than imperative changes.
- Explicitly forbids:
  - File edits or patch suggestions.
  - Refactors or new implementation designs.
  - Creating new tasks or phases.
- Keeps output bounded and deterministic:
  - Uses the four named sections above, in order.
  - Avoids timestamps, environment-specific paths, or non-deterministic details.
  - Stays strictly within the `PLAN_ID`-scoped artifacts presented.

## Assumptions
- All artifacts (`CleanupPlan`, `ButlerSpec`, `ExecutionResult`, `git diff`) are already on disk and owned by other phases; `/changes-review` is read-only.
- There is exactly one `CleanupPlan` per plan file and the `PLAN_ID` can be resolved unambiguously.
- Codex is already configured as the execution engine for ai-clean and can be called with a structured payload plus prompt.

## Non-goals
- Re-running apply or test phases.
- Modifying any artifacts (plans, specs, execution results, or the working tree).
- Changing plan status, creating new plans, or updating ButlerSpec.
- Reviewing code outside the diff and artifacts tied to the specified `PLAN_ID`.

## Impact / Risks
- Unlocks later phases that depend on `/changes-review` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline, and read-only review flows.
- Scope stays limited to the tasks below; new needs require separate proposals.
