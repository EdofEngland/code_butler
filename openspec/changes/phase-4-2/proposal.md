# Proposal: Phase 4.2 – Writing ButlerSpec Files

## Why
This change is part of 4 – ButlerSpec Backend & Spec Files (Our Own Tooling) and introduces Writing ButlerSpec Files so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path` as a deterministic serializer:

  - File name: `{spec.id}.butler.yaml` using the already canonicalized spec ID (no whitespace, lowercase enforced upstream).
  - Directory: `.ai-clean/specs/` by default, but the helper accepts any `Path` and ensures `directory.mkdir(parents=True, exist_ok=True)` before writing.
  - Content: UTF-8 YAML with a documented schema:
    - Root keys in fixed order: `id`, `plan_id`, `target_file`, `intent`, `model`, `batch_group`, `actions`, `metadata`.
    - `actions` is an array of dictionaries with keys ordered `type`, `index`, `summary`, `payload`.
    - `metadata` is a mapping sorted by key, with nested arrays serialized one item per line for readability.
    - Files always end with a single trailing newline and never include tabs or stray whitespace.

- Guardrails & validation before writing:

  - Each ButlerSpec file reflects exactly one target file and ≤25 actions; specs whose metadata hints at multiple files/topics are rejected with clear errors.
  - The backend refuses to overwrite files containing different spec IDs (collision check) but allows deterministic overwrites when the payload matches (idempotent writes).
  - YAML output must stay human-readable (≤32 KB, ASCII unless original plan metadata includes Unicode) and deterministic across runs; tests compare byte-for-byte equality.

- Filesystem contract:

  - `.ai-clean/specs/` is created on demand; missing directories are not an error.
  - Permission errors or unwritable locations surface as actionable exceptions.
  - Non-default directories (e.g., for tests) must still receive `.butler.yaml` suffix and the same schema/determinism rules.

## Assumptions / Non-Goals

- Phase 4.2 only handles writing ButlerSpec YAML files; batching, executor orchestration, or YAML diff tooling are deferred.
- No compression, streaming writers, or alternative serialization formats are considered in this phase.
- Valid ButlerSpecs are supplied by Phase 4.1; Phase 4.2 validates guardrails (single target, action limits) only to prevent regression, not to re-run full plan validation.
- Any enhancements to spec discovery/CLI commands happen in later phases to keep this scope focused on persistence.

## Impact / Risks
- Unlocks later phases that depend on Writing ButlerSpec Files.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
