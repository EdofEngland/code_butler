# Proposal: Phase 3.5 – Planner for Advanced Cleanup

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Advanced Cleanup so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on translating every `advanced_cleanup` finding into a small, well-described plan while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes

### Planner intent
- Each `advanced_cleanup` finding yields a single `CleanupPlan` that applies exactly one Codex-suggested micro-change (e.g., simplify a conditional, standardize naming, remove dead code) confined to the snippet lines provided by the analyzer.
- Plans remain self-contained, referencing one file and a bounded line range; no structural refactors or multi-module rewrites.

### Guardrails and heuristics
- Enforce strict limits:
  - Touch at most one file per plan (mirrors analyzer output).
  - Limit the edited span to the provided `start_line`–`end_line` range plus minimal context (≤10 surrounding lines).
  - Cap total changed lines (e.g., ≤25) and note the estimated change size inside plan metadata.
- Reject/re-scope findings when:
  - Metadata is incomplete (missing `target_path`, `start_line`, etc.).
  - Codex suggests multiple unrelated improvements; planners only accept single-action suggestions.
  - The change would affect APIs or behavior beyond the localized snippet.

### Plan structure
- Steps must include:
  1. Verifying the snippet still matches the suggestion (protect against drift).
  2. Applying the precise change (mentioning file path + line range).
  3. Running the specified test command (use the finding’s custom command when available, otherwise the config default).
- Constraints reiterate “no API changes,” “no unrelated edits,” and “limit edits to lines X–Y.”
- Metadata records the target file, span, change type, prompt hash, Codex model, and any assumption flags (e.g., `{"needs_manual_verification": false}`).

### Acceptance criteria
- Deterministic plan IDs/titles referencing the change type and file.
- Plans are review-friendly: small scope, explicit steps, constraints, and tests.
- Tests cover positive flows (various change types, custom test commands) and guardrails (missing metadata, multi-file suggestions, exceeding size limits).

## Assumptions & Non-goals
- No new analyzer logic is introduced; the planner consumes metadata from Phase 2.6.
- This phase does not alter Codex suggestions—it only expresses them as plans.
- Performance and CLI changes remain out of scope.

## Impact / Risks
- Unlocks later phases that depend on Planner for Advanced Cleanup.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
