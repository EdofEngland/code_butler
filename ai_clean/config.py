"""Configuration loader for ai-clean."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ai_clean.paths import (
    default_metadata_root,
    default_plan_path,
    default_result_path,
    default_spec_path,
)


@dataclass(frozen=True)
class SpecBackendConfig:
    type: str
    default_batch_group: str
    specs_dir: Path


@dataclass(frozen=True)
class ExecutorConfig:
    type: str
    binary: str
    apply_args: tuple[str, ...]
    results_dir: Path


@dataclass(frozen=True)
class ReviewConfig:
    type: str
    mode: str


@dataclass(frozen=True)
class GitConfig:
    base_branch: str
    refactor_branch: str


@dataclass(frozen=True)
class TestsConfig:
    default_command: str


@dataclass(frozen=True)
class PlanLimitsConfig:
    max_files_per_plan: int
    max_changed_lines_per_plan: int


@dataclass(frozen=True)
class DuplicateAnalyzerConfig:
    window_size: int
    min_occurrences: int
    ignore_dirs: tuple[str, ...]


@dataclass(frozen=True)
class StructureAnalyzerConfig:
    max_file_lines: int
    max_function_lines: int
    ignore_dirs: tuple[str, ...]


@dataclass(frozen=True)
class DocstringAnalyzerConfig:
    min_docstring_length: int
    min_symbol_lines: int
    weak_markers: tuple[str, ...]
    important_symbols_only: bool
    ignore_dirs: tuple[str, ...]


@dataclass(frozen=True)
class OrganizeAnalyzerConfig:
    min_group_size: int
    max_group_size: int
    max_groups: int
    ignore_dirs: tuple[str, ...]


@dataclass(frozen=True)
class AdvancedAnalyzerConfig:
    max_files: int
    max_suggestions: int
    prompt_template: str
    codex_model: str
    temperature: float
    ignore_dirs: tuple[str, ...]


@dataclass(frozen=True)
class AnalyzersConfig:
    duplicate: DuplicateAnalyzerConfig
    structure: StructureAnalyzerConfig
    docstring: DocstringAnalyzerConfig
    organize: OrganizeAnalyzerConfig
    advanced: AdvancedAnalyzerConfig


@dataclass(frozen=True)
class AiCleanConfig:
    spec_backend: SpecBackendConfig
    executor: ExecutorConfig
    review: ReviewConfig
    git: GitConfig
    tests: TestsConfig
    plan_limits: PlanLimitsConfig
    analyzers: AnalyzersConfig
    metadata_root: Path
    plans_dir: Path
    specs_dir: Path
    results_dir: Path


_DEFAULT_DUPLICATE_WINDOW_SIZE = 5
_DEFAULT_DUPLICATE_MIN_OCCURRENCES = 2
_DEFAULT_DUPLICATE_IGNORE_DIRS: tuple[str, ...] = (".git", "__pycache__", ".venv")
_DEFAULT_STRUCTURE_MAX_FILE_LINES = 400
_DEFAULT_STRUCTURE_MAX_FUNCTION_LINES = 60
_DEFAULT_DOC_MIN_LENGTH = 32
_DEFAULT_DOC_MIN_SYMBOL_LINES = 5
_DEFAULT_DOC_WEAK_MARKERS: tuple[str, ...] = ("todo", "fixme", "tbd")
_DEFAULT_DOC_IMPORTANT_ONLY = True
_DEFAULT_ORGANIZE_MIN_GROUP = 2
_DEFAULT_ORGANIZE_MAX_GROUP = 5
_DEFAULT_ORGANIZE_MAX_GROUPS = 5
_DEFAULT_ADV_MAX_FILES = 3
_DEFAULT_ADV_MAX_SUGGESTIONS = 5
_DEFAULT_ADV_PROMPT = (
    "Suggest small, local cleanup changes only; no API redesigns.\n"
    "Existing findings:\n{findings}\n\nSnippets:\n{snippets}"
)
_DEFAULT_ADV_MODEL = "gpt-4o-mini"
_DEFAULT_ADV_TEMPERATURE = 0.2
_DEFAULT_PLAN_MAX_FILES = 1
_DEFAULT_PLAN_MAX_CHANGED_LINES = 200


def _load_toml_text(text: str) -> dict[str, Any]:
    try:  # Python 3.11+
        import tomllib

        return tomllib.loads(text)
    except ModuleNotFoundError:
        return _parse_simple_toml(text)


def _parse_simple_toml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current_section = data.setdefault(section, {})
            continue
        if current_section is None:
            raise ValueError("Configuration keys must appear inside a section")
        if "=" not in line:
            raise ValueError(f"Invalid configuration line: {raw_line}")
        key, value = (part.strip() for part in line.split("=", 1))
        if value.startswith("[") and value.endswith("]"):
            entries = [
                _unescape_string(chunk.strip().strip('"'))
                for chunk in value[1:-1].split(",")
                if chunk.strip()
            ]
            current_section[key] = entries
        else:
            cleaned_value = value.strip().strip('"')
            current_section[key] = _unescape_string(cleaned_value)
    return data


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    text = path.read_text()
    return _load_toml_text(text)


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate


def load_config(path: Path | None = None) -> AiCleanConfig:
    config_path = path or Path("ai-clean.toml")
    raw = _read_toml(config_path)

    spec_backend_section = raw.get("spec_backend")
    executor_section = raw.get("executor")
    review_section = raw.get("review")
    git_section = raw.get("git")
    tests_section = raw.get("tests")
    plan_limits_section = raw.get("plan_limits", {})

    missing = [
        name
        for name, section in (
            ("spec_backend", spec_backend_section),
            ("executor", executor_section),
            ("review", review_section),
            ("git", git_section),
            ("tests", tests_section),
        )
        if section is None
    ]
    if missing:
        raise ValueError(f"Missing config sections: {', '.join(missing)}")

    metadata_section = raw.get("metadata", {})
    default_root = default_metadata_root().resolve()
    metadata_root = _resolve_path(metadata_section.get("root"), default_root)

    default_plan_dir = default_plan_path("__plan__").resolve().parent
    default_spec_dir = default_spec_path("__spec__").resolve().parent
    default_result_dir = default_result_path("__plan__").resolve().parent

    if metadata_section.get("root"):
        default_plan_dir = metadata_root / "plans"
        default_spec_dir = metadata_root / "specs"
        default_result_dir = metadata_root / "results"

    plans_dir = _resolve_path(metadata_section.get("plans_dir"), default_plan_dir)
    specs_dir = _resolve_path(metadata_section.get("specs_dir"), default_spec_dir)
    results_dir = _resolve_path(metadata_section.get("results_dir"), default_result_dir)

    spec_backend = SpecBackendConfig(
        type=spec_backend_section.get("type", "").strip(),
        default_batch_group=spec_backend_section.get("default_batch_group", "default"),
        specs_dir=specs_dir,
    )
    if spec_backend.type != "butler":
        raise ValueError(f"Unsupported spec_backend.type: {spec_backend.type}")

    executor = ExecutorConfig(
        type=executor_section.get("type", "").strip(),
        binary=executor_section.get("binary", "codex"),
        apply_args=tuple(executor_section.get("apply_args", ["apply"])),
        results_dir=results_dir,
    )
    if executor.type not in {"manual", "codex_shell"}:
        raise ValueError(f"Unsupported executor.type: {executor.type}")

    review = ReviewConfig(
        type=review_section.get("type", "").strip(),
        mode=review_section.get("mode", ""),
    )
    if review.type != "codex_review":
        raise ValueError(f"Unsupported review.type: {review.type}")

    git = GitConfig(
        base_branch=git_section.get("base_branch", ""),
        refactor_branch=git_section.get("refactor_branch", ""),
    )
    tests = TestsConfig(default_command=tests_section.get("default_command", ""))

    max_files_per_plan = _coerce_int(
        plan_limits_section.get("max_files_per_plan"),
        default=_DEFAULT_PLAN_MAX_FILES,
        field_name="max_files_per_plan",
        context="Plan limits",
    )
    if max_files_per_plan < 1:
        raise ValueError("Plan limits max_files_per_plan must be at least 1")

    max_changed_lines_per_plan = _coerce_int(
        plan_limits_section.get("max_changed_lines_per_plan"),
        default=_DEFAULT_PLAN_MAX_CHANGED_LINES,
        field_name="max_changed_lines_per_plan",
        context="Plan limits",
    )
    if max_changed_lines_per_plan < 1:
        raise ValueError("Plan limits max_changed_lines_per_plan must be at least 1")

    plan_limits = PlanLimitsConfig(
        max_files_per_plan=max_files_per_plan,
        max_changed_lines_per_plan=max_changed_lines_per_plan,
    )

    duplicate_section = _extract_section(raw, "analyzers", "duplicate")

    window_size = _coerce_int(
        duplicate_section.get("window_size"),
        default=_DEFAULT_DUPLICATE_WINDOW_SIZE,
        field_name="window_size",
        context="Duplicate analyzer",
    )
    if window_size <= 0:
        raise ValueError("Duplicate analyzer window_size must be greater than 0")

    min_occurrences = _coerce_int(
        duplicate_section.get("min_occurrences"),
        default=_DEFAULT_DUPLICATE_MIN_OCCURRENCES,
        field_name="min_occurrences",
        context="Duplicate analyzer",
    )
    if min_occurrences <= 1:
        raise ValueError("Duplicate analyzer min_occurrences must be greater than 1")

    ignore_dirs_raw = duplicate_section.get("ignore_dirs")
    if ignore_dirs_raw is None:
        ignore_dirs = _DEFAULT_DUPLICATE_IGNORE_DIRS
    else:
        ignore_dirs = _normalize_ignore_dirs(ignore_dirs_raw)

    structure_section = _extract_section(raw, "analyzers", "structure")

    max_file_lines = _coerce_int(
        structure_section.get("max_file_lines"),
        default=_DEFAULT_STRUCTURE_MAX_FILE_LINES,
        field_name="max_file_lines",
        context="Structure analyzer",
    )
    if max_file_lines <= 0:
        raise ValueError("Structure analyzer max_file_lines must be greater than 0")

    max_function_lines = _coerce_int(
        structure_section.get("max_function_lines"),
        default=_DEFAULT_STRUCTURE_MAX_FUNCTION_LINES,
        field_name="max_function_lines",
        context="Structure analyzer",
    )
    if max_function_lines <= 0:
        raise ValueError("Structure analyzer max_function_lines must be greater than 0")

    structure_ignore_dirs = _merge_ignore_dirs(structure_section.get("ignore_dirs"))

    doc_section = _extract_section(raw, "analyzers", "docstring")

    min_docstring_length = _coerce_int(
        doc_section.get("min_docstring_length"),
        default=_DEFAULT_DOC_MIN_LENGTH,
        field_name="min_docstring_length",
        context="Docstring analyzer",
    )
    if min_docstring_length <= 0:
        raise ValueError(
            "Docstring analyzer min_docstring_length must be greater than 0"
        )

    min_symbol_lines = _coerce_int(
        doc_section.get("min_symbol_lines"),
        default=_DEFAULT_DOC_MIN_SYMBOL_LINES,
        field_name="min_symbol_lines",
        context="Docstring analyzer",
    )
    if min_symbol_lines <= 0:
        raise ValueError("Docstring analyzer min_symbol_lines must be greater than 0")

    weak_markers_raw = doc_section.get("weak_markers")
    if weak_markers_raw is None:
        weak_markers = _DEFAULT_DOC_WEAK_MARKERS
    else:
        weak_markers = _normalize_string_list(
            weak_markers_raw,
            field_name="weak_markers",
            lower=True,
        )
        if not weak_markers:
            raise ValueError(
                "Docstring analyzer weak_markers must include at least one entry"
            )

    important_symbols_only = _coerce_bool(
        doc_section.get("important_symbols_only"),
        default=_DEFAULT_DOC_IMPORTANT_ONLY,
        field_name="important_symbols_only",
        context="Docstring analyzer",
    )

    doc_ignore_dirs = _merge_ignore_dirs(doc_section.get("ignore_dirs"))

    organize_section = _extract_section(raw, "analyzers", "organize")

    min_group_size = _coerce_int(
        organize_section.get("min_group_size"),
        default=_DEFAULT_ORGANIZE_MIN_GROUP,
        field_name="min_group_size",
        context="Organize analyzer",
    )
    if min_group_size < 2:
        raise ValueError("Organize analyzer min_group_size must be at least 2")

    max_group_size = _coerce_int(
        organize_section.get("max_group_size"),
        default=_DEFAULT_ORGANIZE_MAX_GROUP,
        field_name="max_group_size",
        context="Organize analyzer",
    )
    if max_group_size < min_group_size or max_group_size > 5:
        raise ValueError(
            "Organize analyzer max_group_size must be between min_group_size and 5"
        )

    max_groups = _coerce_int(
        organize_section.get("max_groups"),
        default=_DEFAULT_ORGANIZE_MAX_GROUPS,
        field_name="max_groups",
        context="Organize analyzer",
    )
    if max_groups < 1:
        raise ValueError("Organize analyzer max_groups must be at least 1")

    organize_ignore_dirs = _merge_ignore_dirs(organize_section.get("ignore_dirs"))

    advanced_section = _extract_section(raw, "analyzers", "advanced")

    max_files = _coerce_int(
        advanced_section.get("max_files"),
        default=_DEFAULT_ADV_MAX_FILES,
        field_name="max_files",
        context="Advanced analyzer",
    )
    if max_files <= 0:
        raise ValueError("Advanced analyzer max_files must be greater than 0")

    max_suggestions = _coerce_int(
        advanced_section.get("max_suggestions"),
        default=_DEFAULT_ADV_MAX_SUGGESTIONS,
        field_name="max_suggestions",
        context="Advanced analyzer",
    )
    if max_suggestions <= 0:
        raise ValueError("Advanced analyzer max_suggestions must be greater than 0")

    prompt_template = advanced_section.get(
        "prompt_template", _DEFAULT_ADV_PROMPT
    ).strip()
    if not prompt_template:
        raise ValueError("Advanced analyzer prompt_template must be provided")

    codex_model = advanced_section.get("codex_model", _DEFAULT_ADV_MODEL).strip()
    if not codex_model:
        raise ValueError("Advanced analyzer codex_model must be provided")

    temperature = _coerce_float(
        advanced_section.get("temperature"),
        default=_DEFAULT_ADV_TEMPERATURE,
        field_name="temperature",
        context="Advanced analyzer",
    )
    if temperature <= 0:
        raise ValueError("Advanced analyzer temperature must be greater than 0")

    advanced_ignore_dirs = _merge_ignore_dirs(advanced_section.get("ignore_dirs"))

    analyzers = AnalyzersConfig(
        duplicate=DuplicateAnalyzerConfig(
            window_size=window_size,
            min_occurrences=min_occurrences,
            ignore_dirs=ignore_dirs,
        ),
        structure=StructureAnalyzerConfig(
            max_file_lines=max_file_lines,
            max_function_lines=max_function_lines,
            ignore_dirs=structure_ignore_dirs,
        ),
        docstring=DocstringAnalyzerConfig(
            min_docstring_length=min_docstring_length,
            min_symbol_lines=min_symbol_lines,
            weak_markers=weak_markers,
            important_symbols_only=important_symbols_only,
            ignore_dirs=doc_ignore_dirs,
        ),
        organize=OrganizeAnalyzerConfig(
            min_group_size=min_group_size,
            max_group_size=max_group_size,
            max_groups=max_groups,
            ignore_dirs=organize_ignore_dirs,
        ),
        advanced=AdvancedAnalyzerConfig(
            max_files=max_files,
            max_suggestions=max_suggestions,
            prompt_template=prompt_template,
            codex_model=codex_model,
            temperature=temperature,
            ignore_dirs=advanced_ignore_dirs,
        ),
    )

    return AiCleanConfig(
        spec_backend=spec_backend,
        executor=executor,
        review=review,
        git=git,
        tests=tests,
        plan_limits=plan_limits,
        analyzers=analyzers,
        metadata_root=metadata_root,
        plans_dir=plans_dir,
        specs_dir=specs_dir,
        results_dir=results_dir,
    )


def _extract_section(raw: dict[str, Any], *path: str) -> dict[str, Any]:
    if not path:
        return {}
    dotted_key = ".".join(path)
    dotted_section = raw.get(dotted_key)
    if isinstance(dotted_section, dict):
        return dotted_section

    section: Any = raw
    for key in path:
        if not isinstance(section, dict):
            return {}
        section = section.get(key)
        if section is None:
            return {}
    return section if isinstance(section, dict) else {}


def _normalize_ignore_dirs(value: Any) -> tuple[str, ...]:
    entries: Iterable[str]
    if isinstance(value, str):
        entries = [value]
    elif isinstance(value, Iterable):
        entries = value
    else:  # pragma: no cover - defensive
        raise ValueError("Duplicate analyzer ignore_dirs must be strings")

    normalized: list[str] = []
    for raw_entry in entries:
        if not isinstance(raw_entry, str):  # pragma: no cover - defensive
            raise ValueError("Duplicate analyzer ignore_dirs must be strings")
        entry = raw_entry.strip()
        if not entry:
            raise ValueError(
                "Duplicate analyzer ignore_dirs entries must be non-empty strings"
            )
        normalized_name = Path(entry).name or entry
        normalized.append(normalized_name)

    deduped = tuple(dict.fromkeys(normalized))
    if not deduped:
        raise ValueError(
            "Duplicate analyzer ignore_dirs entries must be non-empty strings"
        )
    return deduped


def _merge_ignore_dirs(value: Any) -> tuple[str, ...]:
    extras = _normalize_ignore_dirs(value) if value is not None else ()
    merged = tuple(dict.fromkeys(_DEFAULT_DUPLICATE_IGNORE_DIRS + extras))
    return merged


def _coerce_int(value: Any, *, default: int, field_name: str, context: str) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{context} {field_name} must be an integer") from exc


def _coerce_bool(value: Any, *, default: bool, field_name: str, context: str) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValueError(f"{context} {field_name} must be a boolean value")


def _normalize_string_list(
    value: Any, *, field_name: str, lower: bool = False
) -> tuple[str, ...]:
    entries: Iterable[str]
    if isinstance(value, str):
        entries = [value]
    elif isinstance(value, Iterable):
        entries = value
    else:  # pragma: no cover - defensive
        raise ValueError(f"Docstring analyzer {field_name} must be strings")

    normalized: list[str] = []
    for raw_entry in entries:
        if not isinstance(raw_entry, str):  # pragma: no cover - defensive
            raise ValueError(f"Docstring analyzer {field_name} must be strings")
        entry = raw_entry.strip()
        if not entry:
            raise ValueError(
                f"Docstring analyzer {field_name} entries must be non-empty strings"
            )
        normalized.append(entry.lower() if lower else entry)

    return tuple(dict.fromkeys(normalized))


def _coerce_float(
    value: Any, *, default: float, field_name: str, context: str
) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{context} {field_name} must be a number") from exc


def _unescape_string(value: str) -> str:
    if not value:
        return value
    # Preserve Windows paths (avoid interpreting \U) while supporting common escapes.
    value = value.replace("\\r\\n", "\r\n")
    value = value.replace("\\n", "\n")
    value = value.replace("\\r", "\r")
    value = value.replace("\\t", "\t")
    return value


__all__ = [
    "AnalyzersConfig",
    "AiCleanConfig",
    "DuplicateAnalyzerConfig",
    "DocstringAnalyzerConfig",
    "AdvancedAnalyzerConfig",
    "OrganizeAnalyzerConfig",
    "StructureAnalyzerConfig",
    "ExecutorConfig",
    "GitConfig",
    "ReviewConfig",
    "SpecBackendConfig",
    "TestsConfig",
    "PlanLimitsConfig",
    "load_config",
]
