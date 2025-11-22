## 1. Deterministic plan ID helper
- [x] 1.1 Define `generate_plan_id(finding_id: str, suffix: str) -> str` inside `ai_clean/planners/orchestrator.py`.
  - [x] Add a pure helper function (top-level, module-private) with a docstring describing the `<finding-id>-<suffix>` contract and deterministic behavior.
  - [x] Implement normalization: `finding_id.strip().lower()`, `suffix.strip().lower()`, join with `"-"`, and collapse repeated `-` so callers cannot sneak whitespace into IDs.
  - [x] Validate `suffix` and resulting ID using a regex that allows `[a-z0-9-]` only; raise `ValueError("invalid plan ID suffix: ...")` when violated.
  - [x] Include at least one inline doctest/example in the docstring (`>>> generate_plan_id("Finding-123", "Doc")  # -> "finding-123-doc"`) to document stability.
- [x] 1.2 Update `ai_clean/planners/__init__.py`.
  - [x] Import `generate_plan_id` from `.orchestrator` and add it to `__all__` so external modules share the helper.

## 2. Serialization helper
- [x] 2.1 Add `write_plan_to_disk(plan: CleanupPlan, base_dir: Path) -> Path` to `ai_clean/planners/orchestrator.py` (or adjacent module if more appropriate).
  - [x] Resolve the output path via `destination = base_dir / f"{plan.id}.json"` and call `destination.parent.mkdir(parents=True, exist_ok=True)`.
  - [x] Write the plan JSON using `destination.write_text(plan.to_json(indent=2), encoding="utf-8")` and return `destination`.
  - [x] Keep the helper side-effect-free beyond the file write (no logging/printing) so tests can assert path + file contents deterministically.
- [x] 2.2 Re-export serialization symbols.
  - [x] Add `write_plan_to_disk` to the module `__all__` list.
  - [x] Import and re-export it in `ai_clean/planners/__init__.py` next to `generate_plan_id`.

## 3. Planning orchestrator module
- [x] 3.1 Create or extend `ai_clean/planners/orchestrator.py` with deterministic dispatch data.
  - [x] Define `_CATEGORY_DISPATCH: dict[str, PlannerCallable]` mapping each `Finding.category` to the correct Phase 3.x helper; annotate the callable signature for clarity.
  - [x] Implement `_plan_duplicate_block(finding, config)` that wraps `plan_duplicate_blocks([finding], config)` and simply returns the resulting list; planners now control batching so no single-plan enforcement happens here.
  - [x] Wire `_CATEGORY_DISPATCH = {"duplicate_block": _plan_duplicate_block, "large_file": plan_large_file, ...}` covering all categories from Phases 3.1–3.5.
  - [x] Ensure module imports for every helper exist at the top of the file and keep ordering alphabetical for lint predictability.
- [x] 3.2 Implement `plan_from_finding(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]`.
  - [x] Look up the callable via `_CATEGORY_DISPATCH[finding.category]`, raising `NotImplementedError(f"Unsupported finding category: {finding.category}")` if missing.
  - [x] Execute the dispatcher to obtain the list of plans (length may be zero, one, or greater) and return it verbatim without writing to disk.
  - [x] Leave plan persistence to the caller (e.g., CLI) using `write_plan_to_disk(plan, config.plans_dir)`.
  - [x] Update `__all__` so `plan_from_finding`, `generate_plan_id`, and `write_plan_to_disk` are exported for reuse.

- [x] 4.1 Create `tests/planners/test_orchestrator.py`.
  - [x] Use `unittest.mock.patch` on each planner helper to assert the orchestrator routes every category call (`duplicate_block`, `large_file`, etc.) to the expected function exactly once.
  - [x] Add test `test_duplicate_block_passthrough` that stubs the duplicate planner to return multiple plans and asserts the orchestrator returns them unchanged without raising.
  - [x] Add test `test_unknown_category` to assert `NotImplementedError` includes the category name when `_CATEGORY_DISPATCH` lacks an entry.
  - [x] Configure a temporary directory for `ButlerConfig.plans_dir`, call `plan_from_finding` to obtain plans, loop over them, and invoke `write_plan_to_disk` to confirm `.ai-clean/plans/{plan_id}.json` exists with JSON matching `plan.to_json()`.
  - [x] Add positive/negative tests for `generate_plan_id` (valid suffix, uppercase input normalization, invalid characters raising `ValueError`).
