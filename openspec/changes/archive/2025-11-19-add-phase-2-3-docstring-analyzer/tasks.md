## 1. Implementation
- [x] 1.1 Add docstring analyzer module (e.g., `ai_clean/analyzers/docstrings.py`) that recursively scans `*.py` files while skipping env/metadata folders (e.g., `.venv*`, `.ai-clean`, `env`, `build`, `dist`).
- [x] 1.2 Detect missing or empty module docstrings and emit `missing_docstring` findings with module-level locations.
- [x] 1.3 Detect missing or trivial docstrings on public classes/functions (no leading underscore), optionally gating by size/line-count for v0, and classify as `missing_docstring` or `weak_docstring`.
- [x] 1.4 Emit findings with symbol names and precise start/end lines for each public symbol flagged.
