## 1. Implementation
- [x] 1.1 Add an advanced analyzer module (e.g., `ai_clean/analyzers/advanced.py`) that accepts a path and a summary of current findings.
- [x] 1.2 Select a bounded subset of files/snippets (config limits) and build a constrained prompt for Codex emphasizing small, local cleanups.
- [x] 1.3 Parse Codex structured responses into `advanced_cleanup` findings with descriptions, metadata, and precise locations.
- [x] 1.4 Enforce configuration limits on number of suggestions and files/snippets per run; treat results as advisory-only (no auto-apply).
