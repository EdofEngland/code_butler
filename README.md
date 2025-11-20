# ai-clean

`ai-clean` is a CLI toolkit to analyze a codebase, propose scoped cleanup plans, and optionally apply them in a structured way.

## Capabilities
**What it does**
- Scans repositories with analyzer pipelines for duplicate blocks, structural smells, docstring gaps, and organize candidates, surfacing actionable findings via `/analyze`.
- Converts any supported finding into a scoped CleanupPlan, storing JSON under `.ai-clean/plans/` and keeping category-specific constraints (docstring, structure, organize, duplicate, advisory cleanups).
- Applies stored plans by converting them to OpenSpec specs, running the configured executor/test commands, and persisting execution logs under `.ai-clean/specs/` and `.ai-clean/executions/`.
- Summarizes applied work—including diffs, stored test results, and Codex review output—through `/changes-review` for easy sharing with reviewers.

**Limitations**
- Docstring and structural findings must stay within a single file, organize plans only move files (no edits), and advisory `/cleanup-advanced` plans never auto-apply; global renames are rejected unless explicitly allowed.
- `/clean` only targets duplicate/large/long findings and caps automatic planning at three items; other categories require dedicated flows such as `/annotate` or `/organize`.
- `ai-clean apply` enforces the configured `git.base_branch`/`git.refactor_branch`, depends on the OpenSpec backend, and requires a valid plan saved on disk before it can run.

## How To Use
### Analyze first
Run `ai-clean analyze <path>` (usually the repo root) to gather findings before every cleanup session. Use `--categories` to narrow results if you're only interested in `missing_docstring`, `long_function`, etc. Skipping this step or pointing at the wrong directory will leave you with stale finding IDs that downstream commands cannot plan.

### Structural cleanups (`/clean`)
After analyzing, run `ai-clean clean <path>` to review duplicate blocks, large files, and long functions. Interactively select up to three findings (or pass `--auto`) to create scoped plans, then choose whether to apply them immediately. Do not use `/clean` for docstring-only or organize-only work; those concerns have dedicated flows and `/clean` will ignore them.

### Docstrings (`/annotate`)
Use `ai-clean annotate <path> [--mode missing|weak|all]` when you're targeting missing or weak docstrings. The command prints the findings, builds plans, and optionally applies them. Avoid using `/annotate` to refactor logic or touch multiple files—it should only introduce or polish docstrings inside the single file flagged by the analyzer.

### Organize-only moves (`/organize`)
Run `ai-clean organize <path> [--max-files N]` to find groups of files that should move together. Inspect the suggested destination, select IDs (or pass `--ids ...`), and optionally apply the resulting move-only plans. Do not use this flow when files need content changes or renames; it is limited to moving a handful of files to a new folder as-is.

### Advisory cleanups (`/cleanup-advanced`)
When you want higher-level suggestions without touching the working tree, call `ai-clean cleanup-advanced <path> [--limit N]`. The tool emits Codex advisory plans and saves them for later review. It deliberately never auto-applies these ideas, so don't expect code changes; treat it as a brainstorming aid rather than an enforcement tool.

### Manual planning (`/plan`)
If you already know the finding ID you want to fix, run `ai-clean plan <finding_id> --path <path> [--chunk-index N]` to rebuild the plan details and store them under `.ai-clean/plans/`. Use this for single findings when you want to inspect the plan text before deciding on any apply step. Do not guess IDs or skip the `--path` disambiguation when multiple findings share the same ID, or the planner will fail.

### Applying plans (`/apply`)
Once a plan looks good, execute `ai-clean apply <plan_id> [--skip-tests --spec-dir DIR]`. The command enforces the configured refactor branch, writes the spec via the OpenSpec backend, runs the executor and tests, then records logs under `.ai-clean/specs/` and `.ai-clean/executions/`. Avoid running `/apply` directly on your main branch or against a plan you have not reviewed—the command assumes the stored plan is ready to execute.

#### Running apply outside Codex
By default, `ai-clean apply` invokes `scripts/apply_spec_wrapper.py`, which first tries `/prompts:openspec-apply {spec_path}` (available inside Codex) and falls back to other commands or the stub. When developing locally:
- `AI_CLEAN_USE_APPLY_STUB=1 ai-clean apply <plan_id>` forces the wrapper's stub helper to print `[stub] Would apply spec located at ...` without touching your working tree—handy for dry runs.
- `AI_CLEAN_APPLY_COMMAND="echo applying {spec_path}" ai-clean apply <plan_id>` (or any other command containing `{spec_path}`) lets you override the wrapper's default command list.
Make sure whatever override you provide includes the `{spec_path}` placeholder so ai-clean can substitute the generated OpenSpec change file.
When validating inside Codex, leave these env vars unset so the wrapper runs `/prompts:openspec-apply` directly; a successful apply will print the spec path, execution log location, and test status in the CLI output.

### Reviewing changes (`/changes-review`)
After a successful apply, run `ai-clean changes-review <plan_id> [--diff-command CMD --verbose]` to bundle the stored plan, execution metadata, and current diff into a Codex review summary. Use it before opening a PR to capture risks and recommended follow-up checks. If a plan was never applied—or tests never ran—`/changes-review` will refuse to run; do not rely on it as a substitute for running the actual cleanup.

## Commands
- `/analyze [PATH] [--categories ...]`: run every analyzer (duplicate blocks, structural, docstring, organize) and print real findings with location summaries so you can decide what to clean up first.
- `/clean [PATH] [--auto --skip-tests --spec-dir]`: filter duplicate/large/long findings, let you select up to three, build plans, and optionally run the apply pipeline immediately.
- `/annotate [PATH] [--mode --all --skip-tests --spec-dir]`: focus on missing or weak docstrings, show detailed plan info, and optionally apply fixes on the spot.
- `/organize [PATH] [--max-files --ids --skip-tests --spec-dir]`: surface organize candidates that move files into clearer folders and, if confirmed, apply the move-only plans.
- `/cleanup-advanced [PATH] [--limit]`: list Codex advisory cleanups (stored as plans for review) without touching the working tree.
- `/plan FINDING_ID [--path --chunk-index]`: rebuild a plan for a specific finding and display its steps, constraints, and tests.
- `/apply PLAN_ID [--skip-tests --spec-dir]`: enforce the configured refactor branch, turn a stored plan into a spec, run the executor/tests, and persist execution logs under `.ai-clean/`.
- `/changes-review PLAN_ID [--diff-command --verbose]`: reload the plan plus its execution record, note the stored test status, capture the current diff, and feed everything into the review executor for a summarized risk report.

Run `ai-clean --help` for the latest option details.

## Configuration
- `ai-clean` reads `ai-clean.toml` to discover the spec backend (`[spec_backend] type = "openspec"`), executor command (must include `{spec_path}`), review backend, enforced git branches, and default test command.
- `[limits]` controls safety rails such as maximum files/lines per plan and the `allow_global_rename` flag (off by default), which determines whether rename steps are permitted.
- Metadata lives under `.ai-clean/`, where the tool automatically maintains `plans/`, `specs/`, and `executions/` directories referenced by the CLI flows.

## Plan constraints

Plans generated by ai-clean focus on a single concern at a time to keep diffs small and reviewable:
- Docstring and structural findings must stay within a single file; multiple files require separate findings.
- Organize, duplicate, and advanced cleanup findings may involve more files but are still scoped to one category intent.
- Global renames or API-wide changes are disabled by default; plans containing rename steps are rejected unless explicitly enabled in configuration.

If a finding violates these constraints (e.g., a docstring request spanning multiple files), the CLI surfaces an error so you can create smaller, single-purpose findings.

## Test-first policy

Every `/apply` run records test execution details (command, exit code, and logs) and stores them under `.ai-clean/executions/`. The CLI highlights the test result status after each apply and `/changes-review` replays the stored status so reviewers know whether tests ran. If tests fail—or are skipped because the apply failed—the CLI prints the failing command and points to the execution log so you can rerun tests locally before retrying.
