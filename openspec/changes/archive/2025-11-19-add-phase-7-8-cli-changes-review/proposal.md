## Why
Provide a CLI to run review executor on applied changes before merge.

## What Changes
- Locate plan by ID, associated git diff, and latest ExecutionResult.
- Call ReviewExecutor with diff, plan intent, and test results.
- Display review summary covering what changed, risks, and suggested manual checks.

## Impact
- Enables pre-merge review summaries tied to plans and test outcomes.
- Standardizes review output via CLI.
