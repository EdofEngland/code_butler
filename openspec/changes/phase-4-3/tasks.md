## 1. Deliverables

- [ ] Implement a backend factory:

  - [ ] Read `ai-clean.toml` → `spec_backend.type`.
  - [ ] If `"butler"`:

    - [ ] Return a `ButlerSpecBackend` instance.
  - [ ] For unknown types:

    - [ ] Raise a friendly error: “Unsupported spec backend: X”.

- [ ] For v0, `butler` is the **only** supported backend.
