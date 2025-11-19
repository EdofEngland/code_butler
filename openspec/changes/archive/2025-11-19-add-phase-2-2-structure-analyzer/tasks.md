## 1. Implementation
- [x] 1.1 Add analyzer module (e.g., `ai_clean/analyzers/structure.py`) that walks a target path for `*.py` files, skipping env/metadata/vendor folders (e.g., `.venv*`, `.ai-clean`, `env`, `build`, `dist`, `site-packages`).
- [x] 1.2 For each file, count lines and compare to a configurable `large_file` threshold; when exceeded emit a `large_file` finding with a location spanning the whole file (start line 1 to last line).
- [x] 1.3 Parse each Python file (AST) to locate function definitions and their start/end lines; compare spans to a configurable `long_function` threshold and emit `long_function` findings for every function breaching it (allow multiple per file).
- [x] 1.4 Expose configuration (defaults) for skip directories, `large_file` threshold, and `long_function` threshold; allow overlapping findings and do not suppress multiple breaches within the same file.
