# Proposal: Phase 3.4 – Planner for Organize Candidates

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Organize Candidates so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on translating every `organize_candidate` finding into small, deterministic plans while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes

### Planner intent
- Each `organize_candidate` finding becomes one or more `CleanupPlan`s that move a tight, coherent set of files (≤5 members) into a better folder while updating imports and re-exports.
- Plans must document the reasoning behind the new folder (topic name, shared parent), list every file/path affected, and stay reversible.

### Folder-selection heuristics
- Derive a target folder by:
  - Preferring the shallowest shared parent of all members; append the analyzer’s topic slug.
  - Falling back to the parent of the first member when no shared parent exists.
  - Rejecting folders that would exceed a configurable depth (e.g., more than two new levels) to avoid deep nesting.
- Split a finding into multiple plans when the proposed group exceeds five files or spans disjoint packages.

### Plan structure
- Steps must explicitly cover:
  1. Creating the destination folder (if missing) without touching unrelated directories.
  2. Moving each listed file, one-by-one, documenting path changes.
  3. Updating imports in modules that reference the moved files and adding re-exports in legacy locations to avoid breaking callers.
- Constraints reiterate “no function body edits” and “avoid deep nesting”; metadata includes the topic, source members, target directory, and whether re-exports are required.

### Acceptance criteria
- Plans emit deterministic IDs/titles referencing the topic and destination folder.
- Metadata mirrors the original finding (`topic`, `members`) plus planner decisions (`target_directory`, `reexports`, `scope="organize"`).
- Tests cover new-folder vs existing-folder flows, exceeding file-count guardrails, deterministic ordering, and import/re-export instructions.

## Assumptions & Non-goals
- Planners never modify function bodies; they only describe file moves and import updates.
- No analyzer changes occur in this phase; planners rely on existing `organize_candidate` metadata.
- This phase emits plans only; actual file moves happen later.

## Impact / Risks
- Unlocks later phases that depend on Planner for Organize Candidates.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
