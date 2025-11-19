## Why
Expose analyzer orchestrator via CLI to list findings with summaries.

## What Changes
- Implement ai-clean analyze [PATH] to run analyzer orchestrator.
- Display findings with IDs, categories, descriptions, and location summaries.
- Keep command read-only without creating plans or specs.

## Impact
- Users can inspect repository issues before planning.
- Findings become discoverable via CLI.
