## 1. Deliverables

### 1.1 Organize analyzer configuration
- [x] Extend `ai-clean.toml` with `[analyzers.organize]` documenting defaults for `min_group_size`, `max_group_size`, `max_groups`, and `ignore_dirs`, including inline comments about suggested ranges.
- [x] Add `OrganizeAnalyzerConfig` to `ai_clean/config.py`, wire it into `AnalyzersConfig`/`AiCleanConfig`, and expose via `__all__`.
- [x] Update `load_config()` to parse this block, enforce `2 <= min_group_size <= max_group_size <= 5` and `max_groups >= 1`, and merge `ignore_dirs` with prior analyzer defaults.
- [x] In `tests/test_config_loader.py`, add assertions for the organize config and negative tests covering zero/negative sizes, `max_groups` less than `min_group_size`, and malformed `ignore_dirs`.

### 1.2 Organize analyzer implementation
- [x] Implement `ai_clean/analyzers/organize.py` with `propose_organize_groups(...)` and export it from `ai_clean/analyzers/__init__.py`.
- [x] Build file profiles containing filename stem tokens, top-level import module names, and module docstring keywords (lowercase, stopwords removed); skip files under `ignore_dirs`.
- [x] Use a `Counter` or map to aggregate topic → set(files); keep only topics whose member counts fall within `[min_group_size, max_group_size]`.
- [x] Sort topics by `(-len(members), topic)` and select up to `max_groups`. For each topic emit a `Finding` with:
  - [x] ID slugified from the topic plus index `organize-{topic}-{idx:02d}`.
  - [x] Description `Consider regrouping N files under "<topic>/"`.
  - [x] `FindingLocation`s with `start_line=end_line=1` for each file and metadata enumerating the member files.
- [x] Ensure each file appears in at most one finding by marking files as claimed.
- [x] Document assumptions in the module docstring, e.g., skip vendor directories, skip ambiguous files.
- [x] Provide deterministic output by iterating files/locations/topics in sorted order and add rerun tests verifying identical results for the same fixture tree.

### 1.3 Tests and docs
- [x] Add `tests/analyzers/test_organize_analyzer.py` that creates fake modules with shared imports/docstrings, asserts the groupings stay within config bounds, and verifies that files are assigned deterministically.
- [x] Document the organize analyzer behavior plus config knobs in README so `/organize` eventually has discoverable behavior.

## 2. Validation
- [x] Run `pytest tests/analyzers/test_organize_analyzer.py tests/test_config_loader.py` before closing Phase 2.4.
