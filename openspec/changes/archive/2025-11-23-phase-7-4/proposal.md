# Proposal: Phase 7.4 – `/clean` Command (Basic Cleanup Wrapper)

## Why
This change is part of 7 – CLI Commands and introduces `/clean` Command (Basic Cleanup Wrapper) so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean clean [PATH]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean clean [PATH]`:

  - Run analyzers.

  - Filter findings for:

    - `duplicate_block`,
    - `large_file`,
    - `long_function`.

  - Present a list; user chooses a finding (or a few).

  - For each chosen finding:

    - Generate `CleanupPlan`.
    - Ask user whether to:

      - Only save plan, or
      - Save and immediately `/apply`.

## Impact / Risks
- Unlocks later phases that depend on `/clean` Command (Basic Cleanup Wrapper).
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
