## 1. Deliverables

### 1.1 Analyzer orchestrator
- [x] Create `ai_clean/analyzers/orchestrator.py` exposing `analyze_repo(root: Path, config_path: Path | None = None) -> list[Finding]`.
- [x] Inside `analyze_repo`, call `load_config`, construct analyzer handles using the config (reusing `ai_clean/analyzers/__init__` exports), and invoke analyzers in fixed order (duplicate → structure → docstrings → organize).
- [x] Implement a `_merge_findings(existing: dict[str, Finding], new: Sequence[Finding])` helper that deduplicates by ID, merging sorted locations and metadata while preserving the first description/category.
- [x] Sort the final list by `(category, id)` and return it, guaranteeing deterministic outputs for identical repos/configs.
- [x] Wrap each analyzer invocation in `try/except`, logging warnings to stderr when an analyzer fails but continuing with the remaining ones; surface errors via metadata.
- [x] Write unit tests (e.g., `tests/analyzers/test_orchestrator.py::test_deduplication`) that feed synthetic findings into `_merge_findings` to assert ID-stability and deduplication logic.

### 1.2 CLI integration
- [x] Update `ai_clean/cli.py` to give the `/analyze` subcommand three options: `--root PATH` (default `.`), `--config FILE` (optional config override), and `--json` (emit machine-readable output).
- [x] Extract the handler for `/analyze` into a helper (e.g., `_run_analyze_command(args)`) that calls `analyze_repo(Path(args.root), args.config)` and captures the returned findings.
- [x] When `--json` is **not** provided, print a tabular summary listing each finding’s ID, category, and description followed by indented `path:start-end` lines for every location.
- [x] When `--json` **is** provided, serialize the findings list using the `Finding.to_json()` helper so downstream tools can consume it.
- [x] Update `README.md` with an example `ai-clean analyze --root src` invocation and document the new CLI flags/output format.
- [x] Document CLI assumptions/non-goals (e.g., no pagination, warnings go to stderr) so future changes understand the scope.

### 1.3 Tests
- [x] Add `tests/analyzers/test_orchestrator.py` that uses temporary files and the real analyzers (with low thresholds) to verify `analyze_repo()` collates results and deduplicates IDs.
- [x] Add `tests/test_cli_analyze.py` that runs `ai_clean.cli.main(["analyze", "--root", tmp_path])`, captures stdout, and asserts the expected textual summary (and JSON output when `--json` is set).
- [x] Extend tests to assert deterministic ordering between multiple runs and proper handling when an analyzer raises an exception (warnings + continued output).

## 2. Validation
- [x] Run `pytest tests/analyzers/test_orchestrator.py tests/test_cli_analyze.py` prior to delivering Phase 2.5.
