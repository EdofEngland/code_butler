## Why
Combine analyzer outputs into a single workflow and surface findings via /analyze.

## What Changes
- Implement analyze_repo(path) to run duplicate, structure, docstring, and organize analyzers.
- Assign stable IDs to each finding and return the combined list.
- Wire orchestrator into the /analyze CLI to present id, category, description, and location summaries.

## Impact
- Users see a consolidated findings list from multiple analyzers.
- Stable IDs enable subsequent planning steps.
