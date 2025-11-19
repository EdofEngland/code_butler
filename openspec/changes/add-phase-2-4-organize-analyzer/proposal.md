## Why
Suggest small, conservative file groupings to prepare for organize moves.

## What Changes
- Infer topics per file from filename, top-level imports, and module docstrings.
- Group related files in flat folders and emit organize_candidate findings suggesting target folders and file lists.
- Keep proposals small (2-5 files) and include locations as file paths.

## Impact
- Provides low-risk organization suggestions for user confirmation.
- Findings reference file paths without needing precise line numbers.
