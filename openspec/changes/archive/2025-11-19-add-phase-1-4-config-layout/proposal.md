## Why
Standardize configuration through ai-clean.toml and define local metadata storage for plans and specs.

## What Changes
- Introduce ai-clean.toml sections for spec_backend, executor, review, git base/refactor branches, and default tests command.
- Define local metadata directories .ai-clean/plans/ and .ai-clean/specs/.
- Add a config loader that reads, validates, and exposes objects for factories.

## Impact
- Downstream components can locate settings and storage paths deterministically.
- Misconfiguration surfaces early via validation.
