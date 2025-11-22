## 1. Deliverables

### 1.1 Configuration + Codex plumbing
- [x] Extend `ai-clean.toml` with `[analyzers.advanced]` that defines `max_files`, `max_suggestions`, `prompt_template`, `codex_model`, `temperature`, and `ignore_dirs`.
- [x] Add an `AdvancedAnalyzerConfig` dataclass to `ai_clean/config.py`, hook it into `AnalyzersConfig`, and ensure `load_config()` validates the numeric limits and loads sensible defaults.
- [x] Update `tests/test_config_loader.py` with assertions for the advanced analyzer config.
- [x] Add negative tests for zero/negative limits, missing prompt templates, and unsupported `codex_model` values so guardrails fail fast.
- [x] Create `ai_clean/interfaces/codex.py` defining a `CodexPromptRunner` Protocol (e.g., `run(prompt: str, attachments: Sequence[PromptAttachment]) -> str`) and small dataclasses describing attachments/snippets that will be sent to Codex.
- [x] Wire a `_CodexPromptRunner` placeholder + `get_codex_prompt_runner()` factory in `ai_clean/factories.py` so the analyzer can request a runner without importing Codex directly.

### 1.2 Advanced analyzer implementation
- [x] Add `ai_clean/analyzers/advanced.py` with `collect_advanced_cleanup_ideas(root: Path, existing_findings: Sequence[Finding], config: AiCleanConfig, runner: CodexPromptRunner) -> list[Finding]`.
- [x] Select candidate files/snippets by sorting the incoming findings by category/ID, picking up to `config.analyzers.advanced.max_files`, and extracting the corresponding code ranges from disk (defaulting to the entire file when ranges are missing).
- [x] Build a prompt using `config.analyzers.advanced.prompt_template.format(...)` that includes:
  - [x] A bulleted summary of the selected findings (category + description + path/range).
  - [x] Inline code snippets (trimmed to a few dozen lines) preceded by markers Codex can follow.
  - [x] The guardrail sentence “Suggest small, local cleanup changes only; no API redesigns.”
- [x] Call `runner.run(prompt, attachments)` and expect a JSON array where each suggestion has `{description, path, start_line, end_line, change_type}`; validate/decode this payload.
- [x] Convert each validated suggestion into a `Finding` with:
  - [x] `category="advanced_cleanup"` and deterministic IDs `f"adv-{sha1((path+description).encode()).hexdigest()[:8]}"`.
  - [x] Description mirroring the Codex text, `FindingLocation` spanning the suggested range, and metadata containing `change_type`, `codex_model`, and the raw Codex response blob.
- [x] Enforce guardrails by truncating to `max_suggestions`, rejecting suggestions for files outside the selected set, and logging (or emitting metadata) when truncation happens.
- [x] Log dropped suggestions with explicit reasons (e.g., disallowed change type, exceeds max files) and include a count summary in the analyzer result metadata.

### 1.3 CLI integration
- [x] Implement a helper (e.g., `ai_clean/commands/advanced_cleanup.py`) that loads existing findings from `--findings-json` (produced by `/analyze`), creates a Codex runner, and calls `collect_advanced_cleanup_ideas`.
- [x] Update the `/cleanup-advanced` CLI handler so it accepts `--root`, `--config`, and `--findings-json` arguments, invokes the helper above, and prints suggestions using the same “ID + category + locations” format as `/analyze`.
- [x] Document the workflow (run `/analyze --json` → feed into `/cleanup-advanced`) inside README.
- [x] Add README notes on non-goals (suggestions are advisory, no auto-apply) aligned with proposal guardrails.

### 1.4 Tests
- [x] Add `tests/analyzers/test_advanced_analyzer.py` that injects a fake `CodexPromptRunner` returning deterministic JSON, asserts findings are produced with capped counts, and verifies guardrails filter out disallowed paths.
- [x] Add `tests/test_cli_cleanup_advanced.py` covering the CLI flag parsing, JSON loading, and human-readable output.

## 2. Validation
- [x] Run `pytest tests/analyzers/test_advanced_analyzer.py tests/test_cli_cleanup_advanced.py tests/test_config_loader.py` to confirm the analyzer and CLI wiring behave as expected. *(Blocked in this sandbox: `pydantic`/`pytest` wheels cannot be installed due to restricted network access; see task summary.)*
