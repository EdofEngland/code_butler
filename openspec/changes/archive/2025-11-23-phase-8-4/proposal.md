# Proposal: Phase 8.4 – Test-First Execution Policy

## Why
This change is part of 8 – Global Guardrails & Limits and introduces Test-First Execution Policy so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `/apply` must always: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `/apply` must always:

  - Record whether tests ran.
  - Include test status in:

    - CLI output,
    - Stored `ExecutionResult`,
    - Any `/changes-review` output.

- Error paths:

  - Failed apply or failed tests → explicit, loud diagnostics.

## Impact / Risks
- Unlocks later phases that depend on Test-First Execution Policy.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
