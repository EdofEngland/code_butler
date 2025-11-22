## 1. Deliverables

### 1.2.1 Dependencies and package layout
- [x] Add `pydantic>=2.6,<3` to the `[project] dependencies` list in `pyproject.toml` so models can inherit from `pydantic.BaseModel`.
- [x] Declare an optional dependency group `[project.optional-dependencies.yaml] = ["pyyaml>=6"]` and gate YAML helpers behind a runtime check so the base install stays stdlib-only.
- [x] Create `ai_clean/models/__init__.py` that re-exports every public model via `__all__` for ergonomic imports (`from ai_clean.models import CleanupPlan`).

- [x] Implement `ai_clean/models/core.py` containing the following `BaseModel` subclasses with full type annotations:
  - [ ] `FindingLocation` with fields `path: Path`, `start_line: int`, `end_line: int`.
  - [ ] `Finding` with fields `id: str`, `category: Literal["duplicate_block","large_file","missing_docstring","organize_candidate","advanced_cleanup","long_function"]`, `description: str`, `locations: list[FindingLocation]`, `metadata: dict[str, Any] = Field(default_factory=dict)`.
  - [ ] `CleanupPlan` with fields `id: str`, `finding_id: str`, `title: str`, `intent: str`, `steps: list[str]`, `constraints: list[str]`, `tests_to_run: list[str]`, `metadata: dict[str, Any] = Field(default_factory=dict)`.
  - [ ] `ButlerSpec` with fields `id: str`, `plan_id: str`, `target_file: str`, `intent: str`, `actions: list[dict[str, Any]]`, `model: str`, `batch_group: str | None = None`, `metadata: dict[str, Any] = Field(default_factory=dict)`.
  - [ ] `ExecutionResult` with fields `spec_id: str`, `plan_id: str`, `success: bool`, `tests_passed: bool | None`, `stdout: str`, `stderr: str`, `git_diff: str | None = None`, `metadata: dict[str, Any] = Field(default_factory=dict)`.

- [x] For each model add instance methods `.to_json()` and `.to_yaml()` that call `self.model_dump()` and serialize via `json.dumps` / `yaml.safe_dump` (guard YAML import with feature detection and useful error messages when the optional extra is missing).
- [x] Provide class methods `@classmethod from_json(cls, data: str)` / `from_yaml(cls, data: str)` to mirror the serialization API so future phases can persist/load specs and plans without ad-hoc code.
- [x] Include helper functions like `default_plan_path(plan_id: str)` / `default_spec_path(spec_id: str)` returning locations under `.ai-clean/plans` and `.ai-clean/specs` so later config work can reuse the same conventions.

### 1.2.4 Guardrails and verification
- [x] Add docstrings to each model pointing out that no Codex/executor logic belongs here—only pure data containers and serialization helpers.
- [x] Write a minimal test or script snippet (e.g., `examples/model_roundtrip.py`) that instantiates each model, calls `to_json()`/`from_json()`, exercises the `.ai-clean/` default path helpers, and asserts equality to ensure serialization is deterministic.
