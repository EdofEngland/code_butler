## Why
Keep each CleanupPlan focused on one concern to simplify review and execution.

## What Changes
- Enforce rule that each plan addresses a single concern such as one helper extraction, one file split, one file move group, one small docstring batch, or one advanced suggestion.
- Update planners to reject or split multi-concern proposals.
- Document the constraint for consistency.

## Impact
- Plans remain small, deterministic, and easy to review.
- Reduces risk of tangled changes.
