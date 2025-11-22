## 1. Docstring planner scaffolding
- [x] 1.1 Add `ai_clean/planners/docstrings.py`.
  - [x] Start with `from __future__ import annotations` and document in a module docstring how docstring findings produce ButlerSpec-ready plans.
  - [x] Import `CleanupPlan`, `Finding`, `FindingLocation`, `ButlerConfig`, and typing helpers as needed.
  - [x] Implement the pure helper `plan_docstring_fix(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]` plus private validation helpers; planners must never touch the filesystem.
  - [x] Declare `__all__ = ["plan_docstring_fix"]` so no other helpers leak into the public API.
- [x] 1.2 Update `ai_clean/planners/__init__.py`.
  - [x] Add `from .docstrings import plan_docstring_fix` and include it in the alphabetized `__all__` list.
  - [x] Add a comment reminding future maintainers to keep exports sorted as additional planners arrive.

## 2. Plan generation for docstring fixes
- [x] 2.1 Implement `plan_docstring_fix`.
  - [x] Validate required metadata (`symbol_type`, `qualified_name`, `symbol_name`, `docstring_preview`, `lines_of_code`) and the presence of exactly one `FindingLocation`; raise `ValueError` with descriptive messages when missing.
  - [x] Capture `path = finding.locations[0].path` and convert to `path_str = path.as_posix()` for reuse, rejecting findings that span multiple files.
  - [x] Determine whether the category is `missing_docstring` or `weak_docstring` to control wording.
  - [x] Emit deterministic strings:
    - `plan_id = f"{finding.id}-docstring"`
    - `title = f"{'Add' if missing else 'Improve'} docstring for {qualified_name}"`
    - `intent = f"{'Add' if missing else 'Strengthen'} the docstring for {qualified_name} in {path_str} without changing behavior"`
  - [x] Build `steps` highlighting scope:
    1. “Review {qualified_name} in {path_str}:{start_line}-{end_line} (≈{lines_of_code} LOC).”
    2. “Draft a docstring covering purpose, parameters, return value, and edge cases using the provided preview/context.”
    3. “Insert or replace the docstring directly above {qualified_name} in {path_str}, matching indentation and style.”
  - [x] Set `constraints = ["No symbol renames or signature changes", "Docstring must describe existing behavior; explicitly state assumptions if unsure"]`.
  - [x] Choose `tests_to_run = [finding.metadata.get("test_command") or config.tests.default_command]` and raise `ValueError` when the result is falsy.
  - [x] Populate `plan.metadata` with `{"plan_kind": "docstring", "target_file": path_str, "qualified_name": qualified_name, "symbol_name": symbol_name, "symbol_type": symbol_type, "docstring_preview": preview, "lines_of_code": lines, "docstring_type": category, "scope": "single_module"}` plus optional flags such as `"assumptions_required": bool(not preview)`.
- [x] 2.2 Scope guardrails.
  - [x] Assert every `steps` entry references `path_str` so the plan never leaks into other files.
  - [x] Since each finding maps to one symbol, return a single-element list (while still following the global list-return signature) and drop any metadata expectations about `symbols` arrays.
  - [x] If metadata indicates >250 LOC or other review risks, set `metadata["requires_review_assistance"] = True` and mention the limitation in a constraint to keep reviewers aware.

- [x] 3.1 Create `tests/planners/test_docstring_planner.py`.
  - [x] Provide factory helpers to construct `Finding` instances for both `missing_docstring` and `weak_docstring` categories with deterministic metadata (including `symbol_name`).
  - [x] Assert plan ids always end with `-docstring`, titles/intents swap wording between “Add” and “Improve,” and each `steps` entry includes the same target file path + line numbers.
  - [x] Validate that constraints contain the “no signature changes” text and metadata mirrors analyzer inputs (preview, lines_of_code, symbol_type, symbol_name, docstring_type).
  - [x] Confirm the function returns a list containing exactly one `CleanupPlan` per finding and never performs disk I/O.
  - [x] Negative tests: missing metadata, zero locations, multi-file findings, and missing default test command should all raise `ValueError` with actionable messages.
