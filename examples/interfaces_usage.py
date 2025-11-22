"""Example implementations for ai-clean interfaces.

This mirrors the `/plan → spec → apply` hand-off described in
`docs/butlerspec_plan.md#phase-1-system-sketch` so contributors can quickly see
how data flows between planners, spec backends, and executors.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ai_clean.interfaces import (
    BaseSpecBackend,
    CodeExecutor,
    ReviewContext,
    StructuredReview,
)
from ai_clean.models import (
    ButlerSpec,
    CleanupPlan,
    ExecutionResult,
    default_result_path,
    default_spec_path,
)


class FileSpecBackend(BaseSpecBackend):
    """Writes specs to the default `.ai-clean/specs` directory using YAML."""

    def plan_to_spec(self, plan: CleanupPlan) -> ButlerSpec:
        return ButlerSpec(
            id=f"spec-{plan.id}",
            plan_id=plan.id,
            target_file=plan.metadata.get("target_file", "unknown"),
            intent=plan.intent,
            actions=[{"type": "todo", "description": plan.intent}],
            model="gpt-4o-mini",
            batch_group="default",
        )

    def write_spec(self, spec: ButlerSpec, directory: Path) -> Path:
        spec_path = default_spec_path(spec.id)
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(spec.to_yaml())
        return spec_path


class PrintExecutor:
    """Pretend executor implementing CodeExecutor."""

    def apply_spec(self, spec_path: Path) -> ExecutionResult:
        print(f"Applying spec at {spec_path}")
        spec_id = spec_path.name.removesuffix(".butler.yaml")
        return ExecutionResult(
            spec_id=spec_id,
            plan_id=spec_id.replace("spec-", ""),
            success=True,
            tests_passed=None,
            stdout="dry-run",
            stderr="",
        )


class SingleBatchRunner:
    """BatchRunner that reuses the code executor for each `.butler.yaml` file."""

    def __init__(self, executor: CodeExecutor) -> None:
        self._executor = executor

    def apply_batch(self, spec_dir: Path, batch_group: str) -> List[ExecutionResult]:
        results: List[ExecutionResult] = []
        for spec_path in spec_dir.glob("*.butler.yaml"):
            results.append(self._executor.apply_spec(spec_path))
        return results


class EchoReviewExecutor:
    """Returns a trivial review structure for demonstration purposes."""

    def review_change(
        self, plan: CleanupPlan, diff: str, exec_result: ExecutionResult
    ) -> StructuredReview:
        return {
            "summary": f"Plan {plan.id} applied",
            "diff_preview": diff[:80],
            "tests_passed": exec_result.tests_passed,
        }


def main() -> None:
    plan = CleanupPlan(
        id="plan-demo",
        finding_id="finding-demo",
        title="Demo",
        intent="Showcase Phase 1 hand-offs",
        steps=["Create spec", "Apply spec"],
        constraints=["Keep deterministic"],
        tests_to_run=[],
    )
    backend = FileSpecBackend()
    spec = backend.plan_to_spec(plan)
    spec_path = backend.write_spec(spec, default_spec_path(spec.id).parent)

    executor = PrintExecutor()
    result = executor.apply_spec(spec_path)
    batch_runner = SingleBatchRunner(executor)
    batch_runner.apply_batch(spec_path.parent, spec.batch_group or "default")
    results_path = default_result_path(plan.id)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(result.to_json())

    reviewer = EchoReviewExecutor()
    context = ReviewContext(plan=plan, diff="--- demo diff ---", exec_result=result)
    review = reviewer.review_change(context.plan, context.diff, context.exec_result)
    print("Review context:", review)


if __name__ == "__main__":  # pragma: no cover
    main()
