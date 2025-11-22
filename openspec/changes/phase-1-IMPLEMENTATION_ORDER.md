# Phase 1 Implementation Order

Phase 1 introduces the minimum skeleton needed for ai-clean to operate on ButlerSpec plans. Each change builds on the previous one; do not start a later change until its prerequisites are merged.

## Sequence

1. **phase-1-1 – Repo & Packaging Setup**
   - Baseline repo, CLI entrypoint, README, `.gitignore`.
   - Establishes the `ai_clean` package other phases import.

2. **phase-1-2 – Core Data Model Definitions**
   - Depends on phase-1-1 (package + dependencies must exist).
   - Delivers `CleanupPlan`, `ButlerSpec`, and `ExecutionResult` models that other phases type against.

3. **phase-1-3 – Plugin Interfaces**
   - Depends on phase-1-2 models.
   - Introduces `SpecBackend`, `CodeExecutor`, and `ReviewExecutor` Protocols plus example implementations.
   - Enables later milestones to plug in Codex-backed components without editing core data classes.

4. **phase-1-4 – Configuration & Local Metadata Layout**
   - Depends on Phase 1.1 bootstrapping the CLI and Phase 1.3 establishing hook points.
   - Adds `ai-clean.toml`, `.ai-clean/` directories, typed config loaders, and factories that wire commands to real implementations.

## Shared Assets

- `.ai-clean/plans`, `.ai-clean/specs`, `.ai-clean/results` directories are created in Phase 1.1 and exercised in Phases 1.2–1.4.
- The serialization helpers from Phase 1.2 feed directly into the metadata layout defined in Phase 1.4.
- Interfaces from Phase 1.3 explicitly accept the dataclasses from Phase 1.2, keeping the boundary narrow and testable.

This structure mirrors the dependency documentation pattern from `thirdparty_learning/openspec/openspec/changes/IMPLEMENTATION_ORDER.md` and should be updated if Phase 1 scopes shift.
