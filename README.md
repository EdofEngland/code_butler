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
- **Advanced cleanup ideas (Codex/LLM required)** — `cleanup-advanced` builds prompts from prior findings to ask Codex for suggestions. Default runner is a stub that returns non-JSON, so no findings appear until you provide a real Codex prompt runner.

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
  `.ai-clean/specs/`, runs the Codex shell executor and tests, and prints spec
  path, success, tests status, and git diff.
- `annotate` — Docstring-focused workflow. Supports a positional path or
  `--path` filter. Modes: `missing` (default) or `all` (includes weak
  docstrings). Groups findings by module, creates plans for the selected
  modules, saves them, and optionally applies all immediately.
- `organize` — Runs the organize analyzer, shows candidate topic groups, lets
  you select indices, then creates plans (saved under `.ai-clean/plans/`) and
  asks to apply each now or save for later.
- `cleanup-advanced` — Requires `--findings-json` from a prior `analyze --json`.
  Builds a Codex prompt with the provided findings and selected file snippets.
  The Codex runner must return a JSON array of suggestions
  (`description/path/start_line/end_line/change_type`); the default stub runner
  returns a non-JSON string, so no suggestions are emitted unless you replace
  it. Output is advisory-only; apply via `plan`/`apply` later.
- `plan` — Loads findings JSON (default `<root>/.ai-clean/findings.json` or
  `--findings-json`) and creates plan(s) for the specified `finding_id`. Plans
  are persisted under `.ai-clean/plans/` and summarized to stdout; nothing is
  applied here.
- `apply` — Loads a saved plan by ID, converts it to ButlerSpec
  `.ai-clean/specs/<plan>-spec.butler.yaml`, runs the Codex shell executor
  (`executor.binary` + `apply_args`), executes the configured default tests, and
  saves the ExecutionResult to `.ai-clean/results/<plan>.json`. Prints spec
  path, success flag, tests status, git diff, stdout/stderr.
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

## Advanced cleanup analyzer

The advanced analyzer (used only by `cleanup-advanced`) selects up to
`max_files` finding locations, attaches file snippets (±3 lines around each
span, capped at 40 lines), and embeds an always-on guardrail sentence. It
expects the Codex response to be a JSON array of suggestions with
`description`, `path`, `start_line`, `end_line`, and `change_type` keys. It
drops suggestions outside the selected files, disallowed change types, or over
`max_suggestions`. Metadata on each finding includes the prompt hash, model
name, and raw Codex payload for traceability. With the default stub runner no
findings are produced because the response is not JSON.

## Planning and apply guardrails

- `plan_from_finding` dispatches per category and enforces plan limits
  (`max_files_per_plan`, `max_changed_lines_per_plan`). Multi-target plans are
  split when allowed; over-limit plans raise errors.
- Duplicate plans group up to three occurrences per helper plan and refuse to
  proceed without a configured test command. Docstring plans also require a
  test command.
- ButlerSpec generation validates metadata size, a single target file, and caps
  action count at 25 before writing `<plan>-spec.butler.yaml`.
