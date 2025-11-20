## Why
- `ai-clean apply` currently shells out through `scripts/apply_spec_wrapper.py`, but Codex runs expose `/prompts:openspec-apply` directly. Falling back to `openspec apply` fails because that binary does not provide an `apply` subcommand, so every apply attempt inside Codex errors out.
- Contributors need guidance on how to execute specs when they are not inside Codex (e.g., via `AI_CLEAN_APPLY_COMMAND` or the stub), otherwise local validation is confusing.

## What Changes
- Update the default executor configuration so the apply command directly targets `/prompts:openspec-apply {spec_path}` instead of the wrapper.
- Clarify developer documentation on how to override the apply command or enable the stub when running outside Codex.
- Keep the wrapper available for local overrides, but remove it from the default pipeline.

## Impact
- Codex runs will successfully invoke the real apply behavior without manual overrides.
- Local developers will have explicit instructions for setting `AI_CLEAN_APPLY_COMMAND` or `AI_CLEAN_USE_APPLY_STUB=1` when `/prompts:openspec-apply` is unavailable.
- No functional changes to spec serialization or plan generation.
