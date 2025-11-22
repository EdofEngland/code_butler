# Proposal: Phase 3.3 – Planner for Docstring Findings

## Why
This change is part of 3 – Planner (Findings → CleanupPlans) and introduces Planner for Docstring Findings so the ButlerSpec-governed ai-clean workflow keeps momentum.
It covers both `missing_docstring` and `weak_docstring` findings while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes

### Planner: `missing_docstring`
- Intent: Add a concise docstring that documents the existing behavior without promising new contracts.
- Heuristics:
  - Inspect analyzer metadata (`symbol_type`, `qualified_name`, `lines_of_code`, preview text) plus AST context to understand inputs/outputs; if behavior is ambiguous, explicitly state “Assumes …” or “Document current behavior only”.
  - Keep each plan scoped to a single module or small cluster of related symbols; emit multiple plans when a module contains more than ~3 missing docstrings.
  - Require plan metadata to capture the target file, qualified name, symbol type, and whether assumptions were noted so reviewers see the confidence level.
- Steps inside each plan must describe:
  1. Reviewing the symbol implementation (with exact line span) and noting observed behavior.
  2. Drafting a factual docstring covering purpose, key parameters, and return value—no speculation.
  3. Inserting the docstring (respecting indentation/docstring style) in the same module.
- Constraints:
  - No renames, signature edits, or extra logic; the docstring must match today’s behavior.
  - If assumptions are unavoidable (e.g., lack of tests), they must be clearly marked inside the docstring.

### Planner: `weak_docstring`
- Intent: Strengthen an existing docstring by adding missing context (purpose, parameters, return value, side effects) while keeping the function identical.
- Heuristics:
  - Use the analyzer’s `docstring_preview` to identify the gaps (too short, contains TODO markers, etc.).
  - Preserve formatting conventions already used in the module (triple-double quotes, indentation) and highlight any external references that must remain accurate.
  - Split large modules into separate plans if necessary so each plan touches a tight group of symbols (e.g., methods within the same class).
- Steps must cover:
  1. Reviewing the current docstring to capture its deficiencies.
  2. Drafting an improved docstring that restates behavior accurately and removes weak markers.
  3. Replacing the old docstring while preserving code structure and comments around it.
- Constraints mirror the missing-docstring planner: no behavior changes, no fictional guarantees, and explicit assumptions if behavior cannot be proved.

### Acceptance criteria
- Each plan produces deterministic IDs/titles referencing the symbol.
- Plan metadata records the file path, qualified name, symbol type, whether it is an “add” or “improve” flow, and any assumptions.
- Plans stay per module (or small cluster) and highlight that other modules remain untouched.
- Tests cover missing vs weak docstrings, grouped symbols (multiple docstrings per file), missing metadata, and verifying that constraints/steps mention the same target file.

## Assumptions & Non-goals
- Planners never invent new behavior or promises—docstrings capture only what the code already does.
- No analyzer changes or new categories are introduced here; planners rely solely on data produced by existing docstring analyzers.
- This phase produces `CleanupPlan`s only; applying docstrings happens in later phases.

## Impact / Risks
- Unlocks later phases that depend on Planner for Docstring Findings.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
