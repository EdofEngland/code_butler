# Proposal: Phase 6.2 – Git Branch Management

## Why
This change is part of 6 – Git Safety & Storage Utilities and introduces Git Branch Management so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `ensure_on_refactor_branch(base_branch, refactor_branch)`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `ensure_on_refactor_branch(base_branch, refactor_branch)`:

  - If already on `refactor_branch`: do nothing.
  - Else:

    - Fetch/update `base_branch`.
    - Create/fast-forward `refactor_branch` from `base_branch`.
    - Checkout `refactor_branch`.

- No auto-commits or merges into `main`. Conflicts are surfaced to user.

## Impact / Risks
- Unlocks later phases that depend on Git Branch Management.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
