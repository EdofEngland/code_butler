## 1. Deliverables

- [x] Wire `ButlerSpecBackend` into `ai_clean.factories.get_spec_backend` so CLI callers receive the real backend.
  - [x] Delete the `_ButlerSpecBackend` placeholder class (and its reference in `__all__`) from `ai_clean/factories.py` and add `from ai_clean.spec_backends import ButlerSpecBackend` near the top of the file.
  - [x] Add a module-level mapping such as `BACKEND_BUILDERS: dict[str, Callable[[SpecBackendConfig], SpecBackend]] = {"butler": ButlerSpecBackend}` to centralize backend constructors; include type annotations for clarity.
  - [x] Update `get_spec_backend` to read `backend_type = (config.spec_backend.type or "").strip().lower()` and look up the callable in `BACKEND_BUILDERS`.
  - [x] When the lookup fails (unknown or blank type), raise `ValueError(f"Unsupported spec backend: {backend_type or '<empty>'}")` before touching the filesystem so callers see the friendly error.
  - [x] When the lookup succeeds, instantiate the backend via the callable, wrap it inside `SpecBackendHandle`, and keep `specs_dir` wired to `config.spec_backend.specs_dir`.

- [x] Update tests to cover the real backend wiring.
  - [x] Extend `tests/test_config_loader.py::ConfigLoaderTests.test_load_config_happy_path` to construct a `CleanupPlan`, call `spec_handle.backend.plan_to_spec(plan)`, and assert a `ButlerSpec` is returned (no `NotImplementedError`).
  - [x] Add `tests/test_factories.py` with `test_get_spec_backend_returns_butler_backend` asserting the handle contains a `ButlerSpecBackend` instance and inherits the path from the config.
  - [x] Add `test_get_spec_backend_rejects_unknown_type` that builds an `AiCleanConfig` containing `SpecBackendConfig(type="other", ...)` and asserts the ValueError message is “Unsupported spec backend: other”.
  - [x] Add `test_get_spec_backend_rejects_blank_type` that passes `""` (and/or `None`) for the type and asserts the same friendly error is raised before attempting instantiation.

- [x] Document backend factory behavior so contributors know how to configure ai-clean.
  - [x] Update `docs/butlerspec_plan.md#phase-4-3` to state explicitly that `get_spec_backend` instantiates `ButlerSpecBackend` when `[spec_backend]` declares `type = "butler"`.
  - [x] Mention that `butler` is the only supported backend identifier in v0 and that new identifiers require an approved proposal before being added to `BACKEND_BUILDERS`.
  - [x] Include a fenced TOML snippet showing the `[spec_backend]` table with `type = "butler"` and `specs_dir = ".ai-clean/specs"` so operators can copy/paste the correct config.
