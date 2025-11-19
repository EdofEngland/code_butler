## Why
Automatically run configured tests after successful apply and report results.

## What Changes
- After a successful apply, run the test command(s) from config.
- Set tests_passed True only when tests exit cleanly; otherwise False.
- Skip tests when apply fails and preserve stdout/stderr from both steps.

## Impact
- Execution results reflect both apply status and test outcomes.
- Tests are not attempted when apply fails, reducing noise.
