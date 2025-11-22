## 1. Deliverables

### 1.1 Doc analyzer configuration
- [x] Add `[analyzers.docstring]` to `ai-clean.toml` with keys `min_docstring_length`, `min_symbol_lines`, `weak_markers` (list of tokens like `"TODO"`/`"fixme"`), `important_symbols_only`, and `ignore_dirs`.
- [x] Define a `DocstringAnalyzerConfig` dataclass in `ai_clean/config.py` (fields above) and attach it to `AnalyzersConfig`.
- [x] Expand `load_config()` to parse the new section, normalize the string lists, ensure the numeric thresholds are positive, and provide defaults when the block is omitted.
- [x] Update `tests/test_config_loader.py` to assert doc analyzer values load correctly and to cover invalid threshold inputs.
- [x] Add negative tests for zero/negative thresholds, empty `weak_markers`, malformed ignore lists, and toggling `important_symbols_only` to confirm validation paths behave deterministically.

### 1.2 Model support
- [x] Update `ai_clean/models/core.py` so the `Finding.category` literal union includes `"weak_docstring"`, ensuring Pydantic accepts the new finding type.
- [x] Add/extend model tests (or analyzer unit tests) that instantiate a `Finding(category="weak_docstring", ...)` to confirm validation succeeds.

### 1.3 Doc analyzer implementation
- [x] Create `ai_clean/analyzers/docstrings.py` exposing `find_docstring_gaps(root: Path, settings: DocstringAnalyzerConfig) -> list[Finding]` and add it to `ai_clean/analyzers/__init__.py`.
- [x] Parse each `.py` file with `ast.parse`, skipping directories from `settings.ignore_dirs`, and inspect:
  - [x] Module docstring via `ast.get_docstring(tree)`; emit a `missing_docstring` finding when absent or blank.
  - [x] Public `ast.ClassDef`, `ast.FunctionDef`, and `ast.AsyncFunctionDef` nodes (names not starting with `_`).
- [x] For each symbol, compute its body length `end_lineno - lineno + 1` and skip ones shorter than `settings.min_symbol_lines` to honor the “important functions only” note.
- [x] Evaluate the docstring:
  - [x] `missing_docstring` when absent/blank.
  - [x] `weak_docstring` when the stripped docstring is shorter than `settings.min_docstring_length` or matches any marker from `settings.weak_markers`.
- [x] Emit a `Finding` per issue with:
  - [x] Deterministic ID `f"doc-{category}-{sha1((relative_path.as_posix()+':'+qualified_name).encode()).hexdigest()[:8]}"`.
  - [x] Description referencing the qualified symbol name and reason.
  - [x] `FindingLocation` covering the AST node span and metadata with `symbol_type`, `docstring_preview`, and `lines_of_code`.
- [x] Sort modules and symbols by `(relative_path, lineno, qualified_name)` before emitting to guarantee deterministic ordering.
- [x] Write analyzer tests that run twice on identical trees and assert byte-for-byte identical findings to enforce determinism.
- [x] Document assumptions (ignore private symbols, generated directories) inside the module docstring and validator tests so future contributors know the non-goals.

### 1.4 Tests and documentation
- [x] Add `tests/analyzers/test_docstring_analyzer.py` that creates modules with missing/weak docstrings, asserts both categories are emitted with correct metadata, and verifies the `min_symbol_lines` filter.
- [x] Document the doc analyzer behavior plus its config keys in README so `/annotate` users know how the findings are generated.

## 2. Validation
- [x] Run `pytest tests/analyzers/test_docstring_analyzer.py tests/test_config_loader.py` before marking Phase 2.3 complete.
