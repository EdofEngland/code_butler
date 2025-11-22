# Proposal: Phase 8.1 – Change Size Limits

## Why
This change is part of 8 – Global Guardrails & Limits and introduces Change Size Limits so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Config + enforcement for: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Config + enforcement for:

  - Max files per plan (ideally **1** in v0).
  - Max changed lines per plan.

- Planners and advanced analyzer must split large changes into multiple plans when limits are exceeded.

## Impact / Risks
- Unlocks later phases that depend on Change Size Limits.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
