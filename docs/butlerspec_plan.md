# ButlerSpec Master Plan

## Milestone 1 – Project Skeleton & Core Types

### Phase 1 System Sketch

The `/plan → spec → apply` loop must stay identical in every command:

1. CLI entrypoints such as `/plan` or `/clean` register actions but immediately defer to libraries.
2. Commands construct `CleanupPlan` models (Phase 1.2) describing the intent, constraints, and tests.
3. A `SpecBackend` (Phase 1.3) converts those plans into ButlerSpec YAML, persisting files under `.ai-clean/specs/`.
4. `CodeExecutor` implementations (Phase 1.3) read the generated specs and run Codex or other tooling to apply them.
5. Each execution records an `ExecutionResult` under `.ai-clean/results/`, and `/changes-review` consumes that metadata later.

Phase 1 focuses on ensuring every box in this pipeline exists, even if implementations are placeholders. Later milestones layer analyzers and richer executors onto the same loop.

See `openspec/changes/phase-1-IMPLEMENTATION_ORDER.md` for dependencies and sequencing across the Phase 1 changes.

### Phase 1.1 – Repo & Packaging Setup

* Create a new repo for `ai-clean` (or `code-butler`, whatever name you prefer).
* Add basic packaging:

  * Python project metadata (name, version, dependencies, entrypoint).
  * A CLI entrypoint (e.g. `ai-clean`).
* Add project hygiene:

  * `.gitignore` for Python.
  * `README` with:

    * Purpose of `ai-clean`.
    * Short explanation of core commands: `/analyze`, `/clean`, `/annotate`, `/organize`, `/cleanup-advanced`, `/plan`, `/apply`, `/changes-review`.
* Verify:

  * The CLI runs and prints a help message listing all commands (even if they’re placeholders).

---

### Phase 1.2 – Core Data Model Definitions

* Add a “core models” module defining the **core abstractions**:

  * `FindingLocation`: path + start/end lines.
  * `Finding`: id, category (e.g. `duplicate_block`, `large_file`, `missing_docstring`, `organize_candidate`, `advanced_cleanup`), description, locations, metadata.
  * `CleanupPlan`: id, finding_id, title, intent, steps, constraints, tests_to_run, metadata.
  * `ButlerSpec`: id, plan_id, target_file, intent, actions, model, batch_group, metadata.
  * `ExecutionResult`: spec_id, plan_id, success, tests_passed, stdout, stderr, git_diff (optional), metadata.

* Ensure:

  * Core models have **no dependency** on Codex or any external tools.
  * All types can be created and serialized (JSON/YAML) using only stdlib + pydantic/dataclasses.

---

### Phase 1.3 – Plugin Interfaces

* Define abstract interfaces:

  * `SpecBackend`:

    * `plan_to_spec(plan: CleanupPlan) -> ButlerSpec`
    * `write_spec(spec: ButlerSpec, directory: Path) -> Path` (returns `spec_path`)

  * `CodeExecutor`:

    * `apply_spec(spec_path: Path) -> ExecutionResult`

  * `ReviewExecutor` (for `/changes-review`):

    * `review_change(plan: CleanupPlan, diff: str, exec_result: ExecutionResult) -> str | StructuredReview`

  * (Optional, if you want batching explicit now) `BatchRunner`:

    * `apply_batch(spec_dir: Path, batch_group: str) -> list[ExecutionResult]`

* Ensure:

  * Interfaces depend only on core models + standard libs.
  * No “OpenSpec” terminology; Codex is referenced only in concrete executor implementations, not in interfaces.

---

### Phase 1.4 – Configuration & Local Metadata Layout

* Decide on a config convention:

  * `ai-clean.toml` in repo root with, for example:

    ```toml
    [spec_backend]
    type = "butler"          # our own tooling

    [executor]
    type = "codex_shell"     # shell-wrapped Codex CLI

    [review]
    type = "codex_review"

    [git]
    base_branch = "main"
    refactor_branch = "refactor/ai-clean"

    [tests]
    default_command = "pytest -q"
    ```

* Define local metadata layout:

  * `.ai-clean/plans/` for serialized `CleanupPlan`s.
  * `.ai-clean/specs/` for serialized `ButlerSpec` YAML files.
  * Optional: `.ai-clean/results/` for `ExecutionResult` logs.

* Add simple config loader:

  * Reads and validates config.
  * Exposes typed config objects used by factories.

---

## Milestone 2 – Analyzers

### Phase 2.1 – Duplicate Code Analyzer (Local)

* Implement a local analyzer for **duplicate code blocks**:

  * Recursively scan a target path for Python files.
  * Build normalized windows of code lines (fixed window size).
  * Group identical windows across files.

* For each group with multiple occurrences:

  * Create a `Finding`:

    * `category = "duplicate_block"`.
    * Description: number of occurrences + brief context.
    * Locations: each file and line range.

* Ensure:

  * Deterministic behavior (same inputs → same findings).
  * Thresholds (window size, min occurrences) are config-driven.

---

### Phase 2.2 – Structure Analyzer: Large Files & Long Functions

* Implement a **structure analyzer** for:

  * Files with line count over a threshold (e.g., 400).
  * Functions with line count over a threshold (e.g., 60).

* For large files:

  * `Finding`:

    * `category = "large_file"`.
    * Locations: file-level range.

* For long functions:

  * `Finding`:

    * `category = "long_function"`.
    * Locations: exact function span.

* Ensure thresholds are configurable and multiple findings per file are allowed.

---

### Phase 2.3 – Docstring Analyzer

* Implement a **doc analyzer** to support `/annotate`:

  * For each module:

    * Missing or empty module docstring → `missing_docstring` finding.
  * For each public class/function (no leading `_`):

    * Missing or trivial docstring → `missing_docstring` or `weak_docstring`.

* Each issue becomes a `Finding`:

  * Category as above.
  * Description: symbol name, path, short context.
  * Locations: definition line(s).

* Optional: consider only “important” functions (e.g., above a size threshold) for v0.

---

### Phase 2.4 – Organize Seed Analyzer

* Implement an **organize-seed** analyzer to emit `organize_candidate` findings:

  * For each file, infer topic from:

    * File name,
    * Top-level imports,
    * Module docstring.

  * Group files by rough responsibility (e.g., `logs`, `api`, `cli`, `db`).

* For each proposed group:

  * Emit `Finding`:

    * `category = "organize_candidate"`.
    * Description: suggested folder path + member files.
    * Locations: file paths only.

* Keep proposals small and conservative (2–5 files per finding).

---

### Phase 2.5 – Analyzer Orchestrator

* Implement `analyze_repo(path: Path) -> list[Finding]`:

  * Calls:

    * Duplicate analyzer,
    * Structure analyzer,
    * Doc analyzer,
    * Organize-seed analyzer.

  * Dedupes and returns a combined list with stable IDs.

* Integrate into `/analyze` command:

  * Prints ID, category, description, and locations.

---

### Phase 2.6 – Codex-Powered Advanced Cleanup Analyzer

* Implement an **advanced cleanup analyzer** that uses Codex, but only to propose **small cleanup ideas**, not to apply them:

  * Input:

    * Selected files/snippets.
    * Summary of existing findings.
    * Clear prompt: “Suggest small, local cleanup changes only; no API redesigns.”

  * Output (Codex):

    * Structured suggestions: description + target file + line ranges + suggested change type.

* Convert each suggestion into a `Finding`:

  * `category = "advanced_cleanup"`.
  * Detailed metadata (target file/lines, description).

* Guardrails:

  * Hard limit on number of suggestions and files per run.
  * These findings stay advisory until turned into `CleanupPlan`s.

---

## Milestone 3 – Planner (Findings → CleanupPlans)

### Phase 3.1 – Planner for Duplicate Blocks

* For each `duplicate_block` finding, create a `CleanupPlan`:

  * Intent:

    * Extract reusable helper and replace duplicates.

  * Steps:

    * Decide helper location.
    * Create helper function/class.
    * Replace duplicate blocks with calls.

  * Constraints:

    * No external behavior changes.
    * No public API changes.

  * Tests:

    * Default test command from config.

* Keep each plan **small**:

  * If a finding has many occurrences, split into multiple plans.

---

### Phase 3.2 – Planner for Large Files & Long Functions

* For `large_file`:

  * Intent: Split into 2–3 logical modules.
  * Steps:

    * Group code by responsibility.
    * Create new modules.
    * Move code and adjust imports.
  * Constraints:

    * Preserve public API, using re-exports if needed.

* For `long_function`:

  * Intent: Extract helpers to reduce length.
  * Steps:

    * Identify logical sub-blocks.
    * Extract into helpers.
    * Call helpers from original function.
  * Constraints:

    * Scope limited to the single function or very close neighbors.

---

### Phase 3.3 – Planner for Docstring Findings

* For `missing_docstring` / `weak_docstring`:

  * Intent: Add or improve docstrings.

  * Steps:

    * Infer behavior from code.
    * Draft concise, factual docstring.
    * Insert/replace docstring.

  * Constraints:

    * No renames or behavior changes.
    * No fictional guarantees; docstrings must reflect existing behavior (or explicitly call out assumptions).

* Scope: plan per module or tight group of related symbols to keep small.

---

### Phase 3.4 – Planner for Organize Candidates

* For `organize_candidate`:

  * Intent: Move a small group of files into a better folder.

  * Steps:

    * Create folder if needed.
    * Move files.
    * Update imports and add re-exports as necessary.

  * Constraints:

    * No changes to function bodies.
    * Avoid deep nesting.

* Each `CleanupPlan` moves only a **small set** of files.

---

### Phase 3.5 – Planner for Advanced Cleanup

* For `advanced_cleanup`:

  * Intent: Implement a single, small Codex-suggested improvement.

  * Examples:

    * Simplify conditional.
    * Standardize naming within module.
    * Remove obviously dead code in a narrow scope.

  * Constraints:

    * Local change only (small patch).
    * Limit number of files + total changed lines.

* Plans should be **review-friendly**: small, self-contained.

---

### Phase 3.6 – Planning Orchestrator

* Implement `plan_from_finding(finding: Finding) -> CleanupPlan`:

  * Dispatch by `category`.
  * Generate a **single** plan for each invocation.

* Provide helpers to:

  * Generate unique plan IDs.
  * Serialize plans to `.ai-clean/plans/{plan_id}.json`.

---

## Milestone 4 – ButlerSpec Backend & Spec Files (Our Own Tooling)

### Phase 4.1 – ButlerSpec Backend: Plan → ButlerSpec

* Implement `ButlerSpecBackend` (your OpenSpec replacement):

  * Accepts a `CleanupPlan`.

  * Enforces governance:

    * **One target file per plan** (one-plan-per-file).
    * Any violation → clear error.

  * Produces a `ButlerSpec` with fields like:

    * `id`: spec id.
    * `plan_id`.
    * `target_file`.
    * `intent`.
    * `actions`: structured instructions for the executor/model.
    * `model`: e.g., `"codex"` (or `"local_jamba"` later).
    * `batch_group`: optional grouping name for batches.
    * `metadata` (constraints, tests).

* Keep the payload:

  * Small, deterministic, and human-readable.

---

### Phase 4.2 – Writing ButlerSpec Files

* Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path`:

  * File name: `{spec.id}.butler.yaml`.
  * Directory: `.ai-clean/specs/` by default.
  * Content: YAML serialization of the `ButlerSpec`.

* Guardrails:

  * Each spec file corresponds to a **single, small change** in a single file.
  * No multi-topic specs.

---

### Phase 4.3 – Backend Factory & Configuration

* Implement a backend factory:

  * Read `ai-clean.toml` → `spec_backend.type`.
  * If `"butler"`:

    * Return a `ButlerSpecBackend` instance.
  * For unknown types:

    * Raise a friendly error: “Unsupported spec backend: X”.

* For v0, `butler` is the **only** supported backend.

---

## Milestone 5 – Executors (Codex + Review)

### Phase 5.1 – CodexShellExecutor: Apply Spec with Shell Wrapper

* Implement `CodexShellExecutor` as a `CodeExecutor`:

  * `apply_spec(spec_path: Path) -> ExecutionResult`:

    * Build a shell command, e.g.:

      * `bash -lc 'codex apply "<spec_path>"'`
    * Run via `subprocess`.
    * Capture:

      * Exit code,
      * stdout,
      * stderr.

  * Populate `ExecutionResult`:

    * `spec_id` from filename or parsed YAML.
    * `success` from exit code.
    * `stdout`/`stderr` from process outputs.
    * `tests_passed` to be set in next phase.
    * `git_diff` left unset for now.

* This preserves your **Codex integration** while making the spec system fully yours.

---

### Phase 5.2 – Test Runner Integration After Apply

* Extend `CodexShellExecutor`:

  * After a successful apply:

    * Run the configured tests (`tests.default_command` from config).
    * Capture exit status + logs.

  * Fill `ExecutionResult`:

    * `tests_passed = True` only if tests succeed.
    * Attach test output to stdout/stderr fields or metadata.

* If apply fails:

  * Skip tests and mark `tests_passed = False`.

---

### Phase 5.3 – ReviewExecutor: Codex-Powered Changes Review

* Implement a `ReviewExecutor` for `/changes-review`:

  * Input:

    * `CleanupPlan` (or `plan_id` to load it),
    * Associated `git diff` for the plan,
    * Latest `ExecutionResult` (apply + test info).

  * Use Codex in “review mode”:

    * Prompt: “Summarize these changes, flag risks, respect constraints.”

  * Output:

    * Review text or structured review:

      * Summary of changes,
      * Risk assessment,
      * Suggested manual checks.

* No code modifications here—review only.

---

### Phase 5.4 – Executor Factories

* Implement factories:

  * `load_executor(config) -> CodeExecutor`:

    * If `executor.type == "codex_shell"`:

      * Return `CodexShellExecutor`.

  * `load_review_executor(config) -> ReviewExecutor`:

    * If `review.type == "codex_review"`:

      * Return Codex-based review executor.

* Unsupported types → explicit, helpful errors.

---

## Milestone 6 – Git Safety & Storage Utilities

### Phase 6.1 – Plan Storage Helpers

* Implement utilities to:

  * Save `CleanupPlan` objects to `.ai-clean/plans/{plan_id}.json`.
  * Load `CleanupPlan` by `plan_id`.

* Ensure:

  * Round-tripping is lossless for required fields.

---

### Phase 6.2 – Git Branch Management

* Implement `ensure_on_refactor_branch(base_branch, refactor_branch)`:

  * If already on `refactor_branch`: do nothing.
  * Else:

    * Fetch/update `base_branch`.
    * Create/fast-forward `refactor_branch` from `base_branch`.
    * Checkout `refactor_branch`.

* No auto-commits or merges into `main`. Conflicts are surfaced to user.

---

### Phase 6.3 – Diff Stat Helper

* Implement `get_diff_stat() -> str`:

  * Uses `git diff --stat` to summarize current changes.

* Used after successful apply to show:

  * Which files changed and how much.

---

## Milestone 7 – CLI Commands

### Phase 7.1 – `/analyze` Command

* `ai-clean analyze [PATH]`:

  * Runs analyzer orchestrator.
  * Prints each `Finding`:

    * ID,
    * Category,
    * Short description,
    * Location summary.

* Read-only; no plans/specs created.

---

### Phase 7.2 – `/plan` Command

* `ai-clean plan FINDING_ID [--path PATH]`:

  * Run analyzers (or load cached findings).
  * Locate `Finding` by ID.
  * Create `CleanupPlan` via planner.
  * Save plan to `.ai-clean/plans/`.
  * Print:

    * Plan ID, title, intent, steps, constraints, tests_to_run.

---

### Phase 7.3 – `/apply` Command

* `ai-clean apply PLAN_ID`:

  * Load config and git settings.
  * Ensure we’re on `refactor_branch`.
  * Load `CleanupPlan`.
  * Use `SpecBackend` (Butler) to:

    * Build `ButlerSpec` from plan.
    * Write spec to `.ai-clean/specs/` and get `spec_path`.
  * Use `CodeExecutor` (CodexShellExecutor) to:

    * Apply spec.
    * Run tests.
  * Display:

    * Apply success/failure,
    * Tests passed/failed,
    * `git diff --stat`.

---

### Phase 7.4 – `/clean` Command (Basic Cleanup Wrapper)

* `ai-clean clean [PATH]`:

  * Run analyzers.

  * Filter findings for:

    * `duplicate_block`,
    * `large_file`,
    * `long_function`.

  * Present a list; user chooses a finding (or a few).

  * For each chosen finding:

    * Generate `CleanupPlan`.
    * Ask user whether to:

      * Only save plan, or
      * Save and immediately `/apply`.

---

### Phase 7.5 – `/annotate` Command

* `ai-clean annotate [PATH] [--mode missing|all]`:

  * Run doc analyzer.

  * Filter for `missing_docstring` (and maybe `weak_docstring` if `--mode all`).

  * Show targets; user chooses modules or “all”.

  * For each selection:

    * Generate a docstring `CleanupPlan`.
    * Offer to apply via the standard `/apply` flow.

---

### Phase 7.6 – `/organize` Command

* `ai-clean organize [PATH]`:

  * Run organize-seed analyzer.

  * Show `organize_candidate` findings.

  * User chooses candidates (each is a small group of files).

  * For each:

    * Generate a file-move `CleanupPlan`.
    * Apply or store via the same plan/spec/executor pipeline.

---

### Phase 7.7 – `/cleanup-advanced` Command

* `ai-clean cleanup-advanced [PATH]`:

  * Run advanced Codex-powered analyzer.

  * Show limited `advanced_cleanup` findings.

  * For each:

    * Generate a `CleanupPlan`.
    * Do **not** auto-apply; the user can call `/apply PLAN_ID` after review.

---

### Phase 7.8 – `/changes-review` Command

* `ai-clean changes-review PLAN_ID`:

  * Locate associated:

    * `CleanupPlan`,
    * `ButlerSpec`,
    * `ExecutionResult`,
    * `git diff` for changes.

  * Use `ReviewExecutor` (Codex) to produce a review of the change.

  * Display:

    * Summary,
    * Risks,
    * Manual QA suggestions.

---

## Milestone 8 – Global Guardrails & Limits

### Phase 8.1 – Change Size Limits

* Config + enforcement for:

  * Max files per plan (ideally **1** in v0).
  * Max changed lines per plan.

* Planners and advanced analyzer must split large changes into multiple plans when limits are exceeded.

---

### Phase 8.2 – Single Concern per Plan

* Enforce that each `CleanupPlan` addresses **one concern**:

  * One helper extraction,
  * One file split,
  * One small file group move,
  * One docstring batch for a small scope,
  * One advanced cleanup suggestion.

* This keeps each Butler spec and Codex call small and deterministic.

---

### Phase 8.3 – No Global Renames or API Overhauls in V0

* Explicit planner + prompt constraints:

  * No broad renaming of public APIs.
  * No multi-module redesigns.
  * Reject or break apart suggestions that violate this.

---

### Phase 8.4 – Test-First Execution Policy

* `/apply` must always:

  * Record whether tests ran.
  * Include test status in:

    * CLI output,
    * Stored `ExecutionResult`,
    * Any `/changes-review` output.

* Error paths:

  * Failed apply or failed tests → explicit, loud diagnostics.
