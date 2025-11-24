## 1. Deliverables

- [x] Define deterministic limits and configuration
  - [x] Add a `PlanLimitsConfig` (e.g., `max_files_per_plan`, `max_changed_lines_per_plan`) to `ai_clean/config.py`, thread through `AiCleanConfig`, and parse from `ai-clean.toml` with defaults (v0: files=1, lines cap set explicitly).
  - [x] Update `ai-clean.toml` template/comments to explain how line deltas are measured (absolute additions + deletions) and which files, if any, are ignored.
- [x] Implement limit calculation helpers
  - [x] Add a shared helper (e.g., `ai_clean/planners/limits.py`) to count targeted files from plan metadata (`target_file`/`target_path`) and deduplicate paths.
  - [x] Add a helper to compute changed-line totals from plan metadata (use line_span if present, or other per-plan metadata; fall back to 0 when unavailable) and return a structured summary `{files, lines}`.
- [x] Enforce in planning/analyzer flows
  - [x] Invoke the limit validator inside `ai_clean/planners/orchestrator.plan_from_finding` (or immediately after planner outputs) and raise a typed error when limits are exceeded.
  - [x] Add a splitter utility that takes oversized plan outputs and emits multiple single-file plans within limits; wire it into planners that can produce multi-file outputs (structure/organize/advanced) before plans are persisted.
- [x] Validation and messaging
  - [x] Create a `PlanLimitError` (or similar) that surfaces current counts, thresholds, and remediation (“split into separate plans”); propagate messages through planner/analyzer logs.
  - [x] Add trace/log entries when a plan list is split, including before/after file counts and line totals, so reviewers can see why division occurred.
- [x] Tests
  - [x] Unit tests for file/line helpers covering advanced, structure, and docstring plan metadata shapes.
  - [x] Planner/orchestrator tests proving: single-file within limits passes; >1 file rejects; over-cap lines reject; split utility produces per-file plans that each validate.
