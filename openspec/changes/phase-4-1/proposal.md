# Proposal: Phase 4.1 – ButlerSpec Backend: Plan → ButlerSpec

## Why
This change is part of 4 – ButlerSpec Backend & Spec Files (Our Own Tooling) and introduces ButlerSpec Backend: Plan → ButlerSpec so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `ButlerSpecBackend` (your OpenSpec replacement): while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `ButlerSpecBackend` (your OpenSpec replacement):

  - Accepts a `CleanupPlan`.

  - Enforces governance:

    - **One target file per plan** (one-plan-per-file).
    - Any violation → clear error.

  - Produces a `ButlerSpec` with fields like:

    - `id`: spec id.
    - `plan_id`.
    - `target_file`.
    - `intent`.
    - `actions`: structured instructions for the executor/model.
    - `model`: e.g., `"codex"` (or `"local_jamba"` later).
    - `batch_group`: optional grouping name for batches.
    - `metadata` (constraints, tests).

- Keep the payload:

  - Small, deterministic, and human-readable.

## Impact / Risks
- Unlocks later phases that depend on ButlerSpec Backend: Plan → ButlerSpec.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
