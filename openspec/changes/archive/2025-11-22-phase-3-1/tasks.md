## 1. Planner scaffolding
- [x] 1.1 Create `ai_clean/planners/__init__.py`.
  - [x] Add a module docstring (“Planner entrypoints for ai-clean”) and import guard `from __future__ import annotations`.
  - [x] Import `plan_duplicate_blocks` from `.duplicate` and expose `__all__ = ["plan_duplicate_blocks"]`.
  - [x] Ensure `__all__` stays alphabetized when later planners are appended.
- [x] 1.2 Add `ai_clean/planners/duplicate.py`.
  - [x] Include imports for `collections`, `itertools`, `pathlib.Path`, `typing.Sequence`, and the relevant core models plus `ButlerConfig`.
  - [x] Add a module docstring describing how duplicate analyzer output is transformed into pure `CleanupPlan` objects.
  - [x] Define `plan_duplicate_blocks(findings: Sequence[Finding], config: ButlerConfig) -> list[CleanupPlan]` plus private helpers for grouping/splitting, helper-path selection, and plan sorting; planners never touch the filesystem.
  - [x] Export only `plan_duplicate_blocks` via `__all__` to keep the public surface narrow.
- [x] 1.3 Update `ai_clean/__init__.py`.
  - [x] Import the `planners` package and add `planners` (and optionally `plan_duplicate_blocks`) to the package `__all__` so `from ai_clean import planners` works out of the box.

- [x] 2.1 Add `_group_duplicates(findings: Sequence[Finding]) -> dict[HelperKey, list[Finding]]`.
  - [x] Use a deterministic key (e.g., tuple of helper path + analyzer group id) so identical inputs always produce the same group ordering.
  - [x] Ensure each group contains only findings pointing at the same helper target and cap the list to three entries per plan; spill extras into additional groups with predictable suffixes like `"{key}-2"`.
  - [x] Document the grouping logic inline so later contributors understand the helper-target invariant.
- [x] 2.2 Implement `_select_helper_path(locations: Sequence[FindingLocation]) -> Path`.
  - [x] Default helper placement to the module containing the first occurrence (`locations[0].path`), documenting this contract with a comment (“later configs may override helper placement”).
  - [x] When duplicates span multiple modules, compute the shallowest shared parent `Path` by intersecting `.parents()`; if no shared parent exists, fall back to the first occurrence path.
  - [x] Always serialize the chosen path to POSIX via `.as_posix()` before storing it in metadata to avoid OS-specific separators.
- [x] 2.3 Preserve ordering.
  - [x] Sort each group’s findings by `(location.path.as_posix(), location.start_line)` before downstream steps so plan generation references duplicates deterministically.
  - [x] Carry the sorted ordering into metadata (e.g., list of occurrences) for traceability.

## 3. CleanupPlan construction
- [x] 3.1 Add `_build_plan(group: list[Finding], helper_path: Path, config: ButlerConfig) -> CleanupPlan`.
  - [x] Generate plan ids using a deterministic format such as `f"{group[0].id}-helper-{index}"` where `index` counts the spillover groups; document the convention in a docstring.
  - [x] Derive `title = f"Extract helper into {helper_path.name}"` and `intent = f"Create shared helper at {helper_path.as_posix()} and replace duplicates"` with data from the helper path + first finding description.
- [x] 3.2 Build ordered plan steps.
  - [x] Step 1: Decide the helper signature and document referencing the files/line numbers pulled from the grouped findings.
  - [x] Step 2: Create the helper in `helper_path` describing docstring expectations and the default naming convention (derived from the helper path until future configs add overrides).
  - [x] Step 3+: For each duplicate occurrence, add a step “Replace lines X–Y in <file> with helper call” referencing the path and range from the sorted findings.
- [x] 3.3 Populate guardrails.
  - [x] Set `constraints` to include “Do not change public APIs in <module>” and “Keep helper pure; no global state,” deriving module names directly from the helper path string.
  - [x] Set `tests_to_run` to `[finding.metadata.get("test_command") or config.tests.default_command]`; raise `ValueError` when this resolves to `None` or an empty string.
  - [x] Copy analyzer metadata (duplicate hashes, similarity score, original line ranges) into `plan.metadata` alongside `helper_path` and occurrence ordering.

## 4. Plan splitting and ordering
- [x] 4.1 Enforce limits.
  - [x] In `plan_duplicate_blocks`, iterate each helper-target group and split it into chunks of ≤3 findings, calling `_build_plan` per chunk.
  - [x] Guard against mixing helper targets: if a finding references a different helper_path than the group key, raise `ValueError`.
- [x] 4.2 Deterministic ordering.
  - [x] Sort the resulting `CleanupPlan` list by `(plan.metadata["helper_path"], plan.metadata["occurrences"][0]["start_line"])`.
  - [x] Add inline comments explaining the ordering so regression reviewers understand the guarantee.

## 5. Tests
- [x] 5.1 Create `tests/planners/test_duplicate_planner.py`.
  - [x] Build helper functions that create `Finding`/`FindingLocation` instances with synthetic paths (use `Path("src/app.py")` to stay platform-neutral).
  - [x] Write tests for single-file duplicates, multi-file duplicates, and helper fallback behavior; assert each plan references the expected helper path and step ordering.
  - [x] Add tests ensuring groups larger than three split into multiple plans and that the resulting plans are sorted by helper path + first occurrence.
  - [x] Verify metadata includes occurrence ordering, helper path, and analyzer hint fields.
- [x] 5.2 Guardrails only.
  - [x] Add negative tests verifying missing config test commands or helper-path mismatches raise `ValueError`.
