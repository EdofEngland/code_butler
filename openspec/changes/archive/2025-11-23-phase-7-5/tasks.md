## 1. CLI wiring

- [x] 1.1 Register an `ai-clean annotate [PATH] [--mode missing|all]` subcommand in `ai_clean/cli.py`:
  - [x] Add `"annotate"` to `_COMMAND_SPECS` with a help text referencing docstring improvements.
  - [x] Add optional `--root` (defaults to `"."`) and `--config` (optional).
  - [x] Add optional `--path` (or positional `path`) to restrict analysis.
  - [x] Add `--mode` flag restricted to `missing` or `all` (default `missing`).
  - [x] Set `handler=_run_annotate_command`.

## 2. Docstring analyzer integration

- [x] 2.1 In `_run_annotate_command`, call `find_docstring_gaps` (or `analyze_repo` then filter) to obtain docstring-related findings.
- [x] 2.2 Filter findings by category based on `--mode`:
  - [x] For `missing`: include only `missing_docstring`.
  - [x] For `all`: include both `missing_docstring` and `weak_docstring`.
- [x] 2.3 Sort docstring findings deterministically (e.g. by path then symbol name) before display.

## 3. Target selection

- [x] 3.1 Display a concise list of targets:
  - [x] Group findings by module or file.
  - [x] For each group, show file path and a count of affected symbols.
- [x] 3.2 Implement a selection mechanism that lets the user:
  - [x] Choose “all modules”.
  - [x] Choose a subset by index (comma-separated).
  - [x] Cancel with a clear message.

## 4. Plan generation

- [x] 4.1 For each selected module or symbol group:
  - [x] Call `plan_from_finding` from `ai_clean.planners.orchestrator` for each relevant finding.
  - [x] Combine or keep separate plans based on planner behavior, but always ensure stable IDs.
- [x] 4.2 Persist each docstring `CleanupPlan` to `.ai-clean/plans/` using `ai_clean/plans.py`.

## 5. Apply integration

- [x] 5.1 After creating plans, prompt the user:
  - [x] Offer options to “save plans only” or “apply now using `ai-clean apply PLAN_ID`”.
- [x] 5.2 When applying immediately:
  - [x] Delegate to the standard `/apply` flow instead of duplicating apply/test logic.
- [x] 5.3 Print a short summary of how many docstrings were planned and how many plans were applied.

## 6. Constraints

- [x] 6.1 Keep `/annotate` focused on docstring-related findings; do not mix in structural or duplicate code issues.
- [x] 6.2 Ensure the command remains deterministic (stable ordering, no timestamps, no random sampling of findings).
