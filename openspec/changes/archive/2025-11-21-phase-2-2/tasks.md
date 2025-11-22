## 1. Deliverables

### 1.1 Structure analyzer configuration
- [x] Add `[analyzers.structure]` to `ai-clean.toml` specifying `max_file_lines`, `max_function_lines`, `ignore_dirs`, and document their default values in comments.
- [x] In `ai_clean/config.py`, create `StructureAnalyzerConfig` and update `AnalyzersConfig`/`AiCleanConfig` to include a `structure` field.
- [x] Modify `load_config()` to parse the new block, ensure thresholds are positive, merge `ignore_dirs` with the duplicate analyzer defaults, and surface the config on `AiCleanConfig`.
- [x] Update `tests/test_config_loader.py` to verify the structure settings load correctly and add failure cases for zero/negative thresholds, malformed ignore lists, and overrides.

### 1.2 Structure analyzer implementation
- [x] Implement `ai_clean/analyzers/structure.py` exposing `find_structure_issues(root: Path, settings: StructureAnalyzerConfig) -> list[Finding]`.
- [x] Use `Path.rglob("*.py")` for discovery while skipping directories listed in `settings.ignore_dirs`.
- [x] Count lines for each file; when `line_count > max_file_lines`, create a `Finding` with:
  - [x] ID `f"large-file-{sha1(relative_path.as_posix().encode()).hexdigest()[:8]}"`.
  - [x] Description `"File foo.py has {line_count} lines (> {threshold})"`.
  - [x] Single `FindingLocation(path, 1, line_count)` and metadata storing the measured count.
- [x] Parse files once with `ast.parse`, walk `FunctionDef`/`AsyncFunctionDef`, compute `length = (end_lineno or lineno) - lineno + 1`, and when `length > max_function_lines` emit `long_function` findings with deterministic IDs `long-func-{sha1(...)}`
- [x] Before returning, sort file findings and function findings by `(relative_path, lineno, qualified_name)` to guarantee deterministic ordering.
- [x] Add helper functions `_iter_large_files` and `_iter_long_functions` to keep logic testable, and ensure unit tests cover both functions.

### 1.3 Tests and documentation
- [x] Create `tests/analyzers/test_structure_analyzer.py` with fixtures that generate temporary files exceeding file/function thresholds, assert both finding types (with expected IDs/metadata), and verify overriding thresholds in `ai-clean.toml` takes effect.
- [x] Document the structure analyzer in `README.md` (within `/analyze` section) including the threshold config keys, example output, and guardrails about multiple findings per file.

## 2. Validation
- [x] Run `pytest tests/analyzers/test_structure_analyzer.py tests/test_config_loader.py` to demonstrate the analyzer + config wiring are stable.
