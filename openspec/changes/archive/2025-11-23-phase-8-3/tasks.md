## 1. Deliverables

- [x] Define constraints and assumptions
  - [x] Add a `ScopeConstraint`/`ForbiddenChange` enum (public API rename, signature change, global/cross-module rename, multi-module redesign, subsystem-wide restructuring) in a shared guard module (e.g., `ai_clean/planners/scope_guard.py`) with docstrings explaining V0 boundaries.
  - [x] Document allowed operations inline: local, behavior-preserving cleanups only; no interface or exported-name changes.
- [x] Implement detection
  - [x] Add detector functions to spot forbidden patterns by scanning plan metadata (exported names, plan_kind, target_file count) and step text heuristics for rename/signature/change words.
  - [x] Provide a summary function returning which forbidden categories were triggered for a plan or batch and why.
- [x] Enforce guardrails
  - [x] Integrate scope guard validation into the planner pipeline (e.g., `plan_from_finding` post-processing) to reject plans that trigger forbidden categories.
  - [x] When a mixed suggestion contains both allowed and forbidden parts, block or split so only the allowed local cleanup is emitted; never emit a plan that changes public API surfaces.
- [x] Observability and messaging
  - [x] Raise a typed error carrying the violated constraint(s) and a remediation note (“open a separate redesign phase”); ensure logging surfaces the blocked category and evidence.
  - [x] Add trace entries for split/block decisions so reviewers can see which constraint fired and what was returned (plans or rejection).
- [x] Tests
  - [x] Unit tests for detectors: allow local cleanup; reject public API rename; reject signature change; reject cross-module/global rename; reject multi-module redesign.
  - [x] Planner/orchestrator tests proving forbidden-only suggestions return a rejection (no executable plans) and mixed suggestions are split to keep only allowed work.
