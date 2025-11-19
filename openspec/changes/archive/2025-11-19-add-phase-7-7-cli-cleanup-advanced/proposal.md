## Why
Expose advanced_cleanup analyzer results without auto-applying changes.

## What Changes
- Run Codex-powered advanced analyzer on a path and present limited advisory findings.
- Generate CleanupPlans for each advanced finding but do not auto-apply.
- Output plan IDs and summaries for later review or apply.

## Impact
- Users can inspect advisory advanced cleanups safely.
- Advanced suggestions remain manual opt-in.
