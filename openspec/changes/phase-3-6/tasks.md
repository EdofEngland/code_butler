## 1. Deliverables

- [ ] Implement `plan_from_finding(finding: Finding) -> CleanupPlan`:

  - [ ] Dispatch by `category`.
  - [ ] Generate a **single** plan for each invocation.

- [ ] Provide helpers to:

  - [ ] Generate unique plan IDs.
  - [ ] Serialize plans to `.ai-clean/plans/{plan_id}.json`.
