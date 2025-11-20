## MODIFIED Requirements
### Requirement: Phase 5.1 Code Executor Applies Spec
The executor MUST call `/prompts:openspec-apply {spec_path}` when running inside Codex and MUST explain how contributors can override the command or enable the stub when `/prompts:openspec-apply` is unavailable locally.

#### Scenario: Codex runs use prompts apply command
- **GIVEN** `ai-clean apply` runs inside the Codex CLI
- **WHEN** the executor invokes the apply command
- **THEN** it shells out to `/prompts:openspec-apply {spec_path}` so the OpenSpec change file produced by ai-clean is applied

#### Scenario: Local runs document override path
- **GIVEN** a contributor runs ai-clean outside Codex
- **WHEN** `/prompts:openspec-apply` is unavailable
- **THEN** the documentation explains how to set `AI_CLEAN_APPLY_COMMAND` or `AI_CLEAN_USE_APPLY_STUB=1` so the pipeline still runs end-to-end
