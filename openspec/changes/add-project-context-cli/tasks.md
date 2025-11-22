## 1. Planning & Design
- [ ] 1.1 Confirm `openspec/project.md` structure and fields to surface.
- [ ] 1.2 Align output schema for `--format json` (keys, casing, optional fields).

## 2. Implementation
- [ ] 2.1 Scaffold the `code-butler` CLI entry point (likely via `python -m code_butler`).
- [ ] 2.2 Implement the `project describe` subcommand that loads markdown and produces structured data.
- [ ] 2.3 Add option parsing for `--format` plus pretty text rendering with section headings.

## 3. Quality
- [ ] 3.1 Add pytest coverage for both JSON/text output modes with fixture project files.
- [ ] 3.2 Document the command in README and ensure `openspec/project.md` stays single source of truth.
- [ ] 3.3 Run pre-commit hooks and `openspec validate add-project-context-cli --strict` before requesting review.
