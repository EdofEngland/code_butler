## 1. CLI command and lifecycle

- [x] 1.1 Register an `ai-clean changes-review PLAN_ID` command in the CLI entrypoint, validating that `PLAN_ID` is provided and resolvable.
- [x] 1.2 Resolve `PLAN_ID` to its associated artifacts in a read-only way:
  - [x] `CleanupPlan`
  - [x] `ButlerSpec`
  - [x] `ExecutionResult` (apply + tests)
  - [x] `git diff` for the plan’s changes
- [x] 1.3 Enforce plan scoping so only artifacts for the specified `PLAN_ID` are loaded and no other plans or diffs are inspected.

## 2. ReviewExecutor integration (review-only)

- [x] 2.1 Construct a structured payload for `ReviewExecutor` that includes only:
  - [x] The resolved `CleanupPlan`
  - [x] The associated `ButlerSpec`
  - [x] The `ExecutionResult` (apply + tests)
  - [x] The `git diff` for the plan
- [x] 2.2 Implement a bounded, review-only prompt that:
  - [x] Summarizes the changes.
  - [x] Flags risks and potential regressions.
  - [x] Confirms apparent adherence to plan / ButlerSpec constraints.
  - [x] Explicitly forbids edits, patches, refactors, or new tasks.
- [x] 2.3 Ensure the ReviewExecutor call is read-only and cannot modify files, git state, or spec/plan artifacts.

## 3. Output formatting and determinism

- [x] 3.1 Format CLI output into four clearly labeled sections in fixed order:
  - [x] Summary of Changes
  - [x] Risk Assessment
  - [x] Manual QA Suggestions
  - [x] Constraint Validation Notes (optional when constraints are implicit)
- [x] 3.2 Keep output deterministic and user-friendly:
  - [x] Avoid timestamps, environment-specific paths, or random ordering.
  - [x] Use stable labels and wording patterns where possible.

## 4. Error handling and partial data

- [x] 4.1 Detect when required artifacts are missing for the given `PLAN_ID`:
  - [x] No `CleanupPlan` for `PLAN_ID`.
  - [x] No `ButlerSpec` entry for `PLAN_ID`.
  - [x] No `ExecutionResult` for apply or tests.
  - [x] No `git diff` associated with the plan.
- [x] 4.2 For hard failures (e.g., missing `CleanupPlan` or unknown `PLAN_ID`), fail fast with a clear, deterministic error message and do not call `ReviewExecutor`.
- [x] 4.3 For soft/partial cases (e.g., missing `ExecutionResult` but diff present), call out the gaps explicitly in the output and ensure the review does not overstate confidence.
- [x] 4.4 Ensure that all error paths remain within review-only scope and never trigger new applies, tests, or edits.
