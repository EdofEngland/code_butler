## 1. Deliverables

- [ ] `ai-clean apply PLAN_ID`:

  - [ ] Load config and git settings.
  - [ ] Ensure we’re on `refactor_branch`.
  - [ ] Load `CleanupPlan`.
  - [ ] Use `SpecBackend` (Butler) to:

    - [ ] Build `ButlerSpec` from plan.
    - [ ] Write spec to `.ai-clean/specs/` and get `spec_path`.
  - [ ] Use `CodeExecutor` (CodexShellExecutor) to:

    - [ ] Apply spec.
    - [ ] Run tests.
  - [ ] Display:

    - [ ] Apply success/failure,
    - [ ] Tests passed/failed,
    - [ ] `git diff --stat`.
