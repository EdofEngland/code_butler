# Project Context

## Purpose
Code Butler is a lightweight Python 3.11 toolkit for building AI-assisted developer automation. The repository primarily hosts OpenSpec-managed specs, proposals, and supporting tooling so every change is planned and reviewed before implementation.

## Tech Stack
- Python 3.11 managed via `pyproject.toml`
- Tooling: Black, Isort, Ruff, and Pre-commit hooks for quality gates
- PyYAML for parsing/writing structured configuration and spec data

## Project Conventions

### Code Style
- Format with Black (line length 88) and manage imports with Isort; Ruff enforces pycodestyle/pyflakes checks.
- Favor small, single-purpose modules with clear docstrings and type hints when public APIs are exposed.
- Keep new features under ~100 LOC when possible and avoid unnecessary abstractions per OpenSpec best practices.

### Architecture Patterns
- Specs define behavior: each capability is captured under `openspec/specs/<capability>/spec.md` and all work flows from these requirements.
- Proposals live in `openspec/changes/<change-id>/` with `proposal.md`, `tasks.md`, and spec deltas to isolate concurrent work.
- Runtime code should stay modular (pure functions or thin CLI/automation wrappers) so AI agents can reason about it quickly.

### Testing Strategy
- Default to pytest-based unit tests for any executable code; keep tests deterministic with fixtures/mocks for external services.
- Validate spec deltas with `openspec validate <change-id> --strict` before sharing proposals or marking changes complete.
- Require CI (or local equivalent) to run linting plus tests before merging.

### Git Workflow
- Use verb-led OpenSpec `change-id`s to name branches; do not start coding until the proposal is reviewed.
- Keep commits scoped to a single task from `tasks.md`; re-run pre-commit hooks prior to pushing.
- Merge changes only after specs and tasks are fully checked off to keep repository and documentation in sync.

## Domain Context
Focus is on "code butler" developer tooling—automation helpers and integrations that streamline coding workflows for AI and human developers. The repo currently acts as the planning surface for upcoming automation features.

## Important Constraints
- Favor boring, well-understood libraries; new dependencies need justification.
- Optimize for maintainability and transparency so AI assistants can follow the reasoning trail.
- Respect OpenSpec's stage gates: proposal → approval → implementation → archive.

## External Dependencies
- PyYAML for handling YAML-based specs/configs.
- Pre-commit-managed tooling (`black`, `isort`, `ruff`) for code formatting and linting.
