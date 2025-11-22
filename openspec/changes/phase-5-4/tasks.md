## 1. Deliverables

- [ ] Implement factories:

  - [ ] `load_executor(config) -> CodeExecutor`:

    - [ ] If `executor.type == "codex_shell"`:

      - [ ] Return `CodexShellExecutor`.

  - [ ] `load_review_executor(config) -> ReviewExecutor`:

    - [ ] If `review.type == "codex_review"`:

      - [ ] Return Codex-based review executor.

- [ ] Unsupported types → explicit, helpful errors.
