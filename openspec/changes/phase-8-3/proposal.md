# Proposal: Phase 8.3 – No Global Renames or API Overhauls in V0

## Why
This change is part of 8 – Global Guardrails & Limits and introduces No Global Renames or API Overhauls in V0 so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Explicit planner + prompt constraints: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Explicit planner + prompt constraints:

  - No broad renaming of public APIs.
  - No multi-module redesigns.
  - Reject or break apart suggestions that violate this.

## Impact / Risks
- Unlocks later phases that depend on No Global Renames or API Overhauls in V0.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
