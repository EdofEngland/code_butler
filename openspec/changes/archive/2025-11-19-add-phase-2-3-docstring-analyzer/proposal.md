## Why
Find documentation gaps to enable annotate-focused cleanups.

## What Changes
- Inspect modules for missing or empty docstrings and flag them.
- Inspect public classes and functions (non-underscored) for missing or trivial docstrings and classify as missing_docstring or weak_docstring.
- Optionally gate symbol checks by importance such as size thresholds.

## Impact
- Creates findings to guide docstring improvements.
- Keeps focus on public/important symbols for initial release.
