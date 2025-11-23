## 1. Plan storage helpers

- [x] 1.1 Create `ai_clean/plans.py` with `save_plan(plan: CleanupPlan, root: Path | None = None) -> Path` that writes `plan.to_json()` to `root or default_metadata_root()/plans/{plan.id}.json`, ensuring parent directories exist.
- [x] 1.2 Add `load_plan(plan_id: str, root: Path | None = None) -> CleanupPlan` in `ai_clean/plans.py` that reads the matching JSON file (same path rule), raises `FileNotFoundError` when missing, and returns `CleanupPlan.from_json(...)`.
- [x] 1.3 Expose these helpers via `ai_clean/__init__.py` (or module exports) so other code can import them deterministically.

## 2. Round-trip guarantees

- [x] 2.1 Add unit tests (e.g., `tests/test_plans.py`) covering `save_plan` then `load_plan` round-trip equality for required fields and metadata.
- [x] 2.2 Add a test that `load_plan` raises a clear `FileNotFoundError` when the plan file is absent.
