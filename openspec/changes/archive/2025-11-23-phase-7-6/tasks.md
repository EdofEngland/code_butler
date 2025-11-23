## 1. CLI wiring

- [x] 1.1 Register an `ai-clean organize [PATH]` subcommand in `ai_clean/cli.py`:
  - [x] Add `"organize"` to `_COMMAND_SPECS` with a help text describing file regrouping.
  - [x] Add optional `--root` (defaults to `"."`) and `--config` (optional).
  - [x] Add optional `--path` (or positional `path`) to restrict analysis.
  - [x] Set `handler=_run_organize_command`.

## 2. Organize analyzer integration

- [x] 2.1 In `_run_organize_command`, call `propose_organize_groups` from `ai_clean.analyzers.organize` (or use `analyze_repo` then filter `organize_candidate` findings).
- [x] 2.2 Ensure findings are filtered to `organize_candidate` category only.
- [x] 2.3 Sort candidates deterministically, e.g. by topic then by file path, matching the analyzer’s ordering.

## 3. Candidate presentation and selection

- [x] 3.1 Group `organize_candidate` findings by topic or group ID based on analyzer metadata.
- [x] 3.2 Print each candidate with topic label and numbered member files.
- [x] 3.3 Implement a selection prompt:
  - [x] Allow selecting one or more candidate groups by index.
  - [x] Provide a way to select none and exit.

## 4. Plan generation and persistence

- [x] 4.1 For each selected `organize_candidate` finding:
  - [x] Call `plan_from_finding` in `ai_clean.planners.orchestrator` with current config.
  - [x] Ensure generated `CleanupPlan` objects describe file moves in their metadata (e.g. source and destination paths).
- [x] 4.2 Save each plan under `.ai-clean/plans/` using `ai_clean/plans.py` helpers.
- [x] 4.3 Print a summary line per plan including ID, target topic, and number of files affected.

## 5. Apply or store behavior

- [x] 5.1 After writing each plan, prompt the user:
  - [x] “Save organize plan only” vs “Apply now”.
- [x] 5.2 When applying immediately:
  - [x] Call the existing `/apply` pipeline with the plan ID and show diff stats.
- [x] 5.3 When saving only:
  - [x] Print a reminder command: `ai-clean apply {PLAN_ID}`.

## 6. Constraints

- [x] 6.1 Do not perform file moves directly in `/organize`; all changes must go through plan → spec → apply.
- [x] 6.2 Keep behavior deterministic: same inputs produce the same candidate ordering and plan IDs.
