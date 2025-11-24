# Proposal: Phase 8.2 – Single Concern per Plan

## Why
This change is part of 8 – Global Guardrails & Limits and introduces Single Concern per Plan so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Enforce that each `CleanupPlan` addresses **one concern**: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Enforce that each `CleanupPlan` addresses exactly **one concern**, using a deterministic taxonomy:
  - One helper extraction.
  - One file split.
  - One small file-group move (tight, related files only).
  - One docstring batch for a small scope.
  - One advanced cleanup suggestion.
- Reject multi-concern plans and require planners/advanced analyzer to split mixed intentions into separate single-concern plans before execution.
- Define invalid mixes (e.g., docstring + helper extraction, move + rename + cleanup) and forbid chained refactors in one plan.
- Maintain ButlerSpec guardrails without adding executor/CLI UX changes in this phase.

## Impact / Risks
- Unlocks later phases that depend on Single Concern per Plan.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to plan-purity enforcement (one concern per plan); any broader workflow or UX changes require separate proposals.
