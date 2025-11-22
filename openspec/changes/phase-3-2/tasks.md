## 1. Deliverables

- [ ] For `large_file`:

  - [ ] Intent: Split into 2–3 logical modules.
  - [ ] Steps:

    - [ ] Group code by responsibility.
    - [ ] Create new modules.
    - [ ] Move code and adjust imports.
  - [ ] Constraints:

    - [ ] Preserve public API, using re-exports if needed.

- [ ] For `long_function`:

  - [ ] Intent: Extract helpers to reduce length.
  - [ ] Steps:

    - [ ] Identify logical sub-blocks.
    - [ ] Extract into helpers.
    - [ ] Call helpers from original function.
  - [ ] Constraints:

    - [ ] Scope limited to the single function or very close neighbors.
