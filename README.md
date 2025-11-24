# ai-clean

ai-clean is a ButlerSpec-governed cleanup assistant that scans a repository for
issues, turns findings into CleanupPlans, converts those plans into ButlerSpec
YAML, and executes them through a Codex shell executor. Metadata (plans, specs,
results) lives under `.ai-clean/` by default so plan → spec → apply runs stay
traceable.

## Capabilities

- **Static analyzers (Python tools)** — Duplicate, structure, docstring, and organize analyzers run locally with no LLM calls. Use when you want deterministic signals about code smells in Python files. Not useful for non-Python code or subjective style feedback.
- **Cleanup planning (Python tools)** — Planners turn findings into ButlerSpec-ready CleanupPlans with guardrails (file/line limits, concern splitting). Use to stage small, local changes. Not a refactor orchestrator; will refuse oversized or mixed-scope plans.
- **Spec generation (Python tools)** — ButlerSpec backend serializes plans into `<plan>-spec.butler.yaml` with validation (single target file, <=25 actions). Use to keep a traceable spec for Codex. Won’t run code or apply changes.
- **Execution (Codex/LLM required)** — `apply` invokes the Codex shell executor to run the spec and optional tests. Requires a working `codex` binary. Without Codex, specs are written but no code changes happen.
- **Review (Codex/LLM required)** — `changes-review` sends plan/spec/diff metadata to a Codex reviewer for advisory risk checks. Needs the Codex prompt runner; otherwise it will fail.
- **Advanced cleanup ideas (via Codex slash command)** — `cleanup-advanced` is disabled in ai-clean; instead, run `codex /cleanup-advanced <PAYLOAD_PATH>` from Codex CLI. ai-clean will show the slash command and payload path but does not call Codex.

Use ai-clean when you want reproducible, small-scope cleanups with explicit plan/spec metadata. Skip it for large architectural refactors, non-Python codebases, or environments without the Codex binary (execution/review/advanced flows will be no-ops or fail).

## Setup

- Install the CLI with `pip install -e .` and run `python -m ai_clean.cli --help`
  (or `ai-clean --help` if your environment wires the entrypoint).
- A valid `ai-clean.toml` is required. Commands look under `<root>/ai-clean.toml`
  unless `--config` points elsewhere. The file must define `spec_backend`,
  `executor`, `review`, `git`, `tests`, `plan_limits`, and `analyzers.*`; the
  checked-in config covers the required sections and defaults.
- All commands except `analyze` create metadata directories under the chosen
  `--root` (overridable via `metadata.*` in the config). `apply` will switch to
  the configured refactor branch (`git checkout -B <refactor_branch> origin/<base_branch>`)
  before executing Codex.

## How to Use

1) **Scan a repo**
```bash
ai-clean analyze --root . --json > findings.json
```
Generates JSON findings without writing metadata.

2) **Plan and apply a quick cleanup**
```bash
ai-clean clean --root . --path src/  # pick duplicate/structure findings interactively
# choose "apply" for a plan to write .ai-clean/specs/... and run Codex + tests
```
Creates plans for eligible findings; lets you save or apply immediately.

3) **Fix docstrings**
```bash
ai-clean annotate --root . --mode all api/handlers.py
# select modules to plan; choose save/apply when prompted
```
Focuses only on docstring gaps/weak spots.

4) **Create a plan from saved findings**
```bash
ai-clean plan dup-1234 --root . --findings-json findings.json
# plans are saved under .ai-clean/plans/
ai-clean apply dup-1234-helper-1 --root .
```
Separates plan creation from execution.

5) **Get organize suggestions**
```bash
ai-clean organize --root .
# pick topic groups; save or apply each plan
```

6) **Review a run**
```bash
ai-clean changes-review dup-1234-helper-1 --root .
```
Summarizes risk/constraints using Codex reviewer (requires Codex).

## Command overview

- `analyze` — Runs the duplicate, structure, docstring, and organize analyzers
  using the loaded config. Fails fast if the config file is missing. Emits a
  text table or JSON array of Finding objects. Read-only; no metadata writes.
  Options: `--root`, `--config`, `--json`.
- `clean` — Runs all analyzers, filters to `duplicate_block`, `large_file`, and
  `long_function`, and optionally limits to `--path`. Prompts you to pick
  findings, creates plans under `.ai-clean/plans/`, and for each plan asks
  whether to save or apply immediately. Applying writes the ButlerSpec to
  `.ai-clean/specs/`, prints the Codex slash command for manual execution, and
  records the spec path and not-executed status.
- `annotate` — Docstring-focused workflow. Supports a positional path or
  `--path` filter. Modes: `missing` (default) or `all` (includes weak
  docstrings). Groups findings by module, creates plans for the selected
  modules, saves them, and optionally applies all immediately.
- `organize` — Runs the organize analyzer, shows candidate topic groups, lets
  you select indices, then creates plans (saved under `.ai-clean/plans/`) and
  asks to apply each now or save for later.
- `cleanup-advanced` — ai-clean fails fast and prints the slash command to run
  manually: `codex /cleanup-advanced <PAYLOAD_PATH>` (use an absolute path or run
  from repo root). No Codex calls are made by ai-clean; run the slash command in
  Codex CLI with your findings/snippets payload.
- `plan` — Loads findings JSON (default `<root>/.ai-clean/findings.json` or
  `--findings-json`) and creates plan(s) for the specified `finding_id`. Plans
  are persisted under `.ai-clean/plans/` and summarized to stdout; nothing is
  applied here.
- `apply` — Loads a saved plan by ID, converts it to ButlerSpec
  `.ai-clean/specs/<plan>-spec.butler.yaml`, and stops. Execution is manual:
  ai-clean prints the absolute spec path and slash command
  (`codex /butler-exec <SPEC_PATH>`) to run inside Codex CLI; repo-root-relative
  paths are acceptable if you prefer them. ai-clean saves an ExecutionResult with
  `success=False`, `tests_passed=None`, and `metadata.manual_execution_required=True`
  to `.ai-clean/results/<plan>.json` to record that apply was not run.
- `/butler-exec` (Codex CLI) — Run `codex /butler-exec <SPEC_PATH>` to execute a
  ButlerSpec. Use an absolute path (or run from the repo root if using a relative
  path). Codex CLI handles auth; the command emits only the unified diff and an
  optional tests block if the spec defines a test command.
- `changes-review` — Reads the plan, spec (if present), and execution result for
  a `plan_id`, attaches any available git diff, and sends it through the Codex
  review executor. Prints summary/risk/manual checks plus warnings when the spec,
  diff, or test metadata is missing.

## Analyzer behavior

### Duplicate detection (`/analyze`, `/clean`)
- Scans Python files (skipping ignored directories) with sliding windows
  (`window_size` default 5). Comment-only windows are ignored.
- Emits `duplicate_block` findings when a normalized window appears at least
  `min_occurrences` times (default 2). Metadata includes window size, the
  normalized snippet, and relative paths.

### Structure analyzer (`/analyze`, `/clean`)
- Flags `large_file` findings when a file exceeds `max_file_lines` (default
  400) with a single file-level location.
- Flags `long_function` findings when a function exceeds `max_function_lines`
  (default 60) with the function span location. A file can emit multiple
  findings. Shares the ignore list with the duplicate analyzer.

### Docstring analyzer (`/analyze`, `/annotate`)
- Walks modules, classes, and functions (public only; names starting with `_`
  are skipped). Emits `missing_docstring` when absent/empty and `weak_docstring`
  when shorter than `min_docstring_length` (default 32) or containing markers
  like `todo`/`fixme`/`tbd`.
- Symbols shorter than `min_symbol_lines` (default 5) are skipped when
  `important_symbols_only` is true (default). Locations point to the symbol
  span; metadata includes qualified name, preview, and line counts.

### Organize analyzer (`/analyze`, `/organize`)
- Suggests grouping related files into a topic directory by comparing filename
  tokens, imports, and module docstrings. Skips ignored directories plus stable
  folders like `tests/` and `migrations/`.
- Emits `organize_candidate` findings capped by `min_group_size`, `max_group_size`
  (defaults 2–5), and `max_groups` (default 5). Metadata lists the topic and
  member file paths.

## Advanced cleanup analyzer (slash command)

The advanced analyzer runs via the Codex slash command `/cleanup-advanced`:
- Prepare a payload JSON that includes prior findings (`description`, `path`,
  `start_line`, `end_line`, `change_type`), file snippets, and limits
  (`max_files`, `max_suggestions`, `max_snippet_lines`).
- Run `codex /cleanup-advanced <PAYLOAD_PATH>` from Codex CLI (absolute path
  recommended; if relative, run from the repo root containing the files).
- Output is JSON-only suggestions (`description`, `path`, `start_line`,
  `end_line`, `change_type`, `model`, `prompt_hash`). If the payload is invalid
  or exceeds limits, the command returns `Error: <reason>` with no suggestions.
ai-clean does not invoke Codex; it only prints the slash command for you to run.

## Planning and apply guardrails

- `plan_from_finding` dispatches per category and enforces plan limits
  (`max_files_per_plan`, `max_changed_lines_per_plan`). Multi-target plans are
  split when allowed; over-limit plans raise errors.
- Duplicate plans group up to three occurrences per helper plan and refuse to
  proceed without a configured test command. Docstring plans also require a
  test command.
- ButlerSpec generation validates metadata size, a single target file, and caps
  action count at 25 before writing `<plan>-spec.butler.yaml`.
