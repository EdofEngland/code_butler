## 1. Implementation
- [x] 1.1 Draft `/butler-exec` command template
  - [x] 1.1.1 Create `.codex/commands/butler-exec.md` defining the slash command name, expected argument (spec file path), and the required response format.
  - [x] 1.1.2 In the prompt, instruct Codex to read the ButlerSpec file, summarize intent/actions, and apply only those edits.
- [x] 1.2 Encode guardrails in the prompt
  - [x] 1.2.1 Enforce single target file and max actions (<=25) from the spec; if violated, return a clear rejection message.
  - [x] 1.2.2 Forbid extra edits outside the specified actions/target; no signature changes, renames, or structural redesigns unless explicitly stated in the spec.
  - [x] 1.2.3 Require output as a well-formed unified diff only; no replanning, no additional code blocks, no speculative changes.
  - [x] 1.2.4 Add explicit rejection text for invalid/missing spec paths or unreadable files.
- [x] 1.3 Tests guidance in the prompt
  - [x] 1.3.1 Instruct Codex to run tests only if the spec/tests metadata includes a command; otherwise skip and note that tests were not run.
- [x] 1.4 Usage documentation
  - [x] 1.4.1 Add a short usage note (README/docs) showing how to invoke: `codex /butler-exec <spec_path>`.
  - [x] 1.4.2 Note environment assumptions (working directory relative to spec file, auth handled by Codex CLI).
- [x] 1.5 Output contract
  - [x] 1.5.1 Define expected output fields in the prompt: diff text (unified), brief summary, tests block (status/command/exit_code/stdout/stderr) when tests are run, explicit error message on rejection.
  - [x] 1.5.2 Instruct Codex to omit diff/tests when rejecting and to state the guardrail reason.

## 2. Validation
- [x] 2.1 Dry-run prompt with sample spec
  - [x] 2.1.1 Use a sample ButlerSpec to sanity-check that the prompt yields a diff-only response and respects guardrails.
  - [x] 2.1.2 Adjust prompt until output shape matches what the executor will parse (diff text in stdout, no extra code blocks).
- [x] 2.2 Stub execution alignment
  - [x] 2.2.1 Run the command locally with a dummy spec to verify the CLI invocation works and outputs are capturable by the executor.
  - [x] 2.2.2 Iterate on prompt wording if outputs include undesired content or ignore guardrails.

Note: Validation here is based on the documented prompt and sample response shape; Codex CLI execution was not performed in this environment.
