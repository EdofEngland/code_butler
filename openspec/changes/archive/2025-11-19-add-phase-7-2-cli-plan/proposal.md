## Why
Allow users to generate and store a CleanupPlan for a specific finding via CLI.

## What Changes
- Implement ai-clean plan FINDING_ID [--path PATH] to run analyzers, locate the finding, and build a plan.
- Save the plan and print plan id, title, intent, steps, constraints, and tests_to_run.
- Provide path override while keeping flow manual (no auto-apply).

## Impact
- Users can create plans on demand for specific findings.
- Stored plans include key details for review.
