## 1. Implementation
- [x] 1.1 Add an orchestrator module (e.g., `ai_clean/analyzers/orchestrator.py`) with `analyze_repo(path)` that calls duplicate, structure, docstring, and organize analyzers.
- [x] 1.2 Assign stable IDs to each finding and merge results into a single list, preserving category, description, and locations.
- [x] 1.3 Ensure each finding can render a concise location summary (path + line ranges) for display.
- [x] 1.4 Wire `/analyze` CLI command to invoke the orchestrator and print ID, category, description, and location summaries.
