## 1. Inputs and loading

- [x] 1.1 Update `_CodexReviewExecutor.review_change` (ai_clean/factories.py) to accept a `CleanupPlan` instance; if only `plan_id` is provided, load it from `metadata_root/plans/{plan_id}.json` (error if missing).
- [x] 1.2 Require the caller to pass the plan’s explicit `git diff` text (no implicit git calls); if empty, record “no code changes” in the review payload.
- [x] 1.3 Require the latest `ExecutionResult` (apply + tests) and validate it contains `spec_id`, `plan_id`, `success`, and `tests_passed`; fail fast with a descriptive error when absent.

## 2. Prompt construction (review mode)

- [x] 2.1 Build a deterministic prompt string inside `_CodexReviewExecutor` using config.review.mode (e.g., “summarize”), the fixed instruction: “Summarize these changes, flag risks, and ensure plan constraints are respected. Provide advisory notes only. Do NOT propose or apply code modifications.”
- [x] 2.2 Attach structured context: plan intent/constraints/target file, the provided diff text, and ExecutionResult summary (success/tests_passed/stdout+stderr snippets) in a fixed order/labels to minimize tokens.
- [x] 2.3 Keep prompt wording static across runs (no chaining, no retries with altered text) and log/return the exact prompt for debugging.

## 3. Invoke Codex

- [x] 3.1 Wire `_CodexReviewExecutor` to use a Codex invocation path (reuse `_CodexPromptRunner` stub or shell out with `subprocess.run`), ensuring exactly one call per review and deterministic arguments.
- [x] 3.2 Capture Codex stdout/stderr/exit status; treat non-zero exit or malformed response as a review failure with a clear error message and no retries.

## 4. Parse and return review output

- [x] 4.1 Normalize Codex output into a `StructuredReview` dict with keys: `summary`, `risk_grade`, `manual_checks` (list), and optional `constraints` notes; fall back to plain text if parsing fails but mark it in metadata.
- [x] 4.2 Ensure the review contains advisory-only content (no code snippets/patches); reject or redact outputs that include apply instructions.
- [x] 4.3 Add metadata entries showing prompt, attachments (plan/diff/result), and Codex exit code for traceability.

## 5. Guardrails and non-goals

- [x] 5.1 Enforce review-only behavior: do not write to repo/spec files; do not suggest API redesigns or scope expansion beyond the provided plan/diff.
- [x] 5.2 Restrict to single-plan context; reject batches or mixed diffs.
- [x] 5.3 Document error handling paths (missing inputs, Codex failures, parsing failures) so orchestrators can branch deterministically.
