## 1. Deliverables

### 1.1 Repository + packaging skeleton
- [x] Update `pyproject.toml` with a `[project]` table that sets `name = "ai-clean"`, semantic `version`, `description`, `requires-python = ">=3.11"`, and runtime dependencies (only stdlib for now).
- [x] Define `[project.scripts] ai-clean = "ai_clean.cli:main"` so `pip install -e .` exposes the CLI entrypoint.
- [x] Create `ai_clean/__init__.py` exporting `__all__ = ["__version__"]` and a `__version__` constant synced with `pyproject.toml`.

### 1.2 CLI entrypoint stub
- [x] Add `ai_clean/cli.py` that uses `argparse` (stdlib) to register subcommands `/analyze`, `/clean`, `/annotate`, `/organize`, `/cleanup-advanced`, `/plan`, `/apply`, `/changes-review`; each handler should currently print `"TODO: <command>"`.
- [x] Ensure `main()` parses args and returns exit code 0 while `python -m ai_clean.cli --help` lists every command name under the “Commands” section.

### 1.3 Project hygiene
- [x] Create/expand `.gitignore` to cover Python artifacts (`__pycache__/`, `*.pyc`, `.mypy_cache/`, `.pytest_cache/`, `.venv/`, `.ai-clean/`, `dist/`, `build/`).
- [x] Write `README.md` with:
  - [x] One-paragraph purpose statement describing ai-clean as a ButlerSpec-governed cleanup assistant.
  - [x] A bullet list briefly explaining each CLI command so new contributors know the intent of `/analyze`, `/clean`, `/annotate`, `/organize`, `/cleanup-advanced`, `/plan`, `/apply`, `/changes-review`.
  - [x] A pointer to the "Phase 1 System Sketch" section in `docs/butlerspec_plan.md` so readers understand how CLI commands feed plans/specs/executions.

### 1.4 Verification
- [x] Run `python -m ai_clean.cli --help` and confirm the help output contains every command string listed above plus a short description.
- [x] Capture the help text snippet (or equivalent screenshot) in PR/notes to prove the skeleton CLI works end-to-end for future reference.
