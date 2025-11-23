## 1. CLI wiring

- [x] 1.1 Register an `ai-clean clean [PATH]` subcommand in `ai_clean/cli.py`:
  - [x] Add `"clean"` to `_COMMAND_SPECS` with a help text describing “guided basic cleanup”.
  - [x] Add optional `--root` (defaults to `"."`) and `--config` (optional config path).
  - [x] Add optional `--path` (or positional `path`) to limit analyzers to a subtree.
  - [x] Set `handler=_run_clean_command`.

## 2. Analyzer integration and filtering

- [x] 2.1 In `_run_clean_command`, call `analyze_repo` from `ai_clean.analyzers.orchestrator` for the selected root/config.
- [x] 2.2 Filter the resulting findings to only include:
  - [x] `duplicate_block`
  - [x] `large_file`
  - [x] `long_function`
- [x] 2.3 Sort filtered findings deterministically (e.g. by `(category, id)`) before displaying them.

## 3. Interactive finding selection

- [x] 3.1 Implement a simple selection loop (no external TUI dependency) that:
  - [x] Prints a numbered list of candidate findings with a one-line summary per entry.
  - [x] Allows the user to choose “none”, a single index, or a comma-separated list of indices.
  - [x] Validates input and re-prompts on invalid selections; exits cleanly on Ctrl+C/EOF.
- [x] 3.2 If no findings are selected, print a “No cleanups selected” message and exit 0.

## 4. Plan generation and persistence

- [x] 4.1 For each selected finding:
  - [x] Use `plan_from_finding` from `ai_clean.planners.orchestrator` and current config to create one or more `CleanupPlan` objects.
  - [x] Persist each plan under `.ai-clean/plans/` using the helpers in `ai_clean/plans.py`.
- [x] 4.2 Print one summary line per created plan that includes its ID and target file.

## 5. Apply-or-save decision

- [x] 5.1 For each generated plan, prompt the user with a deterministic question:
  - [x] “(S)ave only”, “(A)pply now”, or “(Skip this plan)”.
  - [x] Default to “save only” if the user presses Enter.
- [x] 5.2 When the user chooses “save only”:
  - [x] Leave the plan on disk and print a hint: `Run 'ai-clean apply {PLAN_ID}' to execute this plan later.`
- [x] 5.3 When the user chooses “apply now”:
  - [x] Reuse the standard `/apply` pipeline (call the same helper used by `ai-clean apply`) instead of duplicating logic.
  - [x] Show a short summary of apply/test results.

## 6. Constraints and non-goals

- [x] 6.1 Keep `/clean` focused on basic categories; do not surface advanced Codex-only findings here.
- [x] 6.2 Avoid non-deterministic output (no random ordering, no timestamps).
- [x] 6.3 Do not create new plan or spec formats; reuse the existing ButlerSpec and plan pipeline.
