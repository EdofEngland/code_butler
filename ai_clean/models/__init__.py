"""Re-export core ai-clean models and helpers.

These data containers intentionally avoid executor logic. They exist solely to
describe ButlerSpec-friendly plans, specs, and execution results.
"""

from ai_clean.paths import (
    default_metadata_root,
    default_plan_path,
    default_result_path,
    default_spec_path,
)

from .core import (
    ButlerSpec,
    CleanupPlan,
    ExecutionResult,
    Finding,
    FindingLocation,
    yaml_available,
)

__all__ = [
    "ButlerSpec",
    "CleanupPlan",
    "ExecutionResult",
    "Finding",
    "FindingLocation",
    "default_metadata_root",
    "default_plan_path",
    "default_result_path",
    "default_spec_path",
    "yaml_available",
]
