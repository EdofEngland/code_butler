# Proposal: Phase 5.2 – Test Runner Integration After Apply

## Why
This change is part of 5 – Executors (Codex + Review) and introduces Test Runner Integration After Apply so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Extend `CodexShellExecutor`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Extend `CodexShellExecutor`:

  - After a successful apply:

    - Run the configured tests (`tests.default_command` from config).
    - Capture exit status + logs.

  - Fill `ExecutionResult`:

    - `tests_passed = True` only if tests succeed.
    - Attach test output to stdout/stderr fields or metadata.

- If apply fails:

  - Skip tests and mark `tests_passed = False`.

## Impact / Risks
- Unlocks later phases that depend on Test Runner Integration After Apply.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
