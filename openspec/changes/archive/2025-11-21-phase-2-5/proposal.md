# Proposal: Phase 2.5 – Analyzer Orchestrator

## Why
This change is part of 2 – Analyzers and introduces Analyzer Orchestrator so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement `analyze_repo(path: Path) -> list[Finding]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement `analyze_repo(path: Path) -> list[Finding]`:

  - Calls:

    - Duplicate analyzer,
    - Structure analyzer,
    - Doc analyzer,
    - Organize-seed analyzer.

  - Orchestrator contract:
    - Load ai-clean config once and pass analyzer-specific settings to each phase implementation.
    - Invoke analyzers in deterministic order (duplicate → structure → docstrings → organize) and collect results.
    - Deduplicate findings by ID: merge locations/metadata when IDs collide, otherwise keep results untouched.
    - Normalize/sort final findings by `(category, id)` so identical repositories produce identical outputs.
    - Gracefully handle analyzer failures (log + continue) to keep `/analyze` resilient.

- Integrate into `/analyze` command:

  - Prints ID, category, description, and locations.
  - CLI expectations:
    - Support `--root`, `--config`, and `--json` flags.
    - Text mode shows a deterministic table with `id | category | description` and indented `path:start-end` lines.
    - JSON mode outputs serialized `Finding` objects (stable ordering).
    - Non-zero exit codes on fatal errors (e.g., invalid config path) while analyzer-level issues are surfaced as warnings.

- Assumptions / Non-goals:
  - Orchestrator does not mutate repositories or create plans/specs; it only emits metadata.
  - Logging format stays minimal (stdout summaries only) until later phases introduce richer UX.

## Impact / Risks
- Unlocks later phases that depend on Analyzer Orchestrator.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
