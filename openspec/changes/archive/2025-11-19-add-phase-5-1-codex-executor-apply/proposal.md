## Why
Run the configured apply command against a spec file and capture execution output.

## What Changes
- Implement CodexExecutor (or equivalent executor) that receives a spec path and invokes the apply command.
- Capture success/failure plus stdout/stderr logs into ExecutionResult.
- Record success based on command exit code and leave tests_passed unset initially.

## Impact
- Specs can be applied programmatically with captured logs.
- Execution results provide visibility into apply attempts.
