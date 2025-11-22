## 1. Deliverables

### 1.1 Analyzer configuration scaffolding
- [x] Extend `ai-clean.toml` with a `[analyzers.duplicate]` table documenting default values for `window_size`, `min_occurrences`, and `ignore_dirs` so operators can tune behavior without code edits.
- [x] In `ai_clean/config.py`, add a `DuplicateAnalyzerConfig` dataclass plus `AnalyzersConfig` bundle, update `AiCleanConfig` with an `analyzers: AnalyzersConfig` field, and expose the new classes via `__all__`.
- [x] Modify `load_config()` to parse `[analyzers.duplicate]`, validate `window_size > 0` and `min_occurrences > 1`, normalize `ignore_dirs` into a tuple of directory names, and fall back to defaults when omitted.
- [x] Update `tests/test_config_loader.py::ConfigLoaderTests.test_load_config_happy_path` to assert the duplicate settings are loaded, and add a new test that sets invalid thresholds to confirm `ValueError` is raised.
- [x] Include a regression test ensuring invalid `ignore_dirs` entries (e.g., empty strings) trigger deterministic validation errors.

### 1.2 Duplicate analyzer implementation
- [x] Create the `ai_clean/analyzers/__init__.py` module exporting `find_duplicate_blocks` so later phases can import it.
- [x] Implement `ai_clean/analyzers/duplicate.py` with `find_duplicate_blocks(root: Path, settings: DuplicateAnalyzerConfig) -> list[Finding]` plus helper functions `_iter_python_files` and `_build_windows`.
- [x] Use `Path.rglob("*.py")` to walk the tree, but skip directories listed in `settings.ignore_dirs` by checking each ancestor segment.
- [x] For each file, build sliding windows of size `settings.window_size`, dedent via `textwrap.dedent`, trim trailing whitespace, skip empty/comment-only windows, and yield `(normalized_text, rel_path, start_line, end_line)` tuples.
- [x] Aggregate windows in a `defaultdict[list]` keyed by normalized text, discard groups smaller than `settings.min_occurrences`, and convert survivors into `Finding` objects with:
  - [x] Deterministic IDs `f"dup-{sha1(normalized_text.encode()).hexdigest()[:8]}"`.
  - [x] Descriptions like `"Found {len(locations)} duplicate windows starting with 'foo = bar'"`.
  - [x] `FindingLocation` instances sorted by `(path, start_line)` plus metadata storing `window_size`, normalized preview, and relative paths.
- [x] Guarantee determinism by sorting discovered files, sorting window tuples prior to grouping, and returning a list sorted by `(category, id)`.
- [x] Add `tests/analyzers/test_duplicate_analyzer.py` fixtures that create in-memory duplicate snippets, run the analyzer twice, and assert identical results (IDs/descriptions/ordering).

### 1.3 Tests and documentation
- [x] In `tests/analyzers/test_duplicate_analyzer.py`, create fixture files with repeated blocks, assert a single `duplicate_block` finding with expected locations, verify `ignore_dirs` filtering, and rerun the analyzer twice to confirm identical outputs.
- [x] Update `README.md` under the `/analyze` command description to explain how duplicate detection works, include sample output, and document the `[analyzers.duplicate]` config keys plus default values.

## 2. Validation
- [x] Run `pytest tests/analyzers/test_duplicate_analyzer.py tests/test_config_loader.py` and capture the passing output when sharing the Phase 2.1 work.
