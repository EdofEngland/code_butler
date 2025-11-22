# Proposal: Phase 1.4 – Configuration & Local Metadata Layout

## Why
This change is part of 1 – Project Skeleton & Core Types and introduces Configuration & Local Metadata Layout so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Decide on a config convention: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

Phase 1.4 is the final dependency in `openspec/changes/phase-1-IMPLEMENTATION_ORDER.md`. It wires the serialization + interface work into real folders (`.ai-clean/plans|specs|results`) and typed config so every Phase 2 command can locate plans, specs, executors, and tests exactly the way the “Phase 1 System Sketch” describes.

## What Changes
- Decide on a config convention:

  - `ai-clean.toml` in repo root with, for example:

    ```toml
    [spec_backend]
    type = "butler"          # our own tooling

    [executor]
    type = "codex_shell"     # shell-wrapped Codex CLI

    [review]
    type = "codex_review"

    [git]
    base_branch = "main"
    refactor_branch = "refactor/ai-clean"

    [tests]
    default_command = "pytest -q"
    ```

- Define local metadata layout:

  - `.ai-clean/plans/` for serialized `CleanupPlan`s.
  - `.ai-clean/specs/` for serialized `ButlerSpec` YAML files.
  - Optional: `.ai-clean/results/` for `ExecutionResult` logs.

- Add simple config loader:

  - Reads and validates config.
  - Exposes typed config objects used by factories.
  - Emits helpful errors when directories or sections are missing, reinforcing ButlerSpec guardrails.

## Impact / Risks
- Unlocks later phases that depend on Configuration & Local Metadata Layout.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
