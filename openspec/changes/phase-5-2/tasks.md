## 1. Deliverables

- [ ] Extend `CodexShellExecutor`:

  - [ ] After a successful apply:

    - [ ] Run the configured tests (`tests.default_command` from config).
    - [ ] Capture exit status + logs.

  - [ ] Fill `ExecutionResult`:

    - [ ] `tests_passed = True` only if tests succeed.
    - [ ] Attach test output to stdout/stderr fields or metadata.

- [ ] If apply fails:

  - [ ] Skip tests and mark `tests_passed = False`.
