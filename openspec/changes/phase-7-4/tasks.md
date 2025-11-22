## 1. Deliverables

- [ ] `ai-clean clean [PATH]`:

  - [ ] Run analyzers.

  - [ ] Filter findings for:

    - [ ] `duplicate_block`,
    - [ ] `large_file`,
    - [ ] `long_function`.

  - [ ] Present a list; user chooses a finding (or a few).

  - [ ] For each chosen finding:

    - [ ] Generate `CleanupPlan`.
    - [ ] Ask user whether to:

      - [ ] Only save plan, or
      - [ ] Save and immediately `/apply`.
