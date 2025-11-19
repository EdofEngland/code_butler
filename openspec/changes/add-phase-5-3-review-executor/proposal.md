## Why
Provide read-only reviews summarizing diffs, risks, and manual checks using configured review tooling.

## What Changes
- Implement ReviewExecutor that accepts plan context, git diff, and ExecutionResult.
- Use configured review style (e.g., Codex review) to summarize changes, highlight risks, and suggest checks.
- Ensure executor is read-only and does not modify files.

## Impact
- Users receive structured change reviews after apply steps.
- Reviews incorporate test results and plan intent.
