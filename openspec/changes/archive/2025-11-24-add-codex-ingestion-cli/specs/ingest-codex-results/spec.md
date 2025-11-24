## ADDED Requirements
### Requirement: Codex artifact ingestion
The system SHALL ingest Codex slash-command artifacts into `ExecutionResult` with strict validation.

#### Scenario: Valid artifact updates execution result
- **WHEN** the user runs `ai-clean ingest --plan-id <id> --artifact <path>` with a JSON artifact containing unified `diff`, `stdout`, `stderr`, and a `tests` block (`status`, `command`, `exit_code`, `stdout`, `stderr`)
- **AND** the artifact (optionally) includes `plan_id` that matches the CLI `--plan-id`
- **THEN** the command parses and validates the payload, rejects multi-file diffs, and sets `ExecutionResult.metadata.manual_execution_required=False`
- **AND** it writes `git_diff`, `stdout`, `stderr`, and `metadata.tests` from the artifact, derives `success`/`tests_passed`, and persists to `.ai-clean/results/<plan>.json`
- **AND** it prints a summary showing diff stats and tests status

#### Scenario: Invalid artifact is rejected
- **WHEN** the artifact is missing required fields, has a non-unified or empty diff without an apply failure, includes unexpected fields, or an unsupported tests status
- **THEN** the ingest command exits with an error and does NOT update the saved `ExecutionResult`

#### Scenario: Mismatched plan is rejected
- **WHEN** the artifact includes `plan_id` that does not match the CLI `--plan-id`
- **THEN** ingest aborts with an error and leaves the saved `ExecutionResult` unchanged

#### Scenario: Apply failure with no diff
- **WHEN** the artifact reports `tests.status=apply_failed` and omits the diff
- **THEN** ingest accepts the artifact, sets `success=False`, `tests_passed=None`, stores stdout/stderr, and persists the failure for diagnosis
