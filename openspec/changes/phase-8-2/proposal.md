# Proposal: Phase 8.2 – Single Concern per Plan

## Why
This change is part of 8 – Global Guardrails & Limits and introduces Single Concern per Plan so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Enforce that each `CleanupPlan` addresses **one concern**: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Enforce that each `CleanupPlan` addresses **one concern**:

  - One helper extraction,
  - One file split,
  - One small file group move,
  - One docstring batch for a small scope,
  - One advanced cleanup suggestion.

- This keeps each Butler spec and Codex call small and deterministic.

## Impact / Risks
- Unlocks later phases that depend on Single Concern per Plan.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
