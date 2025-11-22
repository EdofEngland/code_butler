# Proposal: Phase 3.1 – Planner for Duplicate Blocks

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Duplicate Blocks so the ButlerSpec-governed ai-clean workflow keeps momentum.
Codex is still the execution engine, but it now receives precise `CleanupPlan`s so ButlerSpec metadata remains the authoritative plan while duplicate code findings flow through the `/plan → spec → apply` loop without manual authoring.

## What Changes
- Define an explicit planner contract for `duplicate_block` findings:

  - Inputs: full `Finding` payload (id, description, metadata) plus every `FindingLocation` (path, start/end lines) emitted by the duplicate analyzer.
  - Outputs: one or more `CleanupPlan`s containing `title`, `intent`, ordered `steps`, `constraints`, `tests_to_run`, and helper-specific metadata the SpecBackend can later persist.
  - Execution flow: planners run inside the existing ButlerSpec pipeline, serialize each plan to `.ai-clean/plans/`, and Codex continues applying the ButlerSpec generated from those plans.

- Encode how helper extraction is described inside each plan:

  - Intent always states that we extract a reusable helper (function, method, or small class) and replace duplicates with a helper call.
  - Steps are numbered and must, at a minimum, decide helper placement, define the helper, and replace each duplicate occurrence.
  - Constraints reiterate “no external behavior changes” and “no public API changes,” referencing specific files/symbols when the finding metadata provides them.
  - Tests list the default test command from config (e.g., `tests.default_command`) unless the finding metadata overrides it.

- Add deterministic helper-location selection:

  - Prefer the file containing the lexicographically earliest duplicate occurrence when all duplicates live in one file.
  - For multi-file findings, pick the shallowest shared package (e.g., module `foo/utils/helpers.py`) or fall back to the repository root helpers module recorded in config; document this rule so reviewers can audit plan intent.

- Keep each plan **small** by codifying splitting heuristics:

  - Cap each plan at 3 duplicate occurrences; emit additional plans for the remaining windows.
  - Never mix helper targets: every plan focuses on a single helper location and contiguous concept.
  - Order emitted plans by helper target path and then by first occurrence line so reviewers can apply them sequentially.

- Expand QA expectations so every plan is verifiable:

  - Add tests covering: (1) a single-file duplicate produces one helper plan, (2) a multi-file finding splits into multiple plans capped at 3 occurrences each, (3) overlapping ranges still yield deterministic ordering, (4) helper-placement logic falls back to the configured helpers module, and (5) the default test command injected into plans matches `tests.default_command`.

## Assumptions & Non-goals
- Phase 3.1 only emits `CleanupPlan`s; no direct file edits or helper scaffolding happens here.
- No renaming or redesign of existing helper APIs—the planner only describes extractions based on current code.
- No new automation surfaces (CLI flags, Codex prompts) beyond what later phases already own; this change is scoped purely to planning duplicate blocks.

## Impact / Risks
- Unlocks later phases that depend on Planner for Duplicate Blocks.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
