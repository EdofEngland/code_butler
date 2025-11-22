## 1. Deliverables

### 1.3.1 Interface package structure
- [x] Create `ai_clean/interfaces/__init__.py` that exposes `SpecBackend`, `CodeExecutor`, `ReviewExecutor`, and `BatchRunner` via `__all__`.
- [x] Add `ai_clean/interfaces/types.py` to hold shared aliases such as `StructuredReview = dict[str, Any] | str` to keep import cycles minimal.

### 1.3.2 SpecBackend interface
- [x] Implement `ai_clean/interfaces/spec_backend.py` defining `class SpecBackend(Protocol)` (use `typing.Protocol`) with methods:
  - [x] `plan_to_spec(self, plan: CleanupPlan) -> ButlerSpec` with docstring referencing ButlerSpec guardrails.
  - [x] `write_spec(self, spec: ButlerSpec, directory: Path) -> Path` returning the written file path.
- [x] Include a concrete `NotImplementedError` fallback mixin `class BaseSpecBackend(ABC)` for backends preferring inheritance over Protocols.

### 1.3.3 Executors
- [x] Implement `ai_clean/interfaces/executor.py` defining:
  - [x] `class CodeExecutor(Protocol)` with `apply_spec(self, spec_path: Path) -> ExecutionResult`.
  - [x] `class BatchRunner(Protocol)` with `apply_batch(self, spec_dir: Path, batch_group: str) -> list[ExecutionResult]`.
  - [x] `class ReviewExecutor(Protocol)` with `review_change(self, plan: CleanupPlan, diff: str, exec_result: ExecutionResult) -> StructuredReview`.
- [x] Add dataclass `ReviewContext` encapsulating `plan`, `diff`, and `exec_result` so downstream implementations can accept a single argument if preferred.

### 1.3.4 Documentation + guardrails
- [x] Add module-level docstrings explicitly stating “Do not import Codex or ButlerSpec backends here—interfaces stay dependency free.”
- [x] Include type-check-only imports (`if TYPE_CHECKING`) of models to avoid runtime circular imports.
- [x] Provide `examples/interfaces_usage.py` demonstrating how a stub backend/executor would implement each Protocol, persist specs via the default path helpers from Phase 1.2, and log `ExecutionResult` objects so future contributors have a deterministic reference.
- [x] Reference the "Phase 1 System Sketch" in example docstrings to reinforce the hand-offs between CLI commands, SpecBackend, and executors.
