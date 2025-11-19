## Why
Enforce configuration for max files and lines per plan to keep diffs small.

## What Changes
- Introduce settings for maximum files and total changed lines per plan.
- Have planners and advanced analyzer split work into multiple plans when limits are exceeded.
- Validate limits are enforced during planning.

## Impact
- Prevents oversized plans and keeps reviews manageable.
- Large changes are automatically partitioned.
