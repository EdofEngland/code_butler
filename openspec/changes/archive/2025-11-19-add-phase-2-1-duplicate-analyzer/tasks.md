## 1. Implementation
- [ ] 1.1 Add analyzer module (e.g., `ai_clean/analyzers/duplicate.py`) that walks a target path recursively for `*.py` files while skipping env/metadata folders (e.g., `.venv*`, `.ai-clean`, `env`, `build`, `dist`).
- [ ] 1.2 Read files and build normalized fixed-size windows of code lines (strip whitespace/comments as needed) using a configurable window size while preserving mapping back to original line numbers.
- [ ] 1.3 Group identical windows across files and, when occurrences meet/exceed a configurable minimum, emit `duplicate_block` findings including description (counts/context) and per-occurrence locations mapped to original file line ranges.
- [ ] 1.4 Support configuration inputs for window size and minimum occurrences (defaults if unspecified) to bound analysis and memory use.
