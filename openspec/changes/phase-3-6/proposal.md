# Proposal: Phase 3.6 – Planning Orchestrator

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planning Orchestrator so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `plan_from_finding(finding: Finding) -> CleanupPlan`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `plan_from_finding(finding: Finding) -> CleanupPlan`:

  - Dispatch by `category`.
  - Generate a **single** plan for each invocation.

- Provide helpers to:

  - Generate unique plan IDs.
  - Serialize plans to `.ai-clean/plans/{plan_id}.json`.

## Impact / Risks
- Unlocks later phases that depend on Planning Orchestrator.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
