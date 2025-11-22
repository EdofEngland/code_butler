# Proposal: Phase 4.1 – ButlerSpec Backend: Plan → ButlerSpec

## Why
This change is part of 4 – ButlerSpec Backend & Spec Files (Our Own Tooling) and introduces ButlerSpec Backend: Plan → ButlerSpec so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `ButlerSpecBackend` (your OpenSpec replacement): while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Define and enforce the `.ai-clean/plans/{plan_id}.json` serialization contract:

  - Plans MUST declare `id`, `intent`, ordered `steps[]`, `constraints[]`, `tests_to_run[]`, and `metadata.target_file` (non-empty string bounded by repo length rules).
  - Whitespace in IDs or steps is trimmed when persisted so ButlerSpec generation receives deterministic, canonical inputs.
  - Unknown planner fields are rejected with actionable errors before ButlerSpec conversion begins.

- Implement `ButlerSpecBackend` (OpenSpec replacement) with a fully specified schema:

  - Required fields: `id = f"{plan.id}-spec"`, `plan_id`, `target_file`, `intent`, `actions[]`, `model` (enum: `"codex"` today, extendable), `metadata` (detached dict copy).
  - Optional field: `batch_group` defaults to `config.default_batch_group` but may be `None`.
  - Metadata augmentation: copy plan metadata and add `plan_title`, normalized `constraints`, and `tests_to_run` arrays so executors never read the plan file.

- Codify governance + guardrails:

  - Exactly one `target_file` per plan/spec; missing or non-string values raise `ValueError("ButlerSpec plans must declare exactly one target_file")`.
  - Overly large metadata (>32 KB), multi-target hints, or mismatched `intent` vs `target_file` path emit deterministic errors referencing the offending key.
  - `write_spec` stays disabled (`NotImplementedError`) until Phase 4.2 writes YAML, preventing accidental persistence outside the contract.

- Introduce a structured `actions` vocabulary tailored for executor models:

  - Phase 4.1 ships `plan_step` entries: `{ "type": "plan_step", "index": n, "summary": step, "payload": null }`.
  - Entries are ordered, trimmed, and capped (e.g., 25 steps) to ensure small, human-readable payloads.
  - Reserve identifiers (`edit_block`, `insert_docstring`, etc.) for later phases so models receive a deterministic schema from day one.

- Keep the ButlerSpec payload small, deterministic, and human-readable via the rules above and explicit metadata copying.

## Assumptions / Non-Goals

- Phase 4.1 only covers in-memory conversion; persisting `.butler.yaml` specs is a Phase 4.2 responsibility.
- Codex remains the only execution model for now; multi-model routing (e.g., `local_jamba`) will follow after governance hardening.
- No CLI changes ship in this phase; planner/runner wiring continues to call the backend indirectly through existing factories.
- Metadata/plan sizes are bounded (e.g., 25 steps, 32 KB metadata) to keep specs reviewable; larger work must split into multiple plans.

## Impact / Risks
- Unlocks later phases that depend on ButlerSpec Backend: Plan → ButlerSpec.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
