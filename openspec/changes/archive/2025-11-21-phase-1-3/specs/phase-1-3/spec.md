## ADDED Requirements

### Requirement: Interface modules export stable APIs
The `ai_clean.interfaces` package MUST expose all Protocols through a documented `__all__` to keep imports consistent.

#### Scenario: Package exports resolve
- **WHEN** `from ai_clean.interfaces import SpecBackend, CodeExecutor, ReviewExecutor, BatchRunner` is executed
- **THEN** the imports succeed without touching Codex-specific code.

### Requirement: SpecBackend contract documented
Spec conversion MUST be defined via both a typing.Protocol and a fallback abstract base class.

#### Scenario: SpecBackend enforces guardrails
- **WHEN** developers inspect `ai_clean/interfaces/spec_backend.py`
- **THEN** they see `class SpecBackend(Protocol)` with `plan_to_spec` and `write_spec` signatures referencing `CleanupPlan`/`ButlerSpec`
- **AND** `BaseSpecBackend` raises `NotImplementedError` for unimplemented methods
- **AND** module docstrings state that Codex integrations belong in concrete implementations.

### Requirement: Executor contracts defined
Executors MUST offer single-plan, batch, and review surfaces with shared context helpers.

#### Scenario: Executors share ReviewContext
- **WHEN** `ai_clean/interfaces/executor.py` is executed under type checking
- **THEN** it defines Protocols for `CodeExecutor`, `BatchRunner`, and `ReviewExecutor`
- **AND** provides a `ReviewContext` dataclass bundling `plan`, `diff`, and `ExecutionResult`.

### Requirement: Guardrail documentation + TYPE_CHECKING imports
Interface modules MUST avoid runtime imports of heavy dependencies while still providing type hints.

#### Scenario: Dependency-free runtime confirmed
- **WHEN** `python -m compileall ai_clean/interfaces`
- **THEN** the modules compile without requiring Codex packages
- **AND** type-only imports for `CleanupPlan`, `ButlerSpec`, and `ExecutionResult` live inside `if TYPE_CHECKING` blocks.

### Requirement: Example demonstrates the pipeline
Contributors MUST have a deterministic reference for implementing custom backends per the Phase 1 system sketch.

#### Scenario: interfaces_usage example persists specs/results
- **WHEN** `examples/interfaces_usage.py` is run
- **THEN** it instantiates stub implementations of every Protocol, writes a ButlerSpec into `.ai-clean/specs/` via the default path helpers, and records a synthetic `ExecutionResult`
- **AND** docstrings mention the `docs/butlerspec_plan.md#phase-1-system-sketch` flow.
