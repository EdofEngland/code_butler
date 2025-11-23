## 1. Document YAML schema and guardrails

- [x] Expand `docs/butlerspec_plan.md#phase-4-2` with concrete persistence guidance tied to the code being added in this phase.
  - [x] Add a `#### ButlerSpec YAML schema` subsection showing the serialized key order (id, plan_id, target_file, intent, model, batch_group, actions, metadata), the required indentation level (2 spaces), UTF-8 encoding, and the trailing newline requirement; include a fenced YAML example produced by the new backend serializer.
  - [x] Document the guardrails that `write_spec` enforces (single target file, ≤25 actions, ≤32 KB metadata) and reference the helper functions added in Phase 4.1.
  - [x] Describe filesystem expectations including the default `.ai-clean/specs/` root, automatic `mkdir(parents=True, exist_ok=True)`, file naming pattern `{spec.id}.butler.yaml`, and deterministic overwrite semantics (compare bytes before rewriting).

- [x] Capture non-goals/assumptions beneath the Phase 4.2 heading so scope remains fixed.
  - [x] Write a short paragraph stating that batching, compression, and remote persistence layers are explicitly out of scope for this change.
  - [x] Mention that YAML signing/checksums will be tracked in later proposals so reviewers know why the helper stops at deterministic file writes.

## 2. Implement deterministic persistence helpers

- [x] Replace the Phase 4.1 `NotImplementedError` inside `ai_clean/spec_backends/butler.py::write_spec` with the real persistence logic.
  - [x] Accept `directory: Path | None`; when `None`, default to `self._specs_dir` captured in the constructor.
  - [x] Call the shared validation helpers to re-check guardrails (`ensure_single_target`, action count, metadata size) before touching the filesystem.
  - [x] Compute `spec_path = (directory or self._specs_dir) / f"{spec.id}.butler.yaml"` and call `spec_path.parent.mkdir(parents=True, exist_ok=True)`.
  - [x] Serialize the spec using a helper (`_serialize_butler_spec`) that calls `spec.model_dump()` and writes YAML with deterministic key ordering plus a trailing newline; write bytes via `spec_path.write_text(payload, encoding="utf-8")`.
  - [x] If the file already exists, read its bytes first and skip the write when the serialized payload matches; when bytes differ, overwrite and log/emit a warning via the module-level logger.
  - [x] Return `spec_path`.

- [x] Update shared helpers/examples to honor the `.butler.yaml` suffix and new directory behavior.
  - [x] Update `ai_clean/paths.py::default_spec_path` (and any re-export in `ai_clean/models/__init__.py`) to include the `.butler.yaml` suffix.
  - [x] Adjust `examples/model_roundtrip.py` and `examples/interfaces_usage.py` so they mention the `.butler.yaml` filenames when demonstrating spec persistence.
  - [x] Grep for `.yaml` references in README/config/test files and update them to the `.butler.yaml` extension so the documentation/fixtures match the guardrails.

## 3. Add regression and filesystem coverage

- [x] Extend `tests/spec_backends/test_butler_backend.py` with persistence-focused tests.
  - [x] `test_write_spec_round_trip` → call `write_spec`, assert the file exists, read it back via `ButlerSpec.from_yaml`, and compare to the original object.
  - [x] `test_write_spec_creates_parent_directories` → point the backend at a temporary nested path, delete it, and assert `write_spec` recreates it during the call.
  - [x] `test_write_spec_guardrails` → verify multi-target metadata, too many actions, or metadata >32 KB causes the method to raise before writing any bytes.
  - [x] `test_write_spec_deterministic_overwrite` → write once, write again with the same spec (assert file timestamp unchanged or bytes identical), then modify a field and assert the method overwrites the file and emits a warning via `caplog`.
  - [x] `test_write_spec_permission_error_bubbles` → use `monkeypatch` to point at a read-only directory and confirm the raised `PermissionError` surfaces with a helpful message.

- [x] Update config/path-related tests to assert the new suffix.
  - [x] In `tests/test_config_loader.py::ConfigLoaderTests.test_load_config_happy_path`, assert the returned `SpecBackendHandle.specs_dir` contains `.butler.yaml` files when `default_spec_path` is invoked.
  - [x] Audit other tests under `tests/` (grep for `.yaml`) and update expectations/fixtures so they assert `.butler.yaml` instead of `.yaml`.
