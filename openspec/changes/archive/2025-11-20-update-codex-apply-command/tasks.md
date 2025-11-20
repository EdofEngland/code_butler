## 1. Update default apply command
- [x] 1.1 Edit `ai-clean.toml` so `[executor].apply_command` equals `["/prompts:openspec-apply", "{spec_path}"]`, replacing the wrapper reference.
- [x] 1.2 Adjust `tests/test_executor_factories.py` (and any other config-parsing tests that hardcode apply commands) to assert the new command shape.
- [x] 1.3 Confirm `scripts/apply_spec_wrapper.py` remains in the repo and document in comments that it is intended for local overrides only (no behavioral change, but add a short note near the `DEFAULT_COMMANDS` tuple).

## 2. Document non-Codex workflows
- [x] 2.1 Update `README.md` to include a new subsection (e.g., “Running apply locally”) describing how to set `AI_CLEAN_APPLY_COMMAND` or `AI_CLEAN_USE_APPLY_STUB=1` when `/prompts:openspec-apply` is missing.
- [x] 2.2 In that section, provide concrete command examples that use the wrapper (e.g., `AI_CLEAN_APPLY_COMMAND="scripts/apply_spec_wrapper.py {spec_path}"`) so contributors know how to reuse it.

## 3. Validate flow
- [x] 3.1 Locally run `AI_CLEAN_USE_APPLY_STUB=1 ai-clean apply <plan>` to ensure the new config path still executes end-to-end (the stub should print the expected message).
- [x] 3.2 Document in the PR description (or README section) that Codex validation requires running `ai-clean apply` without the stub so `/prompts:openspec-apply` is exercised; note any expected output or checks reviewers should perform inside Codex.
