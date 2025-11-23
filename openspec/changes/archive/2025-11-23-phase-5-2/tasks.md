## 1. Wire test execution into CodexShellExecutor

- [x] 1.1 Update `_CodexShellExecutor.apply_spec` (ai_clean/factories.py) to check `config.tests.default_command`; if apply failed or command is empty, skip running tests.
- [x] 1.2 When apply succeeds and a test command is configured, run it via `subprocess.run(..., capture_output=True, text=True, shell=True)` with deterministic `cwd` (repo root/spec parent).
- [x] 1.3 Capture test stdout/stderr and exit code; append/merge test streams to the existing `ExecutionResult.stdout`/`stderr` or store under `metadata["tests"] = {...}` to keep apply logs intact.
- [x] 1.4 Set `ExecutionResult.tests_passed = (test_exit_code == 0)`; if tests are skipped, set `tests_passed = False` and add a reason in metadata.
- [x] 1.5 Ensure failures in test execution (missing binary, timeout) mark `tests_passed = False` without retrying apply; preserve original apply success flag.

## 2. Tests for test-run wiring

- [x] 2.1 Add a unit test (e.g., `tests/test_factories.py`) that mocks `subprocess.run` for both apply and tests, asserting the test command runs only when apply succeeded and command is configured.
- [x] 2.2 Add a test that injects a failing test exit code and verifies `tests_passed=False` while keeping `success=True` from apply.
- [x] 2.3 Add a test that ensures stdout/stderr contain both apply and test output (or metadata entries) deterministically.
