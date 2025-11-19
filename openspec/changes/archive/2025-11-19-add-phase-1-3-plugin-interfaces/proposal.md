## Why
Allow interchangeable backends and executors via abstract interfaces that rely only on core models.

## What Changes
- Define SpecBackend with plan_to_spec(plan) -> SpecChange and write_spec(spec, directory) -> path.
- Define CodeExecutor with apply_spec(spec_path) -> ExecutionResult.
- Define ReviewExecutor with review_change(plan_id, diff, execution_result) -> review output while avoiding tool-specific names.

## Impact
- Plugins can be built against stable interfaces without coupling to Codex or OpenSpec naming.
- Core models remain the only dependency for plugin authors.
