# Proposal: Phase 6.1 – Plan Storage Helpers

## Why
This change is part of 6 – Git Safety & Storage Utilities and introduces Plan Storage Helpers so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement utilities to: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement utilities to:

  - Save `CleanupPlan` objects to `.ai-clean/plans/{plan_id}.json`.
  - Load `CleanupPlan` by `plan_id`.

- Ensure:

  - Round-tripping is lossless for required fields.

## Impact / Risks
- Unlocks later phases that depend on Plan Storage Helpers.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
