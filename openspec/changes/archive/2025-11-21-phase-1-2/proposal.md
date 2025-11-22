# Proposal: Phase 1.2 – Core Data Model Definitions

## Why
This change is part of 1 – Project Skeleton & Core Types and introduces Core Data Model Definitions so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Add a “core models” module defining the **core abstractions**: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

Phase 1.2 depends on the package scaffold from Phase 1.1 (`openspec/changes/phase-1-IMPLEMENTATION_ORDER.md`). It supplies the data flow components referenced in the “Phase 1 System Sketch” so later phases (`SpecBackend`, config, factories) interact with typed objects rather than ad-hoc dicts.

## What Changes
- Add a “core models” module defining the **core abstractions**:

  - `FindingLocation`: path + start/end lines.
  - `Finding`: id, category (e.g. `duplicate_block`, `large_file`, `missing_docstring`, `organize_candidate`, `advanced_cleanup`), description, locations, metadata.
  - `CleanupPlan`: id, finding_id, title, intent, steps, constraints, tests_to_run, metadata.
  - `ButlerSpec`: id, plan_id, target_file, intent, actions, model, batch_group, metadata.
  - `ExecutionResult`: spec_id, plan_id, success, tests_passed, stdout, stderr, git_diff (optional), metadata.

- Ensure:

  - Core models have **no dependency** on Codex or any external tools.
  - All types can be created and serialized (JSON/YAML) using only stdlib + pydantic/dataclasses plus an optional `pyyaml` extra guarded behind feature detection.

## Impact / Risks
- Unlocks later phases that depend on Core Data Model Definitions.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
