## Why
`ai-clean apply` currently crashes before it can create a spec because the backend factory runs `isinstance(backend, SpecBackend)` even though `SpecBackend` is a `typing.Protocol` without `@runtime_checkable`. Python forbids runtime `isinstance` on such protocols, so the tool errors out immediately.

## What Changes
- Mark the plugin protocols (`SpecBackend`, `CodeExecutor`, `ReviewExecutor`) as `@runtime_checkable` so the factory and future guards can safely verify implementations.
- Keep the backend factory logic intact so unsupported or malformed backends continue to raise clear errors.

## Impact
- `ai-clean apply` (and any other flow that builds backends/executors) will proceed instead of failing on the protocol check.
- Protocol conformance checks will work consistently across spec, executor, and review plug-in points without changing their type signatures.
