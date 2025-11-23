# Proposal: Phase 4.3 – Backend Factory & Configuration

## Why
This change is part of 4 – ButlerSpec Backend & Spec Files (Our Own Tooling) and introduces Backend Factory & Configuration so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a backend factory: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a backend factory:

  - Read `ai-clean.toml` → `spec_backend.type`.
  - If `"butler"`:

    - Return a `ButlerSpecBackend` instance.
  - For unknown types:

    - Raise a friendly error: “Unsupported spec backend: X”.

- For v0, `butler` is the **only** supported backend.

## Configuration Contract & Non-goals
- The `[spec_backend]` table MUST define `type` and `specs_dir`. Missing, empty, or whitespace-only `type` values default to the same “Unsupported spec backend: <value>” error so configuration bugs are surfaced before backend construction.
- `specs_dir` continues to drive `SpecBackendHandle.specs_dir`; Phase 4.3 SHALL not invent defaults or mutate filesystem paths outside what `ai-clean.toml` provides.
- Only the literal string `butler` is recognized in v0; adding additional backend identifiers or default fallbacks is explicitly out of scope and requires a new proposal.

## Impact / Risks
- Unlocks later phases that depend on Backend Factory & Configuration.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
