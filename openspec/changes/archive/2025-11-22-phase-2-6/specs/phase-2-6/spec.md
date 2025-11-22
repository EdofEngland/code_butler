## ADDED Requirements

### Requirement: Phase 2.6 – Codex-Powered Advanced Cleanup Analyzer
The ai-clean project MUST fulfill the deliverables for Phase 2.6 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Prompt construction and Codex call
- **GIVEN** selected files/snippets and prior findings
- **WHEN** the advanced analyzer runs
- **THEN** it builds a prompt using the configured template, injects snippets + finding summaries, and sends it to Codex via the prompt runner.

#### Scenario: Suggestion validation and conversion
- **GIVEN** Codex returns structured suggestions
- **WHEN** the analyzer parses the payload
- **THEN** each valid suggestion becomes an `advanced_cleanup` finding with metadata for file, line range, change type, model, and prompt hash.
- **AND** IDs are deterministic (hash of file + description).

#### Scenario: Guardrails
- **GIVEN** the analyzer enforces `max_files`, `max_suggestions`, and allowed change types
- **WHEN** Codex returns suggestions exceeding limits or referencing disallowed files/change types
- **THEN** the analyzer truncates/rejects them, logs reasons, and records truncation metadata in the findings list.

#### Scenario: Deterministic execution and logging
- **GIVEN** identical inputs and Codex responses
- **WHEN** the analyzer runs twice
- **THEN** the finding list (IDs/order/metadata) is identical and logs include summary counts for selected files, suggestions accepted, and suggestions dropped.
