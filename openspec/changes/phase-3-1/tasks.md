## 1. Deliverables

- [ ] For each `duplicate_block` finding, create a `CleanupPlan`:

  - [ ] Intent:

    - [ ] Extract reusable helper and replace duplicates.

  - [ ] Steps:

    - [ ] Decide helper location.
    - [ ] Create helper function/class.
    - [ ] Replace duplicate blocks with calls.

  - [ ] Constraints:

    - [ ] No external behavior changes.
    - [ ] No public API changes.

  - [ ] Tests:

    - [ ] Default test command from config.

- [ ] Keep each plan **small**:

  - [ ] If a finding has many occurrences, split into multiple plans.
