## Why
Convert CleanupPlans into SpecChange payloads using the OpenSpec backend type.

## What Changes
- Implement OpenSpecBackend that accepts a CleanupPlan and produces a SpecChange with backend_type="openspec".
- Populate payload with plan id, title, intent, steps, constraints, tests to run, and finding metadata.
- Keep payload structure consistent across plan types and human-readable.

## Impact
- Plans can be transformed into specs ready for downstream execution.
- SpecChange payloads stay uniform and editable.
