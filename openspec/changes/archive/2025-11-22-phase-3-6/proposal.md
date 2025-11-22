# Proposal: Phase 3.6 – Planning Orchestrator

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planning Orchestrator so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `plan_from_finding(finding: Finding) -> CleanupPlan`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `plan_from_finding(finding: Finding) -> CleanupPlan` as the single entrypoint for planners delivered in Phases 3.1–3.5.
  - Dispatch by `finding.category` using a documented mapping:
    - `duplicate_block` → wrapper that calls `plan_duplicate_blocks([finding], config)` and errors if it emits ≠1 plan.
    - `large_file` / `long_function` → Phase 3.2 helper.
    - `missing_docstring` / `weak_docstring` → Phase 3.3 helper.
    - `organize_candidate` → Phase 3.4 helper.
    - `advanced_cleanup` → Phase 3.5 helper.
  - Raise `NotImplementedError` for new/unknown categories so the orchestrator fails loudly.
  - Enforce “one plan per invocation” by validating helper output before returning and by persisting the JSON artifact (see below).
- Provide deterministic helpers to:
  - Generate plan IDs with the format `<finding-id>-<suffix>` (lowercase, `[a-z0-9-]` only) so the same `finding.id`+suffix pair always yields the same plan ID and filename.
  - Serialize plans to `.ai-clean/plans/{plan_id}.json` using UTF-8 encoded `CleanupPlan` JSON (ordered keys, no extra fields) so restart/resume flows find identical content on disk.

## Impact / Risks
- Unlocks later phases that depend on Planning Orchestrator.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Establishes deterministic IDs and persisted JSON schemas as shared contracts for downstream tooling and future orchestration tests.
- Scope stays limited to the tasks below; new needs require separate proposals.
