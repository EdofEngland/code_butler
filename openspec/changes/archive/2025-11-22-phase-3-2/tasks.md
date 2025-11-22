## 1. Structure planner scaffolding
- [x] 1.1 Create `ai_clean/planners/structure.py`.
  - [x] Add `from __future__ import annotations` and describe the file purpose in a module docstring.
  - [x] Import `CleanupPlan`, `Finding`, `ButlerConfig`, and typing helpers used throughout (`Sequence`, `list`, etc.).
  - [x] Define pure helpers `plan_large_file(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]` and `plan_long_function(...)` that return lists of plans and never touch the filesystem.
  - [x] Declare `__all__ = ["plan_large_file", "plan_long_function"]` to limit exports.
- [x] 1.2 Update `ai_clean/planners/__init__.py`.
  - [x] Import both helpers from `.structure`.
  - [x] Append them to `__all__` in alphabetical order (e.g., `["plan_advanced_cleanup", "plan_docstring_fix", "plan_duplicate_blocks", "plan_large_file", ...]` once all planners exist).
  - [x] Add short inline comments reminding future maintainers to keep the list sorted.

- [x] 2.1 Implement `plan_large_file`.
  - [x] Extract `target_path = finding.locations[0].path` and convert to POSIX string once (e.g., `target_file = target_path.as_posix()`), raising `ValueError` if `finding.locations` is empty.
  - [x] Validate metadata presence for `line_count` and `threshold`; call `raise ValueError("large_file findings require line_count and threshold metadata")` when missing.
  - [x] Build deterministic identifiers: `plan_id = f"{finding.id}-split"`, `title = f"Split {target_file} into focused modules"`, and `intent = f"Split {target_file} into 2–3 logical modules while preserving imports`.
  - [x] Compose steps:
    1. “Analyze {target_file} (lines {start}-{end}) and group code by responsibility.”
    2. “Create new modules {module_targets} under {target_file}'s package and move code accordingly.”
    3. “Update imports, re-exports, and tests to reference the new modules.”
  - [x] Force each step to include `{target_file}` or derived module paths so scope is explicit.
  - [x] Set `constraints = [f"Preserve public API by re-exporting from {target_file}", "Do not change function/class behavior"]`.
  - [x] Choose `test_command = finding.metadata.get("test_command") or config.tests.default_command` and raise `ValueError` if falsy; set `tests_to_run = [test_command]`.
  - [x] Populate `metadata` with `plan_kind`, `target_file`, `line_count`, `threshold`, and module clustering output.
- [x] 2.2 Implement `_cluster_module_targets(locations: Sequence[FindingLocation], *, max_modules: int = 3) -> ClusteredTargets`.
  - [x] Define `@dataclass class ClusteredTargets: primary_modules: list[Path]; leftover_segments: list[FindingLocation]` near the top of the module with a docstring explaining how leftovers trigger additional plans.
  - [x] Group spans by approximate responsibility using ordering by `start_line` and chunk into ≤`max_modules` sequences; convert each chunk into suggested module names/paths (e.g., `{stem}_{index}`) stored in `primary_modules`.
  - [x] When there are more chunks than allowed, place the extra `FindingLocation` objects in `leftover_segments` so callers can schedule new plans deterministically.
- [x] 2.3 Enforce guardrails.
  - [x] Inside `plan_large_file`, call `_cluster_module_targets` and build at most one plan from `primary_modules`. When `leftover_segments` is non-empty, record that work is incomplete (e.g., via metadata or by requesting follow-up plans) instead of guessing.
  - [x] Ensure at least one step or constraint explicitly mentions re-exporting from the original file; unit tests should check for the substring “re-export”.
  - [x] Add inline comments referencing the ButlerSpec requirement (“one plan per file”) so contributors do not widen scope later.

- [x] 3.1 Implement `plan_long_function`.
  - [x] Require `finding.locations` to contain a single entry; raise `ValueError` otherwise.
  - [x] Read `qualified_name` and `line_count` from metadata; derive `start_line`/`end_line` from `finding.locations[0]` (trusting the analyzer span).
  - [x] Build deterministic identifiers: `plan_id = f"{finding.id}-helpers"`, `title = f"Extract helpers for {qualified_name} in {target_file}"`, and `intent = f"Break {qualified_name} into helpers without changing behavior"`.
  - [x] Compose steps referencing the captured line span:
    1. “Review {qualified_name} in {target_file}:{start_line}-{end_line} and list logical blocks.”
    2. “Extract each block into helper functions prefixed `{qualified_name}_...` in {target_file}.”
    3. “Replace the original block bodies with helper calls and re-run targeted tests.”
  - [x] Constraints should mention “Do not change function signature or side effects” and “Limit edits to {target_file}”.
  - [x] Choose `tests_to_run = [finding.metadata.get("test_command") or config.tests.default_command]`, validating non-empty.
  - [x] Store metadata keys: `plan_kind`, `target_file`, `function`, `line_count`, `start_line`, `end_line`, and helper hints (e.g., `"helper_prefix": qualified_name.split(".")[-1]`).
- [x] 3.2 Additional guardrails.
  - [x] When metadata indicates nested helper suggestions (e.g., `finding.metadata["segments"]`), ensure the plan references each segment inside `steps` or `metadata["segments"]`.
  - [x] Add a boolean flag `metadata["scope"] = "single_function"` to make the limitation explicit.
  - [x] Avoid re-checking analyzer thresholds; raise only for missing metadata or multiple locations.

- [x] 4.1 Create `tests/planners/test_structure_planner.py`.
  - [x] Add `make_finding` helpers returning `Finding` objects with `Path("src/module.py")` paths to keep assertions OS-independent.
  - [x] Write tests asserting `plan_large_file` uses the `-split` suffix, embeds module target names in steps, and copies metadata (`line_count`, `threshold`, `module_targets`).
  - [x] Test `_cluster_module_targets` by providing >3 segments and assert the helper surfaces the `ClusteredTargets.leftover_segments` list for follow-up planning.
  - [x] Verify `plan_long_function` includes the qualified name + line range extracted from the `FindingLocation` in every step, constraints mention scope limitations, and metadata contains helper hints.
  - [x] Negative tests: missing metadata, multiple locations, empty `config.tests.default_command`, or absent `finding.locations` should raise `ValueError` with actionable messages.
