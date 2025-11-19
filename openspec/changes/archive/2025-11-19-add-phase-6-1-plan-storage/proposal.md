## Why
Persist CleanupPlans to disk and reload them losslessly for apply and review flows.

## What Changes
- Provide utilities to save CleanupPlan to .ai-clean/plans/{plan_id}.json.
- Provide utilities to load CleanupPlan by ID with lossless serialization/deserialization.
- Ensure required fields remain intact across save/load operations.

## Impact
- Plans survive across CLI invocations and can be reapplied or reviewed later.
- Serialization fidelity avoids data loss.
