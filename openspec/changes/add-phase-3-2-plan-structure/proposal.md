## Why
Provide structured plans for large files and long functions with controlled scope.

## What Changes
- For large_file findings, plan to split into 2-3 logical modules with grouped responsibilities and minimal public API impact.
- For long_function findings, plan helper extraction steps scoped to the function or closely related code only.
- Outline constraints to preserve behavior and avoid deep nesting, using re-exports if needed.

## Impact
- Enables safer refactors of oversized code while clarifying boundaries.
- Keeps plan scope narrow to reduce regression risk.
