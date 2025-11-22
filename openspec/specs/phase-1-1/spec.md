# phase-1-1 Specification

## Purpose
TBD - created by archiving change phase-1-1. Update Purpose after archive.
## Requirements
### Requirement: Packaging skeleton exists
The repository MUST expose a runnable `ai_clean` package with metadata synced between `pyproject.toml` and `ai_clean/__init__.py`.

#### Scenario: Package metadata compiles
- **WHEN** `pip install -e .` is executed
- **THEN** the `ai-clean` console script resolves to `ai_clean.cli:main`
- **AND** `python -c "import ai_clean; print(ai_clean.__version__)"` reports the same semantic version defined in `pyproject.toml`.

### Requirement: CLI help documents ButlerSpec commands
New contributors MUST see every ButlerSpec command stub via `python -m ai_clean.cli --help`.

#### Scenario: CLI help lists command roster
- **GIVEN** the repo has been bootstrapped per Phase 1.1
- **WHEN** `python -m ai_clean.cli --help` runs
- **THEN** the help output lists `/analyze`, `/clean`, `/annotate`, `/organize`, `/cleanup-advanced`, `/plan`, `/apply`, `/changes-review`
- **AND** each entry displays placeholder text `"TODO: <command>"` or similar acknowledgements.

### Requirement: Contributor documentation links to architecture
The README MUST describe ai-clean’s purpose, outline each command, and reference the “Phase 1 System Sketch” for architectural context.

#### Scenario: README orients new contributors
- **WHEN** a maintainer opens `README.md`
- **THEN** the file contains a ButlerSpec-governed purpose paragraph
- **AND** a bullet list that summarizes the role of every command stub
- **AND** a link pointing to `docs/butlerspec_plan.md#phase-1-system-sketch`.

### Requirement: Git hygiene excludes generated assets
Python build artifacts and ButlerSpec metadata directories MUST be ignored by default.

#### Scenario: .gitignore protects metadata
- **WHEN** `.gitignore` is reviewed
- **THEN** it contains entries for `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.pytest_cache/`, `.venv/`, `.ai-clean/`, `dist/`, and `build/`.
