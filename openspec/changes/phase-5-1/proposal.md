# Proposal: Phase 5.1 – CodexShellExecutor: Apply Spec with Shell Wrapper

## Why
This change is part of 5 – Executors (Codex + Review) and introduces CodexShellExecutor: Apply Spec with Shell Wrapper so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `CodexShellExecutor` as a `CodeExecutor`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `CodexShellExecutor` as a `CodeExecutor`:

  - `apply_spec(spec_path: Path) -> ExecutionResult`:

    - Build a shell command, e.g.:

      - `bash -lc 'codex apply "<spec_path>"'`
    - Run via `subprocess`.
    - Capture:

      - Exit code,
      - stdout,
      - stderr.

  - Populate `ExecutionResult`:

    - `spec_id` from filename or parsed YAML.
    - `success` from exit code.
    - `stdout`/`stderr` from process outputs.
    - `tests_passed` to be set in next phase.
    - `git_diff` left unset for now.

- This preserves your **Codex integration** while making the spec system fully yours.

## Impact / Risks
- Unlocks later phases that depend on CodexShellExecutor: Apply Spec with Shell Wrapper.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
