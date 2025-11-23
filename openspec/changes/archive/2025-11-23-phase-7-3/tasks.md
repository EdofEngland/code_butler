## 1. CLI wiring and inputs

- [x] 1.1 Add `ai-clean apply PLAN_ID` command that requires exactly one plan ID; reject missing or extra args with a clear error + non-zero exit.
- [x] 1.2 Load configuration and git settings deterministically at the start (no prompts).

## 2. Git safety

- [x] 2.1 Invoke `ensure_on_refactor_branch(config.git.base_branch, config.git.refactor_branch)` before any writes; propagate failures.
- [x] 2.2 Keep repo unchanged otherwise: no commits/merges/pushes; deterministic working directory.

## 3. Plan and spec materialization

- [x] 3.1 Load the `CleanupPlan` via `load_plan(plan_id)` (or equivalent backend helper); fail fast on missing file with descriptive copy.
- [x] 3.2 Use `SpecBackend.plan_to_spec(plan)` to build a `ButlerSpec` and write it to `.ai-clean/specs/{spec.id}.butler.yaml`, echoing the path used.

## 4. Apply and test execution

- [x] 4.1 Call `CodeExecutor.apply_spec(spec_path)` exactly once per run; do not batch or parallelize.
- [x] 4.2 Respect executor outputs: capture success flag, stdout/stderr, tests_passed state (including skipped), and metadata/exit codes without mutation.

## 5. Reporting and git diff summary

- [x] 5.1 After apply/tests, run `get_diff_stat()` and include its output in the user-facing summary.
- [x] 5.2 Print a deterministic summary that includes: spec path, apply success/failure, tests_passed state (or skipped reason), and git diff stat; keep messages ASCII-safe.

## 6. Failure handling and exits

- [x] 6.1 If plan load, spec build/write, apply, tests, or git helpers fail, exit non-zero with concise error messages; skip tests when apply fails.
- [x] 6.2 Do not hide executor stderr/stdout; surface them (possibly truncated) so users can act.

## 7. Non-goals and constraints

- [x] 7.1 No interactive prompts, no batch apply, and no speculative retries; the command runs once per plan ID with deterministic side effects.
