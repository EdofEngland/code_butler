# Proposal: Add project context CLI

## Why
- Developers and AI agents currently need to open `openspec/project.md` manually to recall the project's purpose, stack, and conventions.
- A single command that summarizes this context speeds up onboarding and allows automated tooling to sync knowledge before coding.
- This foundation will also let future commands surface spec data through a consistent interface.

## What Changes
- Introduce a `code-butler project describe` CLI command that reads `openspec/project.md` and outputs a curated summary.
- Support `--format text|json` so humans get a readable synopsis while automation can parse structured output.
- Include metadata such as last modified time and any missing sections so contributors know when to update the file.

## Impact / Risks
- Adds a new runtime entry point; requires docs/tests to avoid regressions.
- No breaking API surface today, but downstream scripts may start depending on the CLI once available.
- Implementation relies on PyYAML/stdlib only; no external API calls are planned.
