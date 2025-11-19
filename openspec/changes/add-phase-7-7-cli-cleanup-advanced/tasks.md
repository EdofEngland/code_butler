## 1. Implementation
- [ ] 1.1 Invoke advanced analyzer and cap number of suggestions shown.
  - [ ] 1.1.1 Add CLI command `ai-clean cleanup-advanced [PATH] --limit N` that calls the advanced analyzer orchestrator with the configured snippet limits.
  - [ ] 1.1.2 Print a summary header noting Codex-powered advisory suggestions and the imposed limit.
- [ ] 1.2 Create plans for each finding while marking them advisory-only.
  - [ ] 1.2.1 For each advanced finding returned, call `plan_advanced_cleanup` (via orchestrator) and persist the plan so metadata includes `advisory=True`.
  - [ ] 1.2.2 Ensure no git/spec/executor commands run; this command is read-only aside from writing plan JSON.
- [ ] 1.3 Present plan IDs and summaries without applying automatically.
  - [ ] 1.3.1 Print the plan id, title, and first step/rationale for each advisory plan plus where it was stored.
  - [ ] 1.3.2 Add tests verifying the limit option, plan creation, and that executors are never invoked.
