# Proposal: Phase 7.6 – `/organize` Command

## Why
This change is part of 7 – CLI Commands and introduces `/organize` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean organize [PATH]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean organize [PATH]`:

  - Run organize-seed analyzer.

  - Show `organize_candidate` findings.

  - User chooses candidates (each is a small group of files).

  - For each:

    - Generate a file-move `CleanupPlan`.
    - Apply or store via the same plan/spec/executor pipeline.

## Impact / Risks
- Unlocks later phases that depend on `/organize` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
