## 1. Implementation
- [x] 1.1 Add a core models module file and declare `FindingLocation` with path, start_line, end_line.
- [x] 1.2 Define `Finding` with id, category (supporting duplicate_block, large_file, missing_docstring, organize_candidate, advanced_cleanup), description, list of FindingLocation objects, and metadata dict.
- [x] 1.3 Define `CleanupPlan` with id, finding_id, title, intent, steps (list of strings), constraints (list of strings), tests_to_run (list of strings), and metadata dict.
- [x] 1.4 Define `SpecChange` with id, backend_type (string), and payload as a dict-like structure.
- [x] 1.5 Define `ExecutionResult` with spec_id, success (bool), tests_passed (bool or None), stdout, stderr, optional git_diff, and metadata dict.
- [x] 1.6 Ensure all models support creation and JSON-safe serialization/deserialization using only the standard library (e.g., dataclasses/asdict/json) with no references to Codex or OpenSpec.
