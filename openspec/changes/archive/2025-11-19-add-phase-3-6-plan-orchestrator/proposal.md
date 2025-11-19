## Why
Provide a single entrypoint to convert findings to plans, manage IDs, and persist plans.

## What Changes
- Implement plan_from_finding to branch by category and return a CleanupPlan.
- Provide helpers for unique plan ID generation and serialization to .ai-clean/plans/.
- Ensure orchestrator returns exactly one plan per call with consistent schema.

## Impact
- Planning becomes deterministic and storage-friendly.
- CLI commands can rely on consistent plan IDs and persistence.
