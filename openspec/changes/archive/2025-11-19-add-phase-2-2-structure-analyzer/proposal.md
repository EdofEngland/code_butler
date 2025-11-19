## Why
Highlight oversized modules and functions to focus cleanup efforts.

## What Changes
- Detect files whose line count exceeds a configurable threshold and emit large_file findings covering the file span.
- Detect functions whose line count exceeds a configurable threshold and emit long_function findings with precise ranges.
- Allow multiple findings per file with deterministic thresholds.

## Impact
- Surfaces structural hotspots before planning.
- Enables planners to scope refactors to specific large areas.
