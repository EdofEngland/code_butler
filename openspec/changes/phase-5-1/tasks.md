## 1. Deliverables

- [ ] Implement `CodexShellExecutor` as a `CodeExecutor`:

  - [ ] `apply_spec(spec_path: Path) -> ExecutionResult`:

    - [ ] Build a shell command, e.g.:

      - [ ] `bash -lc 'codex apply "<spec_path>"'`
    - [ ] Run via `subprocess`.
    - [ ] Capture:

      - [ ] Exit code,
      - [ ] stdout,
      - [ ] stderr.

  - [ ] Populate `ExecutionResult`:

    - [ ] `spec_id` from filename or parsed YAML.
    - [ ] `success` from exit code.
    - [ ] `stdout`/`stderr` from process outputs.
    - [ ] `tests_passed` to be set in next phase.
    - [ ] `git_diff` left unset for now.

- [ ] This preserves your **Codex integration** while making the spec system fully yours.
