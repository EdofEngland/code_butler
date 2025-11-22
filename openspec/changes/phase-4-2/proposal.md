# Proposal: Phase 4.2 – Writing ButlerSpec Files

## Why
This change is part of 4 – ButlerSpec Backend & Spec Files (Our Own Tooling) and introduces Writing ButlerSpec Files so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path`:

  - File name: `{spec.id}.butler.yaml`.
  - Directory: `.ai-clean/specs/` by default.
  - Content: YAML serialization of the `ButlerSpec`.

- Guardrails:

  - Each spec file corresponds to a **single, small change** in a single file.
  - No multi-topic specs.

## Impact / Risks
- Unlocks later phases that depend on Writing ButlerSpec Files.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
