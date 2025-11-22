# Proposal: Phase 5.4 – Executor Factories

## Why
This change is part of 5 – Executors (Codex + Review) and introduces Executor Factories so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement factories: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement factories:

  - `load_executor(config) -> CodeExecutor`:

    - If `executor.type == "codex_shell"`:

      - Return `CodexShellExecutor`.

  - `load_review_executor(config) -> ReviewExecutor`:

    - If `review.type == "codex_review"`:

      - Return Codex-based review executor.

- Unsupported types → explicit, helpful errors.

## Impact / Risks
- Unlocks later phases that depend on Executor Factories.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
