## 1. CLI ingest command
- [x] 1.1 Add `ai-clean ingest --plan-id <id> --artifact <path> [--update-findings]` parser wiring in `ai_clean/cli.py`.
- [x] 1.2 Implement ingest logic (new module or helper) to load existing `ExecutionResult`, parse artifact JSON, validate schema/plan_id/diff/tests, set `manual_execution_required=False`, derive `success/tests_passed`, and persist via `save_execution_result`.
- [x] 1.3 Validate diff format (unified, single file) and required tests block; reject missing/invalid fields with clear errors.
- [x] 1.4 Print a concise summary after ingest (diff stat, tests status).

## 2. Advanced suggestions (optional flag)
- [x] 2.1 Gate mapping of `cleanup-advanced` suggestions behind `--update-findings`.
- [x] 2.2 Validate suggestions payload against the slash-command schema; reject out-of-scope paths or mixed specs.
- [x] 2.3 Persist accepted suggestions into findings JSON (new or existing file), keeping paths within the payload/root.

## 3. Docs and tests
- [x] 3.1 Add unit tests for happy path and invalid artifacts (schema, plan_id mismatch, bad diff/tests).
- [x] 3.2 Add tests for suggestions flag: accepts valid array, rejects invalid/mismatched payloads.
- [x] 3.3 Update README and `docs/executor_manual.md` with the ingest workflow and test/env notes.
