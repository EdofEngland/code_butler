## 1. CLI wiring

- [x] 1.1 Ensure `ai-clean cleanup-advanced` is registered in `ai_clean/cli.py`:
  - [x] `"cleanup-advanced"` already appears in `_COMMAND_SPECS`; keep the help text aligned with advanced cleanup behavior.
  - [x] Confirm the subparser accepts `--root`, `--config`, `--findings-json`, and optional `--json`.
  - [x] Keep `handler=_run_cleanup_advanced_command`.

## 2. Advanced analyzer integration

- [x] 2.1 In `ai_clean/commands/advanced_cleanup.py`, ensure `run_advanced_cleanup`:
  - [x] Loads config via `load_config(config_path)`.
  - [x] Loads findings from the `--findings-json` path into `Finding` objects.
  - [x] Calls `collect_advanced_cleanup_ideas(root, findings, config, runner)` with a Codex runner from `get_codex_prompt_runner`.
- [x] 2.2 Confirm that advanced findings use the `advanced_cleanup` category and include enough metadata for planning.

## 3. CLI behavior and output

- [x] 3.1 Implement `_run_cleanup_advanced_command` in `ai_clean/cli.py` to:
  - [x] Resolve `root` and `config_path`.
  - [x] Call `run_advanced_cleanup`.
  - [x] Respect `--json` flag using `_print_findings`, identical to `/analyze`.
  - [x] Handle file/config load errors and unexpected exceptions with clear messages and non-zero exits.
- [x] 3.2 Ensure findings are printed in deterministic order (relying on the ordering returned by `collect_advanced_cleanup_ideas`).

## 4. Plan generation (no auto-apply)

- [x] 4.1 Document that `/cleanup-advanced` is an analysis-only command that surfaces `advanced_cleanup` findings but does not apply changes directly.
- [x] 4.2 Add follow-up guidance in the CLI output:
  - [x] For each finding, show its ID and a hint: `Use 'ai-clean plan {FINDING_ID}' to create a plan.`
  - [x] Do **not** invoke `plan_from_finding` or `/apply` from within `/cleanup-advanced`.

## 5. Constraints

- [x] 5.1 Keep `/cleanup-advanced` non-interactive apart from flags; it should not prompt for selections or apply decisions.
- [x] 5.2 Ensure all Codex calls are routed through the existing factories and runners and are used only to generate findings, not patches.
