## Why
Quickly summarize changed files after apply to show impact size.

## What Changes
- Implement get_diff_stat() to return git diff --stat summary of the working tree.
- Use output after successful apply to indicate touched files and change magnitude.
- Keep helper read-only.

## Impact
- Users see concise change summaries post-apply.
- Works without modifying repository state.
