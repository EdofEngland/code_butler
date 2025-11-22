## 1. Deliverables

- [ ] Implement `ButlerSpecBackend` (your OpenSpec replacement):

  - [ ] Accepts a `CleanupPlan`.

  - [ ] Enforces governance:

    - [ ] **One target file per plan** (one-plan-per-file).
    - [ ] Any violation → clear error.

  - [ ] Produces a `ButlerSpec` with fields like:

    - [ ] `id`: spec id.
    - [ ] `plan_id`.
    - [ ] `target_file`.
    - [ ] `intent`.
    - [ ] `actions`: structured instructions for the executor/model.
    - [ ] `model`: e.g., `"codex"` (or `"local_jamba"` later).
    - [ ] `batch_group`: optional grouping name for batches.
    - [ ] `metadata` (constraints, tests).

- [ ] Keep the payload:

  - [ ] Small, deterministic, and human-readable.
