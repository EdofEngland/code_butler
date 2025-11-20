## Why
Prevent risky large-scale renames or API redesigns in initial release.

## What Changes
- Add explicit constraints in planners and advanced analyzer prompts forbidding broad public API renames or cross-layer redesigns.
- Downgrade or reject suggestions that violate this policy for v0.
- Ensure prompts and constraints make the limitation clear.

## Impact
- Reduces risk of breaking changes in early versions.
- Keeps cleanup work localized and safe.
