## 1. CLI wiring

- [x] 1.1 Register an `ai-clean plan FINDING_ID` subcommand in `ai_clean/cli.py`:
  - [x] Add `"plan"` to `_COMMAND_SPECS` with a help string that references findings.
  - [x] Add positional argument `finding_id`.
  - [x] Add optional `--root` (defaults to `"."`) and `--config` (optional path).
  - [x] Set `handler=_run_plan_command`.

## 2. Finding resolution

- [x] 2.1 Decide the finding source for `/plan`:
  - [x] Initially, read findings from a JSON file argument (e.g. `--findings-json`) or from a fixed `.ai-clean/findings.json` location as described in the ButlerSpec plan docs.
  - [ ] Document the chosen source in the help text and in `docs/butlerspec_plan.md` if needed (separate change).
- [x] 2.2 Implement a helper in `ai_clean/cli.py` or `ai_clean/commands/plan.py` that:
  - [x] Loads the findings JSON into a list of `Finding` objects (using `Finding.model_validate`).
  - [x] Searches for `Finding.id == FINDING_ID`.
  - [x] Raises a clear error if the finding is not present, including the ID that was requested.

## 3. Plan creation via planners

- [x] 3.1 Add a helper `run_plan_for_finding(...)` in `ai_clean/commands/plan.py` that:
  - [x] Accepts `root: Path`, `config_path: Path | None`, and `finding: Finding`.
  - [x] Loads config with `load_config` from `ai_clean.config`.
  - [x] Calls `plan_from_finding(finding, config)` from `ai_clean.planners.orchestrator`.
  - [x] Returns a list of `CleanupPlan` objects.
- [x] 3.2 Ensure `ai_clean/planners/orchestrator.py` already covers relevant categories:
  - [x] `duplicate_block`, `large_file`, `long_function`, `missing_docstring`, `weak_docstring`, `organize_candidate`, `advanced_cleanup`.
  - [x] If an unsupported category is requested, surface `NotImplementedError` as a user-facing error with a clear message.

## 4. Plan persistence

- [x] 4.1 Use `ai_clean/plans.py` helpers to persist plans:
  - [x] Decide whether to use `save_plan(plan, root)` or `write_plan_to_disk(plan, base_dir)`; prefer one and keep it consistent.
  - [x] Ensure plans are written under `.ai-clean/plans/` beneath the chosen root.
- [x] 4.2 Guarantee deterministic IDs and file paths:
  - [x] Use `generate_plan_id(finding.id, suffix)` (or an equivalent helper) to build plan IDs if multiple plans per finding are needed.
  - [x] Confirm that plan filenames follow `{plan.id}.json`.

## 5. CLI output

- [x] 5.1 After saving each plan, print a summary line that includes:
  - [x] `Plan ID`
  - [x] `Title`
  - [x] `Intent`
  - [x] A short preview of `steps` (e.g. count + first item).
  - [x] `constraints` presence (count) and `tests_to_run` presence (count).
- [x] 5.2 When multiple plans are generated for a single finding, print them in a stable order (e.g. sort by `plan.id`).

## 6. Error handling and non-goals

- [x] 6.1 On failure to load findings, config, or write a plan file, exit non-zero with a concise error; do not create partial plan files.
- [x] 6.2 Ensure `/plan` only creates plans and does not invoke `/apply`, write ButlerSpec specs, or run tests.
