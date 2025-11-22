# Proposal: Phase 3.2 – Planner for Large Files & Long Functions

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Large Files & Long Functions so the ButlerSpec-governed ai-clean workflow keeps momentum.
It covers both `large_file` and `long_function` findings while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes

### Planner: `large_file`
- Intent: Split a large file (often 400+ lines) into 2–3 logical modules while preserving the original public surface.
- Heuristics:
  - Cluster `FindingLocation` ranges and top-level symbols into thematic groups (e.g., helpers vs. CLI glue) and cap each plan at three resulting modules. Emit additional plans when more clusters exist.
  - Prefer colocating helpers inside the same package; only create new folders when no shared parent can express the new boundary cleanly.
  - Require each plan to record metadata about the source file, targeted modules, and any re-export decisions so ButlerSpec reviewers see the intent.
- Steps inside each plan must call out:
  1. Reviewing the large file and assigning code blocks to the future modules.
  2. Creating module files/folders (with deterministic naming) and moving code.
  3. Updating imports plus re-exporting prior entry points to keep callers stable.
- Constraints:
  - Preserve public API via explicit re-exports from the original file or package `__init__.py`.
  - Forbid editing function bodies other than adjusting imports after moves.

### Planner: `long_function`
- Intent: Shorten a long function by extracting tightly-scoped helpers so behavior stays identical.
- Heuristics:
  - Use analyzer metadata (`qualified_name`, `start_line`, `end_line`, `line_count`) to describe sub-blocks, referencing control-flow markers (loops, conditionals) when determining helper boundaries.
  - Keep extractions local: helpers live next to the original function, share its visibility, and reuse existing arguments unless absolutely necessary.
  - Raise a clear error when metadata is missing, ensuring the planner never guesses at the target function.
- Steps inside each plan must call out:
  1. Identifying logical sub-blocks (with explicit line ranges).
  2. Extracting concise helper functions/methods with descriptive names.
  3. Replacing the original code with helper calls and validating readability.
- Constraints:
  - No API redesigns or changes in observable behavior.
  - Limit edits to the target function and adjacent helpers; do not touch distant modules.

### Acceptance criteria
- Deterministic plan IDs, titles, and metadata link every plan back to its source `Finding`.
- Plans describe exactly one helper/module boundary at a time and specify re-export or helper-placement decisions.
- Tests cover single-file vs. multi-module splits, helper extraction for nested functions, missing configuration defaults, and metadata propagation.

## Assumptions & Non-goals
- Phase 3.2 emits `CleanupPlan`s only—no file moves or refactors occur yet.
- No new analyzer categories or CLI flags are introduced; existing findings drive the planners.
- Performance tuning and Codex executor changes stay out of scope.

## Impact / Risks
- Unlocks later phases that depend on Planner for Large Files & Long Functions.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
