# Proposal: Phase 2.2 – Structure Analyzer: Large Files & Long Functions

## Why
This change is part of 2 – Analyzers and introduces Structure Analyzer: Large Files & Long Functions so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a **structure analyzer** for: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a **structure analyzer** for:

  - Files with line count over a threshold (e.g., 400).
  - Functions with line count over a threshold (e.g., 60).
  - Configuration lives under `[analyzers.structure]` in `ai-clean.toml` with:
    - `max_file_lines` (default 400) and `max_function_lines` (default 60) – positive integers validated at load time.
    - `ignore_dirs` – directory names skipped during traversal (defaults align with duplicate analyzer).
    - Validation rules that raise clear `ValueError`s when thresholds are <= 0 or ignore lists contain invalid entries.

- For large files:

  - `Finding`:

    - `category = "large_file"`.
    - Locations: file-level range.

- For long functions:

  - `Finding`:

    - `category = "long_function"`.
    - Locations: exact function span.

- Ensure thresholds are configurable and multiple findings per file are allowed.
- Emit deterministic results by sorting discovered files/functions before producing findings so identical repositories yield identical outputs.

## Impact / Risks
- Unlocks later phases that depend on Structure Analyzer: Large Files & Long Functions.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
