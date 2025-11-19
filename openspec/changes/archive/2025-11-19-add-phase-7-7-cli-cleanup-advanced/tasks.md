## 1. Implementation
- [x] 1.1 Invoke advanced analyzer and cap number of suggestions shown.
  - [x] 1.1.1 Add CLI command `ai-clean cleanup-advanced [PATH] --limit N` that calls the advanced analyzer orchestrator with the configured snippet limits.
  - [x] 1.1.2 Print a summary header noting Codex-powered advisory suggestions and the imposed limit.
- [x] 1.2 Create plans for each finding while marking them advisory-only.
  - [x] 1.2.1 For each advanced finding returned, call `plan_advanced_cleanup` (via orchestrator) and persist the plan so metadata includes `advisory=True`.
  - [x] 1.2.2 Ensure no git/spec/executor commands run; this command is read-only aside from writing plan JSON.
- [x] 1.3 Present plan IDs and summaries without applying automatically.
  - [x] 1.3.1 Print the plan id, title, and first step/rationale for each advisory plan plus where it was stored.
  - [x] 1.3.2 Add tests verifying the limit option, plan creation, and that executors are never invoked.
