## 1. Advanced cleanup planner scaffolding
- [x] 1.1 Create `ai_clean/planners/advanced.py`.
  - [x] Add `from __future__ import annotations`, import `CleanupPlan`, `Finding`, `ButlerConfig`, `Path`, and typing helpers.
  - [x] Document via module docstring that the planner turns Codex-suggested findings into ButlerSpec plans with strict scope control and no filesystem writes.
  - [x] Implement `plan_advanced_cleanup(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]` plus helper functions `_validate_metadata` and `_build_steps`.
  - [x] Expose `__all__ = ["plan_advanced_cleanup"]`.
- [x] 1.2 Update `ai_clean/planners/__init__.py`.
  - [x] Import the helper from `.advanced` and include it in the alphabetized `__all__`.
  - [x] Comment that advanced plans must remain opt-in (referencing the docstring) so future maintainers treat it carefully.

- [x] 2.1 Implement `plan_advanced_cleanup`.
  - [x] Require exactly one `FindingLocation`; raise `ValueError` otherwise.
  - [x] Read metadata keys `target_path`, `start_line`, `end_line`, `change_type`, `prompt_hash`, `codex_model`, and optional `test_command`, `description`.
  - [x] Validate that `start_line < end_line`, all fields above exist, and `end_line - start_line + 1` is ≤ the configured threshold (e.g., 25 lines); raise `ValueError` with descriptive text when violated.
  - [x] Convert `target_path`/location path to a POSIX string stored in `target_file`.
  - [x] Emit deterministic identifiers: `plan_id = f"{finding.id}-plan"`, `title = f"{change_type.capitalize()} in {target_file}"`, and `intent = f"Apply Codex-suggested {change_type} limited to lines {start_line}-{end_line} of {target_file}"`.
  - [x] Build ordered steps:
    1. “Review the Codex suggestion (prompt hash, description) and confirm the change still applies to {target_file}:{start_line}-{end_line}.”
    2. “Implement the described change strictly within {target_file}:{start_line}-{end_line}, referencing the snippet in metadata.”
    3. “Run the specified tests (`test_command` or default) and verify no unrelated files changed.”
  - [x] Set `constraints = [f"Limit edits to {target_file}:{start_line}-{end_line}", "Do not introduce unrelated refactors or API changes", "Keep coding style consistent with existing file"]`.
  - [x] Determine `tests_to_run = [finding.metadata.get("test_command") or config.tests.default_command]` and reject falsy results.
  - [x] Populate metadata with all analyzer fields plus derived data (`{"plan_kind": "advanced_cleanup", "target_file": target_file, "start_line": start_line, "end_line": end_line, "line_span": line_span, "change_type": change_type, "prompt_hash": prompt_hash, "codex_model": codex_model}`) so downstream tooling can correlate to the original suggestion.
- [x] 2.2 Keep scope intentionally small.
  - [x] If the finding references multiple files or multiple Codex suggestions (e.g., `finding.metadata["suggestions"]` array), split them into separate plans (returning multiple `CleanupPlan`s in the list) or raise `ValueError` instructing the analyzer to emit granular findings.
  - [x] Limit `steps` to the three bullets above to keep ButlerSpec instructions concise; add inline comments inside code to enforce this behavior.
  - [x] When metadata indicates optional follow-up actions, encode them as additional constraints rather than expanding steps to avoid scope creep.

- [x] 3.1 Create `tests/planners/test_advanced_planner.py`.
  - [x] Build fixture helpers generating `Finding` objects with `Path("src/service.py")` and metadata mirroring `collect_advanced_cleanup_ideas`.
  - [x] Assert generated plan ids end with `-plan`, titles/intents mention `target_file` and `change_type`, and steps include the exact `start_line`–`end_line` range.
  - [x] Verify metadata copies prompt hash, codex model, and computed `line_span`; ensure `tests_to_run` respects `test_command` overrides or defaults.
  - [x] Add negative tests for missing metadata, multi-location findings, spans where `start_line >= end_line`, spans > threshold, and findings lacking test commands—all should raise `ValueError`.
  - [x] Include a test that ensures multiple suggestions trigger either multiple plans in the returned list or `ValueError`, confirming scope enforcement.
