# Proposal: Phase 1.3 – Plugin Interfaces

## Why
This change is part of 1 – Project Skeleton & Core Types and introduces Plugin Interfaces so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Define abstract interfaces: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

Per `openspec/changes/phase-1-IMPLEMENTATION_ORDER.md`, Phase 1.3 consumes the Phase 1.2 core models and turns the “Phase 1 System Sketch” into concrete Protocols for plan → spec → executor handoffs. These interfaces make it trivial to stub Codex during local tests while still enforcing ButlerSpec guardrails.

## What Changes
- Define abstract interfaces:

  - `SpecBackend`:

    - `plan_to_spec(plan: CleanupPlan) -> ButlerSpec`
    - `write_spec(spec: ButlerSpec, directory: Path) -> Path` (returns `spec_path`)

  - `CodeExecutor`:

    - `apply_spec(spec_path: Path) -> ExecutionResult`

  - `ReviewExecutor` (for `/changes-review`):

    - `review_change(plan: CleanupPlan, diff: str, exec_result: ExecutionResult) -> str | StructuredReview`

  - (Optional, if you want batching explicit now) `BatchRunner`:

    - `apply_batch(spec_dir: Path, batch_group: str) -> list[ExecutionResult]`

- Ensure:

  - Interfaces depend only on core models + standard libs.
  - No “OpenSpec” terminology; Codex is referenced only in concrete executor implementations, not in interfaces.
  - Documentation clearly states these contracts are the only boundary Phase 2+ components should rely on.

## Impact / Risks
- Unlocks later phases that depend on Plugin Interfaces.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
