## 1. Deliverables

- [ ] `ai-clean plan FINDING_ID [--path PATH]`:

  - [ ] Run analyzers (or load cached findings).
  - [ ] Locate `Finding` by ID.
  - [ ] Create `CleanupPlan` via planner.
  - [ ] Save plan to `.ai-clean/plans/`.
  - [ ] Print:

    - [ ] Plan ID, title, intent, steps, constraints, tests_to_run.
