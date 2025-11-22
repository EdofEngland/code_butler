# Proposal: Phase 3.3 – Planner for Docstring Findings

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Docstring Findings so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on For `missing_docstring` / `weak_docstring`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- For `missing_docstring` / `weak_docstring`:

  - Intent: Add or improve docstrings.

  - Steps:

    - Infer behavior from code.
    - Draft concise, factual docstring.
    - Insert/replace docstring.

  - Constraints:

    - No renames or behavior changes.
    - No fictional guarantees; docstrings must reflect existing behavior (or explicitly call out assumptions).

- Scope: plan per module or tight group of related symbols to keep small.

## Impact / Risks
- Unlocks later phases that depend on Planner for Docstring Findings.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
