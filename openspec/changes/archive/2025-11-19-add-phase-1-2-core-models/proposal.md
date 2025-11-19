## Why
Provide shared serializable types for findings, plans, specs, and execution results without tool branding.

## What Changes
- Define FindingLocation with path plus start/end lines.
- Define Finding with id, category, description, locations, metadata for categories like duplicate_block, large_file, missing_docstring, organize_candidate, advanced_cleanup.
- Define CleanupPlan, SpecChange, and ExecutionResult models that can be instantiated and serialized without extra dependencies.

## Impact
- Analyzers, planners, and executors can exchange structured data via stable contracts.
- Models stay decoupled from specific tools or branding.
