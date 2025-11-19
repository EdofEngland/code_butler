## Why
Translate duplicate_block findings into actionable plans to extract shared helpers.

## What Changes
- Generate CleanupPlans from duplicate_block findings with intent to extract helpers and replace duplicates.
- Outline steps to choose helper module, create helper, and replace occurrences without changing behavior or public APIs.
- Attach default tests to run and scope plans only to listed locations, splitting when many occurrences exist.

## Impact
- Provides repeatable plans to de-duplicate code safely.
- Keeps each plan small and tied to specific occurrences.
