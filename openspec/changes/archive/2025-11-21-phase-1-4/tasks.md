## 1. Deliverables

### 1.4.1 Repository config file
- [x] Create `ai-clean.toml` in the repo root that defines:
  - [x] `[spec_backend] type = "butler"` plus a `default_batch_group = "default"` key.
  - [x] `[executor] type = "codex_shell"` with `binary = "codex"` and `apply_args = ["apply"]`.
  - [x] `[review] type = "codex_review"` with `mode = "summarize-and-risk"`.
  - [x] `[git] base_branch = "main"` and `refactor_branch = "refactor/ai-clean"`.
  - [x] `[tests] default_command = "pytest -q"`.
  - [x] Inline comments reminding contributors that these blocks map directly to the "Phase 1 System Sketch" pipeline.

### 1.4.2 Metadata directories
- [x] Update the CLI bootstrap (e.g., `ai_clean/cli.py`) to call a helper `ensure_metadata_dirs()` before running commands; the helper should create `.ai-clean/plans`, `.ai-clean/specs`, `.ai-clean/results` via `Path(".ai-clean").joinpath(...).mkdir(parents=True, exist_ok=True)` using the default path helpers defined in Phase 1.2.
- [x] Ensure the helper runs once per invocation (before parsing args) and logs where artifacts will be written.
- [x] Add `.ai-clean/` to `.gitignore` to keep generated plans/specs/results out of version control.

### 1.4.3 Config loader module
- [x] Implement `ai_clean/config.py` with dataclasses `SpecBackendConfig`, `ExecutorConfig`, `ReviewConfig`, `GitConfig`, `TestsConfig`, and a wrapper `AiCleanConfig` that stores resolved metadata directories.
- [x] Provide a `load_config(path: Path | None = None) -> AiCleanConfig` function that:
  - [x] Uses stdlib `tomllib` to parse TOML.
  - [x] Validates required keys, raising `ValueError` with actionable error messages when missing.
  - [x] Expands relative paths to absolute `Path` objects where appropriate (e.g., metadata directories) and defaults to `.ai-clean/` directories when values are omitted.
  - [x] Surfaces the default plan/spec/result path helpers from Phase 1.2 so loader outputs and model serialization stay consistent.

### 1.4.4 Factories consuming config
- [x] Add `ai_clean/factories.py` with helpers `get_spec_backend(config)`, `get_executor(config)`, and `get_review_executor(config)` that read from the typed config objects and instantiate placeholder implementations compatible with the Phase 1.3 Protocols.
- [x] Wire the factories so they expose metadata directory Paths (e.g., for writing specs/results) alongside the instantiated components.
- [x] Include unit tests (e.g., `tests/test_config_loader.py`) covering:
  - [x] Happy-path load + helper usage.
  - [x] Failure when a key is missing or malformed.
  - [x] Failure when the config references unsupported backend/executor/review types.
