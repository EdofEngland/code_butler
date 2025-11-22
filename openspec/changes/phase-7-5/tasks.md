## 1. Deliverables

- [ ] `ai-clean annotate [PATH] [--mode missing|all]`:

  - [ ] Run doc analyzer.

  - [ ] Filter for `missing_docstring` (and maybe `weak_docstring` if `--mode all`).

  - [ ] Show targets; user chooses modules or “all”.

  - [ ] For each selection:

    - [ ] Generate a docstring `CleanupPlan`.
    - [ ] Offer to apply via the standard `/apply` flow.
