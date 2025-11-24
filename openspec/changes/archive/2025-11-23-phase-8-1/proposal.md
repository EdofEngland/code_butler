# Proposal: Phase 8.1 – Change Size Limits

## Why
This change is part of 8 – Global Guardrails & Limits and introduces Change Size Limits so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Config + enforcement for: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Config + enforcement for deterministic size ceilings:
  - Max files per plan (v0 MUST be 1).
  - Max changed lines per plan (counted as absolute additions + deletions).
- Mandatory split behavior: planners and advanced analyzer MUST split work into multiple plans whenever either limit would be exceeded.
- Rejection guardrails: multi-file or over-cap plans SHALL be rejected with clear errors; no multi-concern plans in Phase 8.1.

## Impact / Risks
- Unlocks later phases that depend on Change Size Limits.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to plan-size enforcement only (no executor/CLI UX changes); broader changes require separate proposals.
