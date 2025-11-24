## Why
Advanced analyzer flows still assume direct Codex invocation, but Codex cannot be called from ai-clean. The current wiring yields stub/no-op results and misleading CLI behavior.

## What Changes
- Disable or remove the Codex-backed advanced analyzer entry point (CLI command, prompt runner wiring) so it fails fast instead of pretending to run Codex.
- Update configuration/docs/tests to reflect that advanced analyzer is unavailable until a Codex slash command exists.
- Leave other analyzers and apply/review flows untouched.

## Impact
- Reduces confusion by making the advanced analyzer explicitly unavailable.
- No spec/apply changes; this is a guardrail/UX adjustment.
