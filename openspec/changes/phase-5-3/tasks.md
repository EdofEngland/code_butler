## 1. Deliverables

- [ ] Implement a `ReviewExecutor` for `/changes-review`:

  - [ ] Input:

    - [ ] `CleanupPlan` (or `plan_id` to load it),
    - [ ] Associated `git diff` for the plan,
    - [ ] Latest `ExecutionResult` (apply + test info).

  - [ ] Use Codex in “review mode”:

    - [ ] Prompt: “Summarize these changes, flag risks, respect constraints.”

  - [ ] Output:

    - [ ] Review text or structured review:

      - [ ] Summary of changes,
      - [ ] Risk assessment,
      - [ ] Suggested manual checks.

- [ ] No code modifications here—review only.
