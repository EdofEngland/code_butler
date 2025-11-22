## 1. Deliverables

- [ ] Implement `ensure_on_refactor_branch(base_branch, refactor_branch)`:

  - [ ] If already on `refactor_branch`: do nothing.
  - [ ] Else:

    - [ ] Fetch/update `base_branch`.
    - [ ] Create/fast-forward `refactor_branch` from `base_branch`.
    - [ ] Checkout `refactor_branch`.

- [ ] No auto-commits or merges into `main`. Conflicts are surfaced to user.
