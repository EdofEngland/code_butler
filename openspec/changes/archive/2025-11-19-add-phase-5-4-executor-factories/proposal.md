## Why
Instantiate code and review executors from configuration with validation.

## What Changes
- Implement load_executor(config) -> CodeExecutor and load_review_executor(config) -> ReviewExecutor.
- Drive selection from ai-clean.toml values and fail clearly for unsupported types.
- Validate required settings before returning instances.

## Impact
- Executor selection becomes configurable and safe.
- Misconfiguration is surfaced before execution attempts.
