## 1. Define schemas, guardrails, and documentation

- [x] Expand `docs/butlerspec_plan.md#phase-4-1` so it locks down the plan/spec contract.
  - [x] Add a `#### Canonical plan JSON` subsection that spells out every key stored in `.ai-clean/plans/{id}.json`, including a fenced JSON example showing trimmed strings, ordered arrays, and the 32 KB `metadata` limit with a single `metadata.target_file` entry.
  - [x] Add a `#### ButlerSpec schema` subsection that lists each dataclass field, whether it is required or optional, the accepted `model` enum values, and the rule `spec.id = f"{plan.id}-spec"` (show a YAML example referencing the JSON sample).
  - [x] Add a `#### Phase 4.1 action vocabulary` subsection that documents the only supported action (`plan_step`) plus the reserved names for future phases, describing the required keys `type`, `index`, `summary`, and `payload`.
  - [x] Add a `#### Governance and error catalog` subsection that enumerates the exact `ValueError` strings to raise for missing targets, multiple targets, metadata overages, and intent/path mismatches; cross-link this subsection from the ButlerSpecBackend docstring.

- [x] Introduce code-level validation helpers so ButlerSpecBackend can reject malformed plans before emitting specs.
  - [x] Add `ai_clean/spec_backends/_validators.py` (new module) exporting helpers such as `ensure_single_target(metadata: dict[str, Any]) -> str`, `normalize_text_array(values: Sequence[str]) -> list[str]`, `assert_metadata_size(metadata: Mapping[str, Any]) -> None`, and a constant `PLAN_METADATA_LIMIT = 32 * 1024`.
  - [x] Write helper docstrings that reference the new documentation subsections (include the section anchors) and explain the exact guards (e.g., trimming whitespace, dropping blank entries, raising ValueErrors with deterministic wording).
  - [x] Import these helpers inside `ai_clean/spec_backends/butler.py` so `plan_to_spec` calls them instead of open-coded assertions; keep helpers private to the backend package by exposing them only from `_validators.py`.

## 2. Implement ButlerSpecBackend module

- [x] Create `ai_clean/spec_backends/__init__.py` that makes the backend importable.
  - [x] Add `from .butler import ButlerSpecBackend` and set `__all__ = ["ButlerSpecBackend"]` so downstream modules and tests do not import the private `_validators` module directly.
  - [x] Include a module docstring explaining that the package hosts ButlerSpec backend implementations.

- [x] Implement `ai_clean/spec_backends/butler.py` and wire it to the interface definitions.
  - [x] Import `BaseSpecBackend` (or the appropriate Protocol) from `ai_clean.interfaces`, `CleanupPlan/ButlerSpec` from `ai_clean.models`, `SpecBackendConfig` from `ai_clean.config`, and the helper functions from `_validators`.
  - [x] Add a module docstring referencing `docs/butlerspec_plan.md#phase-4-1` and describing the deterministic conversion pipeline implemented here.
  - [x] Define `class ButlerSpecBackend(BaseSpecBackend)` and include `__all__ = ["ButlerSpecBackend"]`.

- [x] Ensure the constructor accepts the correct configuration knobs.
  - [x] Accept `config: SpecBackendConfig`, optional `model_name: str = "codex"`, and optional `batch_group: str | None = None`.
  - [x] Store `_config`, `_model_name`, `_batch_group = batch_group or config.default_batch_group`, and `_specs_dir = config.specs_dir` for reuse in tests.
  - [x] Document each attribute with inline comments pointing to the doc sections that justify the defaults so later phases can reuse them.

- [x] Implement `plan_to_spec(self, plan: CleanupPlan) -> ButlerSpec` using the helper routines.
  - [x] Normalize plan identifiers, title, intent, and ordered `steps/constraints/tests_to_run` arrays (trim whitespace, drop empties, enforce ≤25 entries) before building the spec; raise `ValueError("CleanupPlan must include at least one step")` when the guards fail.
  - [x] Extract and validate `target_file` via `ensure_single_target`, raising `ValueError("ButlerSpec plans must declare exactly one target_file")` when the key is missing or blank and `ValueError("ButlerSpec plans must not declare multiple target files")` when conflicting metadata is present; validate intent/path mismatches via a helper that compares `plan.intent` to the normalized filename.
  - [x] Build deterministic identifiers/actions: `spec_id = f"{plan.id.strip()}-spec"`, and `actions = [{"type": "plan_step", "index": idx + 1, "summary": step, "payload": None}]` while ensuring `idx` ordering and action count guardrails.
  - [x] Copy `plan.metadata` into a new dict, augment it with `plan_title`, normalized `constraints`, and `tests_to_run`, and store the computed `target_file` so downstream callers never read the JSON plan again.
  - [x] Return a new `ButlerSpec` (without mutating `plan`) populated with the computed IDs, the incoming `intent`, the deterministic actions list, `model=self._model_name`, and `batch_group=self._batch_group`.

- [x] Override `write_spec` to block file persistence in this phase.
  - [x] Implement the method signature `def write_spec(self, spec: ButlerSpec, directory: Path | None = None) -> Path:` so later phases can extend it.
  - [x] Immediately raise `NotImplementedError("Phase 4.2 adds ButlerSpec file writing")` and mention this doc section in the error message so callers know why the operation is disallowed.

## 3. Validation and regression coverage

- [x] Add `tests/spec_backends/test_butler_backend.py` to exercise the backend end-to-end.
  - [x] Use `SpecBackendConfig(type="butler", default_batch_group="default", specs_dir=Path(".ai-clean/specs"))` in a `make_backend` helper so each test focuses on the behavior being validated.
  - [x] Provide a `_sample_plan(**overrides)` factory that builds `CleanupPlan` objects with realistic metadata (`target_file`, `constraints`, `tests_to_run`, `steps`).

- [x] Write a happy-path test that asserts every `ButlerSpec` field.
  - [x] Call `plan_to_spec` on the sample plan and assert the ID suffix (`-spec`), batch group default, action ordering, metadata copy (deep copy), and target file propagation.
  - [x] Assert the source `CleanupPlan` object (and its nested lists/dicts) are untouched after conversion by comparing ids/deep copies.

- [x] Cover governance failures with dedicated tests.
  - [x] `test_plan_to_spec_requires_target_file` → delete `target_file` and assert the exact `ValueError` message documented earlier.
  - [x] `test_plan_to_spec_rejects_multiple_targets` → provide extra metadata keys (e.g., `target_file_candidates`) and assert the multi-target error string.
  - [x] `test_plan_to_spec_rejects_oversized_metadata` → fabricate metadata above 32 KB and assert the raised `ValueError` mentions the size guard.
  - [x] `test_plan_to_spec_validates_intent_path_alignment` → mismatch the intent description vs. file path and assert the deterministic error text.

- [x] Prove determinism and immutability.
  - [x] `test_plan_to_spec_returns_new_metadata_dict` → mutate the returned `ButlerSpec.metadata` and assert the source plan metadata has not changed.
  - [x] `test_plan_to_spec_is_deterministic` → call the method twice and compare `spec.model_dump()` dictionaries to verify identical ordering for actions and metadata.

- [x] Validate plan serialization/canonicalization.
  - [x] Add a fixture JSON file under `tests/fixtures/plans/sample_plan.json` (or inline JSON string) that mimics `.ai-clean/plans/{id}.json`.
  - [x] Load the fixture, run it through the new helper/canonicalization path (e.g., `CleanupPlan.model_validate_json` + validator functions), and assert whitespace trimming, normalized ordering, and schema enforcement before backend conversion.
