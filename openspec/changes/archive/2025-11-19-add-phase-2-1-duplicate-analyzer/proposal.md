## Why
Surface repeated Python code blocks as structured findings to drive deduplication plans.

## What Changes
- Recursively scan target paths for Python files and build normalized windows of code lines using configurable window size.
- Group identical windows across files and emit Findings with category duplicate_block containing occurrence counts and locations.
- Keep analysis deterministic and resource-bounded with configurable thresholds.

## Impact
- Identifies redundancy hotspots for later planning.
- Produces location-rich findings for targeted refactors.
