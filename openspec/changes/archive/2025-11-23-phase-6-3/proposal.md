# Proposal: Phase 6.3 – Diff Stat Helper

## Why
This change is part of 6 – Git Safety & Storage Utilities and introduces Diff Stat Helper so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `get_diff_stat() -> str`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `get_diff_stat() -> str`:

  - Uses `git diff --stat` to summarize current changes.

- Used after successful apply to show:

  - Which files changed and how much.

## Impact / Risks
- Unlocks later phases that depend on Diff Stat Helper.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
