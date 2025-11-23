# Proposal: Phase 5.1 – CodexShellExecutor: Apply Spec with Shell Wrapper

## Why
This change is part of 5 – Executors (Codex + Review) and introduces CodexShellExecutor: Apply Spec with Shell Wrapper so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `CodexShellExecutor` as a `CodeExecutor`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `CodexShellExecutor` as a `CodeExecutor`:

  - `apply_spec(spec_path: Path) -> ExecutionResult`:

    - Build a deterministic shell command:

      - Always run `bash -lc 'codex apply "<spec_path>"'`, escaping the absolute `spec_path` and pinning the working directory so Codex reads the same files every run.
      - Do not inject extra flags, env overrides, or chained scripts; the executor MUST launch exactly one Codex apply per call.
    - Run via `subprocess`.
    - Capture:

      - Exit code,
      - stdout,
      - stderr.
    - Surface deterministic errors for missing `codex` binary, non-zero exit codes, or timeouts instead of masking stderr.

  - Populate `ExecutionResult`:

    - `spec_id` from filename or parsed YAML.
    - `success` derived strictly from `exit_code == 0`; also retain the numeric exit code for debugging.
    - `stdout`/`stderr` from process outputs.
    - Leave `tests_passed`/`git_diff` unset in this phase while documenting that later phases will populate them.
    - Keep spec files untouched; CodexShellExecutor MUST fail instead of mutating the spec input.
    - Enforce one spec per invocation: reject lists, glob patterns, or derived batches to keep plan→spec→apply deterministic.

- Provide prompt guidance to keep the Codex apply phrase concise and low-token, mirroring OpenSpec’s guardrail language so the executor stays predictable.

- This preserves your **Codex integration** while making the spec system fully yours.

## Impact / Risks
- Unlocks later phases that depend on CodexShellExecutor: Apply Spec with Shell Wrapper.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline, single-spec execution, and no speculative edits to spec files.
- Scope stays limited to the tasks below; new needs require separate proposals.
- Failure handling is explicit (missing binary, stderr forwarding, exit codes) so downstream orchestrators can reason about deterministic outcomes.
