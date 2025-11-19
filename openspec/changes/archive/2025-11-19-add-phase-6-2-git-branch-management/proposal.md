## Why
Provide helper to ensure work happens on a refactor branch derived from a base branch without forcing merges.

## What Changes
- Implement ensure_on_refactor_branch(base_branch, refactor_branch) with logic to fetch/update base, create or fast-forward refactor branch, and checkout refactor branch when needed.
- Avoid automatic commits or merges into main and surface conflicts to the user.
- Only act when not already on the refactor branch.

## Impact
- Enforces safe branch workflow for apply operations.
- Users stay off main while making changes.
