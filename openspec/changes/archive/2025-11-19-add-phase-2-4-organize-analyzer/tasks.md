## 1. Implementation
- [x] 1.1 Add organize-seed analyzer module (e.g., `ai_clean/analyzers/organize.py`) that scans `*.py` (and optionally related files) while skipping env/metadata/vendor folders (e.g., `.venv*`, `.ai-clean`, `env`, `build`, `dist`, `site-packages`).
- [x] 1.2 For each file, extract topic signals from filename tokens, top-level imports, and module docstring (if present) to infer rough topics.
- [x] 1.3 Group files sharing similar topics in the same folder into small candidate sets and emit `organize_candidate` findings with suggested destination folder and list of file paths.
- [x] 1.4 Enforce conservative limits per finding (e.g., 2–5 files) and avoid overlapping or excessive moves in a single finding.
