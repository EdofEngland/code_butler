# /butler-exec — Execute a ButlerSpec

Purpose: run a single ButlerSpec file with strict guardrails; never replan or modify other files.

Invocation: `codex /butler-exec <SPEC_PATH>`
- Arguments: `<SPEC_PATH>` MUST be a single ButlerSpec path (`*.butler.yaml`). Prefer an absolute path; relative paths must be resolved from the repo root that contains the target file.
- Auth/environment: handled by Codex CLI. Do not request credentials; do not open browsers.

Execution steps:
1) Read the ButlerSpec YAML from `<SPEC_PATH>`. If the file is missing or unreadable, respond with `Error: spec file not found or unreadable` and stop immediately. Do NOT search for other specs, scan the repo, or apply any actions when the requested file is absent.
2) Validate guardrails before applying:
   - Spec MUST declare exactly one `target_file` and no conflicting targets.
   - Spec MUST have `actions` length between 1 and 25.
   - Reject if metadata exceeds limits or the spec requests renames/signature changes/structural redesigns not explicitly described in the actions.
   - If any guardrail fails, respond with `Error: <reason>` and do not emit a diff or tests block.
3) Summarize the intent and actions (count + short bullet summaries) to anchor the edit.
4) Apply only the specified actions to the `target_file`. Do NOT touch other files or lines outside the action ranges. No speculative edits, no formatting sweeps, no new files, no code fences.
5) Tests: if `metadata.tests_to_run` contains a command, run it from the spec directory after applying changes and capture stdout/stderr/exit_code. If no test command is present, set status to `not_run` with reason `no_test_command`.

Output contract (exact shape):
- On success:
  ```
  Summary: <1–2 lines: intent, target_file, actions count>
  Diff:
  <unified diff against target_file only, no extra text, no code fences>
  Tests:
  status=<ran|failed|not_run|timed_out|command_not_found|apply_failed>; command=<test command or none>; exit_code=<int or none>; stdout=<trimmed stdout or empty>; stderr=<trimmed stderr or empty>
  ```
  - Diff MUST be unified format and only include edits described by the actions. If no changes would be produced, respond with `Error: no diff produced`.
- On guardrail failure (invalid spec, missing file, multi-target, >25 actions, forbidden rename/signature/structural change, etc.): respond with `Error: <reason>` only. Do NOT include `Diff:` or `Tests:` sections.

Notes:
- Never rewrite the spec file. Never batch multiple specs. Always keep edits confined to the declared target file.
- Keep responses terse. If tests are skipped/not run, still emit the `Tests:` line with `status=not_run` and a reason.

Sample sanity check (expected shape):
```
Summary: Update docstring wording in foo.py (1 action)
Diff:
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@
-def hello():
-    """hi"""
+def hello():
+    """Say hello to the user."""
Tests:
status=not_run; command=none; exit_code=none; stdout=; stderr=
```
If the spec is invalid or unreadable, return `Error: <reason>` instead of the above sections.
