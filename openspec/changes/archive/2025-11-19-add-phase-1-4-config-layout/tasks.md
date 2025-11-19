## 1. Implementation
- [x] 1.1 Define the expected `ai-clean.toml` structure with sections: `[spec_backend] type`, `[executor] type`, `[review] type`, `[git] base_branch/refactor_branch`, and `[tests] default_command`.
- [x] 1.2 Document and create (if missing) local metadata directories `.ai-clean/plans/` and `.ai-clean/specs/`.
- [x] 1.3 Add a config loader module (e.g., `ai_clean/config.py`) that reads `ai-clean.toml`, validates required keys, and returns typed config objects/dicts for factories.
- [x] 1.4 Ensure validation errors are clear when unsupported backend/executor/review types are provided.
