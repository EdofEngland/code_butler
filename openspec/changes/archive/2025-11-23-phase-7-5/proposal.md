# Proposal: Phase 7.5 – `/annotate` Command

## Why
This change is part of 7 – CLI Commands and introduces `/annotate` Command so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on `ai-clean annotate [PATH] [--mode missing|all]`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- `ai-clean annotate [PATH] [--mode missing|all]`:

  - Run doc analyzer.

  - Filter for `missing_docstring` (and maybe `weak_docstring` if `--mode all`).

  - Show targets; user chooses modules or “all”.

  - For each selection:

    - Generate a docstring `CleanupPlan`.
    - Offer to apply via the standard `/apply` flow.

## Impact / Risks
- Unlocks later phases that depend on `/annotate` Command.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
