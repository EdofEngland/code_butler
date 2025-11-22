# Proposal: Phase 2.1 – Duplicate Code Analyzer (Local)

## Why
This change is part of 2 – Analyzers and introduces Duplicate Code Analyzer (Local) so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a local analyzer for **duplicate code blocks**: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a local analyzer for **duplicate code blocks**:

  - Recursively scan a target path for Python files.
  - Build normalized windows of code lines (fixed window size).
  - Group identical windows across files.
  - Respect configuration defined under `[analyzers.duplicate]` in `ai-clean.toml`:
    - `window_size`: positive integer controlling the sliding window (default 5 lines).
    - `min_occurrences`: positive integer threshold for emitting findings (default 2).
    - `ignore_dirs`: list of directory names skipped during traversal (defaults: `.git`, `.venv`, `__pycache__`).
    - Validation: raise configuration errors if thresholds are missing/invalid and normalize directory names.

- For each group with multiple occurrences:

  - Create a `Finding`:

    - `category = "duplicate_block"`.
    - Description: number of occurrences + brief context.
    - Locations: each file and line range.

- Ensure:

  - Deterministic behavior (same inputs → same findings).
  - Thresholds (window size, min occurrences) are config-driven.
  - Traversal order, window grouping, and finding IDs are stable by sorting discovered paths before processing.

## Impact / Risks
- Unlocks later phases that depend on Duplicate Code Analyzer (Local).
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
