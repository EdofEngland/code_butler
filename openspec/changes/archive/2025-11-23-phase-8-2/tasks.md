## 1. Deliverables

- [x] Define concern taxonomy and rules
  - [x] Add a `Concern` enum (helper_extraction, file_split, file_group_move, docstring_batch, advanced_cleanup) in a shared module (e.g., `ai_clean/planners/concerns.py`) with short docstrings describing boundaries.
  - [x] Document invalid mixes in code comments (docstring + helper extraction, move + rename + cleanup, chained refactors) and keep them close to the enum for easy reference.
- [x] Implement concern classification
  - [x] Add `classify_plan_concern(plan: CleanupPlan) -> Concern` using metadata keys like `plan_kind`, `target_file`, line spans, and step text heuristics.
  - [x] Add `classify_plan_group(plans: list[CleanupPlan])` to detect mixed concerns across a batch; return evidence of which concerns were found.
  - [x] Export classifier to planner and advanced analyzer flows so every emitted plan is tagged with a single concern.
- [x] Enforce single-concern validation
  - [x] Add a validator that raises a typed error when a plan (or list) contains >1 concern, including the detected concern names in the message.
  - [x] Add a splitter that, when possible, separates mixed outputs into single-concern plans (e.g., split docstring+helper suggestions into two plans) and block when the split cannot preserve single-concern purity.
- [x] Observability and messaging
  - [x] Emit validation errors citing the detected concerns and the required remediation (“split into separate plans for X and Y”).
  - [x] Log/trace split decisions with before/after concern tags so reviewers see why plans were divided.
- [x] Tests
  - [x] Unit tests for classifier covering each concern type and mixed-case detection (docstring+helper, move+cleanup).
  - [x] Validator tests that mixed concerns are rejected with actionable errors; splitter tests showing multiple single-concern plans are produced when possible.
  - [x] Integration test around planner/analyzer flow ensuring every plan is tagged with exactly one concern and mixed batches are blocked/split.
