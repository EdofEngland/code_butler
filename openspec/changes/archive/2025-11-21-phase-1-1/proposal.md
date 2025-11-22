# Proposal: Phase 1.1 – Repo & Packaging Setup

## Why
This change is part of 1 – Project Skeleton & Core Types and introduces Repo & Packaging Setup so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Create a new repo for `ai-clean` (or `code-butler`, whatever name you prefer). while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

Phase 1.1 anchors the “Phase 1 System Sketch” described in `docs/butlerspec_plan.md` by giving later phases a concrete CLI module, package metadata, and documentation to build upon. Per `openspec/changes/phase-1-IMPLEMENTATION_ORDER.md`, no subsequent Phase 1 work should begin until this repo skeleton lands.

## What Changes
- Create a new repo for `ai-clean` (or `code-butler`, whatever name you prefer).
- Add basic packaging:

  - Python project metadata (name, version, dependencies, entrypoint).
  - A CLI entrypoint (e.g. `ai-clean`).
- Add project hygiene:

  - `.gitignore` for Python.
  - `README` with:

    - Purpose of `ai-clean`.
    - Short explanation of core commands: `/analyze`, `/clean`, `/annotate`, `/organize`, `/cleanup-advanced`, `/plan`, `/apply`, `/changes-review`.
- Verify:

  - The CLI runs and prints a help message listing all commands (even if they’re placeholders).
  - Capture the help text snippet in the change notes so reviewers see the initial `/plan → spec → apply` loop wired end-to-end.

## Impact / Risks
- Unlocks later phases that depend on Repo & Packaging Setup.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
