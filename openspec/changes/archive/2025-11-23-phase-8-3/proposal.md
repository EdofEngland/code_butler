# Proposal: Phase 8.3 – No Global Renames or API Overhauls in V0

## Why
This change is part of 8 – Global Guardrails & Limits and introduces No Global Renames or API Overhauls in V0 so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Explicit planner + prompt constraints: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Explicit planner + prompt constraints for V0 safety:
  - No broad renaming of public APIs.
  - No global or cross-module renames.
  - No multi-module redesigns or subsystem-wide restructuring.
  - No breaking changes to public-facing interfaces or exported signatures.
- Enforce local, behavior-preserving, reversible cleanups only; planners/analyzers must reject or split any suggestion that crosses these boundaries.
- Non-goals: no API surface changes, no interface breaks, no sweeping module moves; any broader redesigns require separate phases.

## Impact / Risks
- Unlocks later phases that depend on No Global Renames or API Overhauls in V0.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to V0 plan-only guardrails; no executor or CLI UX changes in this phase. Broader API redesigns or cross-module work need separate proposals.
