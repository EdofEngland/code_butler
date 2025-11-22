## ADDED Requirements

### Requirement: Planner emits factual plans for `missing_docstring` findings
The planner MUST convert every `missing_docstring` finding into a deterministic `CleanupPlan` (returned inside a single-element list) that adds a concise docstring reflecting existing behavior.

#### Scenario: Add docstring plan
- **GIVEN** a `Finding` with `category="missing_docstring"` plus metadata (`symbol_type`, `qualified_name`, `symbol_name`, `lines_of_code`, `docstring_preview`)
- **WHEN** the planner runs
- **THEN** the generated plan id/title reference the symbol and whether the docstring is being added
- **AND** the plan steps include reviewing the implementation, drafting a factual docstring, and inserting it into the same module
- **AND** constraints forbid renames or behavior changes and require assumptions to be called out explicitly
- **AND** metadata captures the target file, symbol, symbol name, symbol type, and whether assumptions were needed

#### Scenario: Guardrails for missing docstring planner
- **GIVEN** the finding lacks required metadata or spans distant modules
- **WHEN** the planner executes
- **THEN** it raises an error instead of guessing and/or splits the work into multiple plans so each plan covers one module or tight symbol group

### Requirement: Planner strengthens `weak_docstring` findings
The planner MUST convert every `weak_docstring` finding into a `CleanupPlan` describing how to improve the docstring while preserving behavior, returning the plan in a list to follow the global planner contract.

#### Scenario: Improve docstring plan
- **GIVEN** a `Finding` with `category="weak_docstring"` and metadata (`symbol_type`, `qualified_name`, `symbol_name`, `lines_of_code`, `docstring_preview`)
- **WHEN** the planner runs
- **THEN** the plan notes weaknesses in the current docstring, outlines how to draft a stronger description, and instructs replacing the docstring in place
- **AND** constraints reiterate “no speculative guarantees” and “no API changes”
- **AND** metadata records the same per-symbol details plus a flag indicating this is an improvement rather than an addition

#### Scenario: Guardrails for weak docstring planner
- **GIVEN** a weak docstring finding missing metadata or referencing multiple modules
- **WHEN** the planner executes
- **THEN** it raises a `ValueError` for missing context and enforces single-module scope, emitting additional plans if needed to keep each plan small
