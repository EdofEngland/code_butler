## Why
Execute a saved plan: generate spec, apply it, run tests, and show results with git summary.

## What Changes
- Load config and git settings, ensure refactor branch via helper, and load the target plan.
- Call SpecBackend to create and write spec, then CodeExecutor to apply and run tests.
- Display apply/test results and git diff --stat summary.

## Impact
- Provides end-to-end apply flow from stored plans with git safety.
- Outputs clear status and change summary for users.
