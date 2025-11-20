## Why
`scripts/apply_spec_wrapper.py` currently runs `openspec apply` without capturing stdout/stderr, so CodexExecutor receives an empty log even when the real command prints important warnings/errors. Users lose the feedback stored under `.ai-clean/executions/`, making it hard to tell what apply did.

## What Changes
- Update the wrapper to capture the `openspec apply` subprocess output and forward it to its own stdout/stderr so CodexExecutor records the real logs.
- Keep the stub fallback behavior untouched.

## Impact
- `ai-clean apply` will once again surface the same executor output as running `openspec apply` directly, preserving execution logs for review.
- No behavior change for environments using the stub.
