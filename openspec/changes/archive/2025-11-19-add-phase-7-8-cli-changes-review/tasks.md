## 1. Implementation
- [x] 1.1 Fetch plan, diff, and execution results for the given plan id.
  - [x] 1.1.1 Extend the CLI with `ai-clean changes-review PLAN_ID` accepting optional `--diff-command`.
  - [x] 1.1.2 Load the plan via `load_plan`, read the latest execution result from `.ai-clean/executions/{plan_id}.json`, and gather the git diff with `git diff --stat && git diff` (or cached output saved by apply).
- [x] 1.2 Invoke review executor with relevant context.
  - [x] 1.2.1 Instantiate the review executor using `build_review_executor(config, codex_completion=...)` (injecting the configured completion callback).
  - [x] 1.2.2 Call `review_change(plan, diff_text, execution_result)` and handle failures by surfacing descriptive errors.
- [x] 1.3 Render summary, risks, and manual checks to the CLI.
  - [x] 1.3.1 Format the returned structure into readable sections (Summary/Risks/Suggested checks) and include any metadata like prompt references when `--verbose` is set.
  - [x] 1.3.2 Add tests mocking the review executor to verify that missing execution results prompt helpful errors and that CLI output includes all required sections.
