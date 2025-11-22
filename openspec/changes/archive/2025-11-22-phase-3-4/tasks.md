## 1. Organize planner scaffolding
- [x] 1.1 Add `ai_clean/planners/organize.py`.
  - [x] Start with `from __future__ import annotations`, import `Path`, typing helpers, `Finding`, `CleanupPlan`, and `ButlerConfig`.
  - [x] Document via module docstring that this planner only handles file moves and import adjustments—no code edits and no filesystem writes.
  - [x] Implement `plan_organize_candidate(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]` plus helpers `_derive_target_folder` and `_validate_members`.
  - [x] Expose `__all__ = ["plan_organize_candidate"]`.
- [x] 1.2 Update `ai_clean/planners/__init__.py`.
  - [x] Import the new helper and insert it into the alphabetized `__all__` list with a brief comment reminding maintainers to keep exports sorted.

## 2. Plan generation for organize candidates
- [x] 2.1 Implement `plan_organize_candidate`.
  - [x] Validate metadata contains non-empty `topic` and `files` (a list of file paths to move); raise `ValueError` otherwise.
  - [x] Convert each file path string into a `Path` for computation while preserving the original ordering for determinism.
  - [x] Invoke `_derive_target_folder(finding, config)` to compute the destination, capturing both the derived `Path` and whether re-exports are required.
  - [x] Allocate one `CleanupPlan` per source file (one-plan-per-file governance): `plan_id = f"{finding.id}-move-{index+1}"`, `title = f"Move {relative_file} into {target_dir}"`, and `intent = f"Move {topic} file {relative_file} into {target_dir} and update imports without altering code bodies"`.
  - [x] Build `steps` for each plan:
    1. “Create {target_dir}` if missing and explain why the folder groups the `{topic}` files.”
    2. “Move {relative_file} to {target_dir}/{relative_file.name} and keep relative imports intact.”
    3. “Update imports/re-exports referencing {relative_file} without modifying function bodies.”
  - [x] Set `constraints = ["No changes inside function/class bodies", "Do not introduce nested packages beyond {target_dir}", "Ensure re-exports maintain the existing public API"]`.
  - [x] Compute `tests_to_run = [finding.metadata.get("test_command") or config.tests.default_command]`, raising `ValueError` when the resolved command is falsy.
  - [x] Populate `plan.metadata` with `{"plan_kind": "organize", "topic": topic, "target_directory": target_dir, "file": relative_file.as_posix(), "split_index": index, "batch_size": len(files), "requires_reexports": target.requires_reexports}`.
- [x] 2.2 Implement `_derive_target_folder`.
  - [x] Introduce `@dataclass class TargetInfo: path: Path; requires_reexports: bool` with a docstring describing what the flag represents.
  - [x] Determine the shallowest shared parent across all files; if no shared parent exists, fall back to `files[0].parent`.
  - [x] Append a slugified form of `topic` (lowercase, spaces → `-`) to this parent to form the destination path.
  - [x] Guard depth by ensuring the derived folder is no more than two levels deeper than the shared parent; raise `ValueError` if violated.
  - [x] Return `TargetInfo` with the computed path and a boolean flag indicating whether re-export stubs are required (based on whether any file originated from a package `__init__.py` or public API module).
- [x] 2.3 Enforce “small set” constraints.
  - [x] Reject disjoint parent folders by raising `ValueError` instructing analyzers to emit separate findings.
  - [x] Keep the `files` list capped at five entries per finding; analyzers must emit multiple findings for larger groups.
  - [x] Include `split_index` / `batch_size` metadata to help downstream orchestration reason about multi-plan findings.

- [x] 3.1 Create `tests/planners/test_organize_planner.py`.
  - [x] Provide helper factories to construct `Finding` objects with `topic`/`files` metadata referencing `Path("src/payments/card.py")` style inputs.
  - [x] Assert the generated plan ids are suffixed with `-move-{index}`; titles/intents mention both `topic`, the specific file, and the derived folder, and every step includes the affected file names.
  - [x] Verify constraints contain the “no function body changes” guardrail and metadata echoes the `file`, `target_directory`, `split_index`, `batch_size`, and `requires_reexports` values.
  - [x] Test `_derive_target_folder` for scenarios: existing destination folder, new folder creation, requiring slugified topics, and detecting overly deep targets.
  - [x] Add tests covering oversized file lists (ensuring analyzers must split findings), missing metadata, disjoint parents, and empty test commands to confirm guardrails raise `ValueError`.
