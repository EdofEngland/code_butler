# phase-1-4 Specification

## Purpose
TBD - created by archiving change phase-1-4. Update Purpose after archive.
## Requirements
### Requirement: ai-clean.toml encodes ButlerSpec pipeline
The repository MUST ship an `ai-clean.toml` whose sections mirror the spec backend, executor, review, git, and tests blocks from the Phase 1 system sketch.

#### Scenario: Config file includes guardrail comments
- **WHEN** maintainers open `ai-clean.toml`
- **THEN** they see the sections listed above with inline comments referencing ButlerSpec guardrails and default batch group / apply args.

### Requirement: Metadata directories are ensured on startup
Running any CLI command MUST create `.ai-clean/plans`, `.ai-clean/specs`, and `.ai-clean/results` before further work happens.

#### Scenario: ensure_metadata_dirs executes first
- **WHEN** `python -m ai_clean.cli --help` runs
- **THEN** the helper logs the resolved directories (using Phase 1.2 path helpers) and the folders exist afterward even if they were missing before.

### Requirement: Typed config loader validates inputs
The codebase MUST expose dataclasses and a loader that parse `ai-clean.toml`, resolve default directories, and throw actionable errors.

#### Scenario: load_config resolves metadata paths
- **WHEN** `load_config()` executes without arguments
- **THEN** it returns `AiCleanConfig` populated with `Path` objects pointing at `.ai-clean/plans|specs|results`
- **AND** raising `ValueError` when a required section/key is absent.

### Requirement: Factories connect config to Protocols
Helper functions MUST translate the typed config into concrete (even if placeholder) implementations for SpecBackend, CodeExecutor, and ReviewExecutor.

#### Scenario: Factories surface implementations + directories
- **WHEN** `get_spec_backend(load_config())` runs
- **THEN** it returns an object (or stub) compatible with the SpecBackend Protocol along with the directory for writing specs, ensuring CLI commands know exactly where to store artifacts.

### Requirement: Tests enforce deterministic behavior
Unit tests MUST cover successful loads and failure cases so later phases can rely on this foundation.

#### Scenario: Config loader tests cover happy path and errors
- **WHEN** `pytest tests/test_config_loader.py -k phase1` is executed
- **THEN** it asserts that valid configs load, missing sections raise `ValueError`, and unsupported backend/executor types produce descriptive errors.
