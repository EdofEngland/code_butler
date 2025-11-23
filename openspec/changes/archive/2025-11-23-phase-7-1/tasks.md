## 1. CLI wiring

- [x] 1.1 In `ai_clean/cli.py`, ensure the `analyze` subcommand is registered in `_COMMAND_SPECS` with the correct help text.
- [x] 1.2 Configure the `analyze` subparser to accept:
  - [x] `--root` (defaults to `"."`) and map it to a `Path`.
  - [x] `--config` (optional) to override the default `ai-clean.toml` path.
  - [x] `--json` (flag) to control JSON vs text output.
- [x] 1.3 Set `handler=_run_analyze_command` for the `analyze` subparser so `main()` dispatches correctly.

## 2. Analyzer orchestration

- [x] 2.1 Implement `_run_analyze_command` in `ai_clean/cli.py` to:
  - [x] Resolve `root` and `config_path` using `_resolve_config_path(root, args.config)`.
  - [x] Call `analyze_repo(root, config_path)` from `ai_clean.analyzers.orchestrator`.
  - [x] Catch `FileNotFoundError` for missing config and print a clear error to `stderr` with non-zero exit.
  - [x] Catch unexpected exceptions and print a concise error to `stderr` with non-zero exit.
- [x] 2.2 Ensure `ai_clean/analyzers/orchestrator.py` exposes `analyze_repo` via `__all__` so imports remain stable.

## 3. Output format and determinism

- [x] 3.1 Implement `_print_findings` in `ai_clean/cli.py` to:
  - [x] When `--json` is set, emit a JSON array of `Finding.model_dump(mode="json")` with stable key ordering.
  - [x] When no findings exist, print `No findings detected.` and exit 0.
  - [x] For text output, print one line per finding as `"{id} | {category} | {description}"`.
  - [x] For each finding, print one line per location as `"  - {rel_path}:{start_line}-{end_line}"` using POSIX-style paths.
- [x] 3.2 Keep output deterministic:
  - [x] Ensure `analyze_repo` already sorts findings by `(category, id)` and relies on that ordering.
  - [x] Avoid timestamps or environment-specific prefixes in CLI output.

## 4. Read-only behavior

- [x] 4.1 Confirm that `/analyze` does not create or modify any `.ai-clean` metadata (plans, specs, or execution results).
- [x] 4.2 Document in code (docstring or comment near `_run_analyze_command`) that `/analyze` is read-only and is the entry point for later planning phases.
