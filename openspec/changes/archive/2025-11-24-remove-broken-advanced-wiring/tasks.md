## 1. Implementation
- [x] 1.1 Disable Codex-dependent advanced analyzer path
  - [x] 1.1.1 Remove or short-circuit the advanced analyzer CLI path so it fails fast with a clear “Codex integration unavailable” message.
  - [x] 1.1.2 Remove/guard the Codex prompt runner wiring for advanced analyzer so no stub Codex calls run.
- [x] 1.2 Config/docs/tests
  - [x] 1.2.1 Update config defaults/help text to mark advanced analyzer as disabled.
  - [x] 1.2.2 Adjust docs to state the advanced analyzer requires a Codex slash command and is currently disabled.
  - [x] 1.2.3 Update or skip tests that assumed Codex-backed advanced analyzer output.

## 2. Validation
- [x] 2.1 CLI behavior
  - [x] 2.1.1 Confirm `ai-clean cleanup-advanced` exits with the explicit “Codex unavailable” error.
- [x] 2.2 Docs/config
  - [x] 2.2.1 Verify README/help text no longer claim Codex-backed execution is available.
