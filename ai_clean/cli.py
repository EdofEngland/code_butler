"""Placeholder CLI for ai-clean with enumerated subcommands."""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Tuple

# CLI commands intentionally avoid executor/storage imports so they remain
# read-only; plan storage happens inside planner orchestrators.
from ai_clean.analyzers.orchestrator import analyze_repo, format_location_summary
from ai_clean.config import AiCleanConfig, load_config
from ai_clean.executors.backends import BackendApplyResult
from ai_clean.executors.factory import (
    build_code_executor,
    build_executor_backend,
    build_review_executor,
)
from ai_clean.git_helpers import (
    GitError,
    ensure_on_refactor_branch,
    get_diff_stat,
)
from ai_clean.models import ExecutionResult, Finding
from ai_clean.planners.orchestrator import PlannerError, plan_from_finding
from ai_clean.spec_backends.factory import build_spec_backend
from ai_clean.storage import (
    load_execution_result,
    load_plan,
    save_execution_result,
)

CommandDef = Tuple[str, Iterable[str], str]


COMMANDS: Tuple[CommandDef, ...] = (
    ("analyze", ["/analyze"], "Scan a path and report findings."),
    ("clean", ["/clean"], "Select structural findings and optionally apply fixes."),
    ("annotate", ["/annotate"], "Docstring cleanups for missing/weak docstrings."),
    ("organize", ["/organize"], "Suggest small file movements."),
    (
        "cleanup-advanced",
        ["/cleanup-advanced"],
        "Advisory advanced cleanups powered by Codex.",
    ),
    ("plan", ["/plan"], "Generate a plan for a finding (placeholder)."),
    ("apply", ["/apply"], "Apply a stored plan and run tests."),
    (
        "changes-review",
        ["/changes-review"],
        "Summarize changes and risks after apply.",
    ),
)

_CLEAN_ALLOWED_CATEGORIES = ("duplicate_block", "large_file", "long_function")
_CLEAN_MAX_PLANS = 3

_ANNOTATE_MODE_CATEGORIES = {
    "missing": ("missing_docstring",),
    "weak": ("weak_docstring",),
    "all": ("missing_docstring", "weak_docstring"),
}
_ADVANCED_CATEGORY = "advanced_cleanup"


def _placeholder_handler(command_name: str) -> Callable[[argparse.Namespace], int]:
    def handler(_: argparse.Namespace) -> int:
        print(
            f"Command '{command_name}' is a placeholder; no actions are performed yet."
        )
        return 0

    return handler


def _analyze_handler(args: argparse.Namespace) -> int:
    root = args.path
    categories = args.categories or []
    category_filters = {category for category in categories if category}
    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    if category_filters:
        findings = [f for f in findings if f.category in category_filters]

    if not findings:
        print("No findings.")
        return 0

    for finding in findings:
        summaries = [format_location_summary(loc) for loc in finding.locations]
        loc_summary = "; ".join(summaries) if summaries else "(no locations)"
        message = (
            f"[{finding.id}] {finding.category} - {finding.description} :: "
            f"{loc_summary}"
        )
        print(message)
    return 0


def _plan_handler(args: argparse.Namespace) -> int:
    root = args.path
    finding_id = args.finding_id
    chunk_index = args.chunk_index
    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    matches = [finding for finding in findings if finding.id == finding_id]
    if not matches:
        print(
            f"Finding '{finding_id}' not found under '{root}'. "
            f"Run 'ai-clean analyze {root}' to list findings."
        )
        return 2
    if len(matches) > 1:
        print(
            f"Multiple findings with id '{finding_id}' were found. "
            "Provide a narrower --path to disambiguate."
        )
        return 2

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    finding = matches[0]
    try:
        plan = plan_from_finding(
            finding,
            chunk_index=chunk_index,
            config=config,
        )
    except (PlannerError, ValueError) as exc:
        print(f"Failed to build plan: {exc}")
        return 2

    stored_at = plan.metadata.get("stored_at", "(not saved)")
    print(f"Plan ID: {plan.id}")
    print(f"Title: {plan.title}")
    print(f"Intent: {plan.intent}")
    print(f"Stored at: {stored_at}")
    _print_numbered_section("Steps", plan.steps)
    _print_numbered_section("Constraints", plan.constraints)
    _print_numbered_section("Tests to run", plan.tests_to_run)
    return 0


def _apply_handler(args: argparse.Namespace) -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2
    return _run_apply_flow(
        plan_id=args.plan_id,
        config=config,
        skip_tests=args.skip_tests,
        spec_dir=args.spec_dir,
    )


def _run_apply_flow(
    *,
    plan_id: str,
    config: AiCleanConfig,
    skip_tests: bool,
    spec_dir: str | None,
) -> int:
    try:
        ensure_on_refactor_branch(
            config.git.base_branch,
            config.git.refactor_branch,
        )
    except GitError as exc:
        print(f"Git branch enforcement failed: {exc}")
        return 2

    try:
        plan = load_plan(plan_id, plans_dir=config.plans_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load plan '{plan_id}': {exc}")
        return 2

    spec_backend = build_spec_backend(config)
    spec = spec_backend.plan_to_spec(plan)

    spec_dir_path = Path(spec_dir) if spec_dir else config.specs_dir
    spec_dir_path.mkdir(parents=True, exist_ok=True)
    spec_path = spec_backend.write_spec(spec, directory=str(spec_dir_path))
    print(f"Spec written to: {spec_path}")

    backend_executor = build_executor_backend(config)
    backend_result = backend_executor.apply(plan.id, spec_path)
    print(f"Backend instructions: {backend_result.instructions}")

    result: ExecutionResult
    if backend_result.status == "manual":
        result = _build_manual_execution_result(spec_path, backend_result)
    else:
        original_tests = config.tests.default_command
        if skip_tests:
            config.tests.default_command = ""

        try:
            executor = build_code_executor(config)
            result = executor.apply_spec(spec_path)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Failed to apply spec: {exc}")
            return 2
        finally:
            config.tests.default_command = original_tests

        backend_meta = dict(backend_result.metadata or {})
        backend_meta.update(
            {
                "status": backend_result.status,
                "instructions": backend_result.instructions,
                "tests_supported": backend_result.tests_supported,
            }
        )
        result.metadata["backend"] = backend_meta

    execution_path = save_execution_result(
        result,
        plan_id,
        executions_dir=config.executions_dir,
    )

    print(f"Execution result stored at: {execution_path}")
    print(f"Apply success: {'yes' if result.success else 'no'}")
    if not result.success:
        _print_apply_failure_hint(result.metadata.get("apply"), execution_path)

    tests_metadata = result.metadata.get("tests") or {}
    tests_label = _describe_tests_status(
        result.tests_passed,
        skip_tests,
        tests_metadata,
    )
    if result.tests_passed is False:
        tests_label = f"{tests_label} (see {execution_path})"
    print(f"Tests: {tests_label}")
    if result.tests_passed is False:
        _print_tests_failure_hint(tests_metadata, execution_path)

    _print_text_block("Executor stdout", result.stdout)
    _print_text_block("Executor stderr", result.stderr)

    try:
        diff_summary = get_diff_stat()
    except GitError as exc:
        print(f"Failed to summarize git diff: {exc}")
        return 2

    print(diff_summary)

    exit_code = 0
    if not result.success or result.tests_passed is False:
        exit_code = 2
    return exit_code


def _clean_handler(args: argparse.Namespace) -> int:
    root = args.path
    auto_select = args.auto
    skip_tests = args.skip_tests
    spec_dir_override = args.spec_dir

    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    eligible = [f for f in findings if f.category in _CLEAN_ALLOWED_CATEGORIES]
    if not eligible:
        print("No cleanup findings found for duplicate/large/long categories.")
        return 0

    ordered = _order_clean_findings(eligible)
    _print_clean_summary(ordered)

    if auto_select:
        count = min(len(ordered), _CLEAN_MAX_PLANS)
        selected_indexes = list(range(count))
        if not selected_indexes:
            print("No findings available for automatic selection.")
            return 0
        print(f"Automatically selecting {count} finding(s).")
    else:
        selected_indexes = _prompt_for_selection(len(ordered), _CLEAN_MAX_PLANS)
        if not selected_indexes:
            print("No findings selected.")
            return 0

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    plans = []
    exit_code = 0
    for index in selected_indexes:
        finding = ordered[index]
        try:
            plan = plan_from_finding(finding, config=config)
        except (PlannerError, ValueError) as exc:
            print(f"Failed to plan finding '{finding.id}': {exc}")
            exit_code = 2
            continue
        stored_at = plan.metadata.get("stored_at", "(unknown)")
        print(
            f"Created plan {plan.id} ({plan.title}) for finding '{finding.id}'. "
            f"Stored at: {stored_at}"
        )
        plans.append(plan)

    if not plans:
        return exit_code or 2

    for plan in plans:
        apply_prompt = _prompt_yes_no(
            f"Apply plan {plan.id} now? [y/N]: ",
            default=False,
        )
        if apply_prompt:
            result = _run_apply_flow(
                plan_id=plan.id,
                config=config,
                skip_tests=skip_tests,
                spec_dir=spec_dir_override,
            )
            if result != 0:
                exit_code = 2
        else:
            stored_at = plan.metadata.get("stored_at", "(unknown)")
            print(f"Plan saved for later at: {stored_at}")

    return exit_code


def _annotate_handler(args: argparse.Namespace) -> int:
    root = args.path
    mode = args.mode
    categories = _ANNOTATE_MODE_CATEGORIES.get(
        mode, _ANNOTATE_MODE_CATEGORIES["missing"]
    )

    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    doc_findings = [f for f in findings if f.category in categories]
    if not doc_findings:
        print(f"No docstring findings for mode '{mode}'.")
        return 0

    _print_docstring_summary(doc_findings)

    if args.all:
        selected_indexes = list(range(len(doc_findings)))
        print(f"Planning all {len(selected_indexes)} docstring finding(s).")
    else:
        selected_indexes = _prompt_for_selection(len(doc_findings), len(doc_findings))
        if not selected_indexes:
            print("No docstring findings selected.")
            return 0

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    exit_code = 0
    for index in selected_indexes:
        finding = doc_findings[index]
        try:
            plan = plan_from_finding(finding, config=config)
        except (PlannerError, ValueError) as exc:
            print(f"Failed to plan finding '{finding.id}': {exc}")
            exit_code = 2
            continue

        stored_at = plan.metadata.get("stored_at", "(unknown)")
        print(
            f"Created plan {plan.id} ({plan.title}) for finding '{finding.id}'. "
            f"Stored at: {stored_at}"
        )
        _print_numbered_section("Constraints", plan.constraints)
        _print_numbered_section("Steps", plan.steps)
        _print_numbered_section("Tests to run", plan.tests_to_run)
        print("Reminder: keep docstrings concise and factual.")

        apply_now = _prompt_yes_no(
            f"Apply plan {plan.id} now? [y/N]: ",
            default=False,
        )
        if apply_now:
            result = _run_apply_flow(
                plan_id=plan.id,
                config=config,
                skip_tests=args.skip_tests,
                spec_dir=args.spec_dir,
            )
            if result != 0:
                exit_code = 2
        else:
            print(f"Plan saved for later at: {stored_at}")

    return exit_code


def _organize_handler(args: argparse.Namespace) -> int:
    root = args.path
    max_files = args.max_files
    selected_ids = set(args.ids or [])

    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    organize_findings = [
        f
        for f in findings
        if f.category == "organize_candidate" and _within_file_limit(f, max_files)
    ]

    if not organize_findings:
        print("No organize candidates found under the provided constraints.")
        return 0

    _print_organize_summary(organize_findings)

    if selected_ids:
        selected_indexes = [
            index
            for index, finding in enumerate(organize_findings)
            if finding.id in selected_ids
        ]
        missing = selected_ids.difference(f.id for f in organize_findings)
        if missing:
            print(f"Warning: Unknown finding ids ignored: {', '.join(sorted(missing))}")
        if not selected_indexes:
            print("No matching organize findings selected.")
            return 0
    else:
        selected_indexes = _prompt_for_selection(
            len(organize_findings), len(organize_findings)
        )
        if not selected_indexes:
            print("No organize findings selected.")
            return 0

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    exit_code = 0
    for index in selected_indexes:
        finding = organize_findings[index]
        try:
            plan = plan_from_finding(finding, config=config)
        except (PlannerError, ValueError) as exc:
            print(f"Failed to plan finding '{finding.id}': {exc}")
            exit_code = 2
            continue

        stored_at = plan.metadata.get("stored_at", "(unknown)")
        files = [loc.path for loc in finding.locations]
        print(
            f"Plan {plan.id} created for organize candidate '{finding.id}'. "
            f"Destination: {finding.metadata.get('target_folder', '(unknown)')}"
        )
        if files:
            print("Files to move:")
            for file_path in files:
                print(f"  - {file_path}")
        print("Reminder: organize plans only move files; no content edits are made.")
        print(f"Stored at: {stored_at}")

        apply_now = _prompt_yes_no(
            f"Apply plan {plan.id} now? [y/N]: ",
            default=False,
        )
        if apply_now:
            result = _run_apply_flow(
                plan_id=plan.id,
                config=config,
                skip_tests=args.skip_tests,
                spec_dir=args.spec_dir,
            )
            if result != 0:
                exit_code = 2

    return exit_code


def _cleanup_advanced_handler(args: argparse.Namespace) -> int:
    root = args.path
    limit = max(args.limit, 1)

    try:
        findings = analyze_repo(root)
    except FileNotFoundError:
        print(f"Path not found: {root}")
        return 2
    except ValueError as exc:
        print(f"Failed to analyze '{root}': {exc}")
        return 2

    advanced_findings = [f for f in findings if f.category == _ADVANCED_CATEGORY]
    if not advanced_findings:
        print("No advisory advanced cleanups available.")
        return 0

    print(
        f"Codex advisory suggestions (showing up to {limit}). "
        "Plans are stored for manual review; no changes applied."
    )

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    exit_code = 0
    for finding in advanced_findings[:limit]:
        try:
            plan = plan_from_finding(finding, config=config)
        except (PlannerError, ValueError) as exc:
            print(f"Failed to plan advisory finding '{finding.id}': {exc}")
            exit_code = 2
            continue

        plan.metadata["advisory"] = True
        stored_at = plan.metadata.get("stored_at", "(unknown)")
        first_step = plan.steps[0] if plan.steps else "(no steps)"
        print(
            f"[{plan.id}] {plan.title} - {plan.intent}\n"
            f"First step: {first_step}\n"
            f"Stored at: {stored_at}\n"
        )
    return exit_code


def _changes_review_handler(args: argparse.Namespace) -> int:
    plan_id = args.plan_id
    diff_command = args.diff_command
    verbose = args.verbose

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load configuration: {exc}")
        return 2

    try:
        plan = load_plan(plan_id, plans_dir=config.plans_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed to load plan '{plan_id}': {exc}")
        return 2

    try:
        execution_result = load_execution_result(
            plan_id,
            executions_dir=config.executions_dir,
        )
    except FileNotFoundError:
        print(
            f"No execution result found for plan '{plan_id}'. "
            "Run 'ai-clean apply' first."
        )
        return 2
    except ValueError as exc:
        print(f"Execution result for '{plan_id}' is invalid: {exc}")
        return 2

    try:
        diff_text = _capture_diff_text(diff_command)
    except (GitError, RuntimeError) as exc:
        print(f"Failed to capture diff: {exc}")
        return 2

    stored_tests = _describe_tests_status(
        execution_result.tests_passed,
        skip_flag=False,
        tests_metadata=execution_result.metadata.get("tests"),
    )
    print(f"Stored tests: {stored_tests}")

    try:
        completion = _load_review_completion()
    except (ImportError, AttributeError, ValueError, RuntimeError) as exc:
        print(f"Failed to load review completion: {exc}")
        return 2

    try:
        reviewer = build_review_executor(
            config,
            codex_completion=completion,
        )
    except Exception as exc:
        print(f"Failed to build review executor: {exc}")
        return 2

    try:
        review = reviewer.review_change(plan, diff_text, execution_result)
    except Exception as exc:
        print(f"Review executor failed: {exc}")
        return 2

    _print_review_output(review, verbose=verbose)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    description_lines = [
        "ai-clean placeholder CLI",
        (
            "Available commands: /analyze, /clean, /annotate, /organize, "
            "/cleanup-advanced, /plan, /apply, /changes-review."
        ),
    ]
    parser = argparse.ArgumentParser(
        prog="ai-clean",
        description="\n".join(description_lines),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    for name, aliases, help_text in COMMANDS:
        sub = subparsers.add_parser(name, aliases=list(aliases), help=help_text)
        if name == "analyze":
            sub.add_argument(
                "path", nargs="?", default=".", help="Path to analyze (default: .)"
            )
            sub.add_argument(
                "--categories",
                "-c",
                nargs="+",
                metavar="CATEGORY",
                help="Only show findings with matching categories.",
            )
            sub.set_defaults(func=_analyze_handler)
        elif name == "clean":
            sub.add_argument(
                "path",
                nargs="?",
                default=".",
                help="Path to analyze for cleanup findings (default: .)",
            )
            sub.add_argument(
                "--auto",
                action="store_true",
                help="Automatically select up to 3 findings without prompting.",
            )
            sub.add_argument(
                "--skip-tests",
                action="store_true",
                help="Skip tests if you choose to apply plans during this flow.",
            )
            sub.add_argument(
                "--spec-dir",
                help="Directory for writing specs when applying during clean.",
            )
            sub.set_defaults(func=_clean_handler)
        elif name == "annotate":
            sub.add_argument(
                "path",
                nargs="?",
                default=".",
                help="Path to analyze for docstring findings (default: .)",
            )
            sub.add_argument(
                "--mode",
                choices=("missing", "weak", "all"),
                default="missing",
                help="Docstring finding types to include (default: missing).",
            )
            sub.add_argument(
                "--all",
                action="store_true",
                help="Plan all docstring findings without prompting.",
            )
            sub.add_argument(
                "--skip-tests",
                action="store_true",
                help="Skip tests when applying docstring plans.",
            )
            sub.add_argument(
                "--spec-dir",
                help="Directory for writing specs if applying docstring plans.",
            )
            sub.set_defaults(func=_annotate_handler)
        elif name == "organize":
            sub.add_argument(
                "path",
                nargs="?",
                default=".",
                help="Path to analyze for organize candidates (default: .)",
            )
            sub.add_argument(
                "--max-files",
                type=int,
                default=5,
                help="Maximum files per candidate to include (default: 5).",
            )
            sub.add_argument(
                "--ids",
                nargs="+",
                help="Specific finding IDs to select instead of interactive picker.",
            )
            sub.add_argument(
                "--skip-tests",
                action="store_true",
                help="Skip tests when applying organize plans.",
            )
            sub.add_argument(
                "--spec-dir",
                help="Directory for specs if applying organize plans.",
            )
            sub.set_defaults(func=_organize_handler)
        elif name == "cleanup-advanced":
            sub.add_argument(
                "path",
                nargs="?",
                default=".",
                help="Path to analyze for advisory advanced cleanups (default: .)",
            )
            sub.add_argument(
                "--limit",
                type=int,
                default=5,
                help="Maximum number of advisory findings to display (default: 5).",
            )
            sub.set_defaults(func=_cleanup_advanced_handler)
        elif name == "changes-review":
            sub.add_argument("plan_id", help="Plan ID to summarize.")
            sub.add_argument(
                "--diff-command",
                help="Custom shell command to capture diff text (default: git diff).",
            )
            sub.add_argument(
                "--verbose",
                action="store_true",
                help="Include metadata such as prompts and raw responses.",
            )
            sub.set_defaults(func=_changes_review_handler)
        elif name == "plan":
            sub.add_argument("finding_id", help="Finding ID to plan.")
            sub.add_argument(
                "--path",
                "-p",
                default=".",
                help="Path to analyze for locating the finding (default: .)",
            )
            sub.add_argument(
                "--chunk-index",
                type=int,
                default=0,
                help="Duplicate chunk index when planning duplicate_block findings.",
            )
            sub.set_defaults(func=_plan_handler)
        elif name == "apply":
            sub.add_argument("plan_id", help="Plan ID to apply.")
            sub.add_argument(
                "--skip-tests",
                action="store_true",
                help="Skip running tests after applying the spec.",
            )
            sub.add_argument(
                "--spec-dir",
                help="Directory for writing generated specs (default: config value).",
            )
            sub.set_defaults(func=_apply_handler)
        else:
            sub.set_defaults(func=_placeholder_handler(name))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


def _print_numbered_section(label: str, items: Iterable[str]) -> None:
    print(f"{label}:")
    has_items = False
    for index, item in enumerate(items, start=1):
        has_items = True
        print(f"  {index}. {item}")
    if not has_items:
        print("  (none)")


def _describe_tests_status(
    tests_passed: bool | None,
    skip_flag: bool,
    tests_metadata: Dict[str, Any] | None,
) -> str:
    if skip_flag:
        return "skipped (--skip-tests)"
    meta = tests_metadata or {}
    if tests_passed is True:
        return "passed"
    if tests_passed is False:
        return "FAILED"
    reason = meta.get("reason")
    if reason:
        return f"skipped ({reason.replace('_', ' ')})"
    return "skipped"


def _build_manual_execution_result(
    spec_path: str,
    backend_result: BackendApplyResult,
) -> ExecutionResult:
    backend_meta = dict(backend_result.metadata or {})
    backend_meta.update(
        {
            "status": backend_result.status,
            "instructions": backend_result.instructions,
            "tests_supported": backend_result.tests_supported,
        }
    )
    metadata = {
        "backend": backend_meta,
        "tests": {"skipped": True, "reason": "manual_backend"},
    }
    spec_id = Path(spec_path).stem
    return ExecutionResult(
        spec_id=spec_id,
        success=True,
        tests_passed=None,
        stdout=backend_result.instructions,
        stderr="",
        metadata=metadata,
    )


def _print_text_block(label: str, text: str, limit: int = 800) -> None:
    content = (text or "").strip()
    if len(content) > limit:
        content = f"{content[:limit].rstrip()}... [truncated]"
    if not content:
        content = "(empty)"
    print(f"{label}:\n{content}")


def _print_apply_failure_hint(
    apply_metadata: Dict[str, Any] | None,
    execution_path: Path,
) -> None:
    meta = apply_metadata or {}
    command = meta.get("command")
    if command:
        cmd_str = " ".join(str(part) for part in command)
        print(f"Apply command: {cmd_str}")
    return_code = meta.get("returncode")
    if return_code is not None:
        print(f"Apply return code: {return_code}")
    print("Apply failed. Review the stderr above and inspect the diff for issues.")
    print(f"Full logs stored at: {execution_path}")


def _print_tests_failure_hint(
    tests_metadata: Dict[str, Any],
    execution_path: Path,
) -> None:
    command = tests_metadata.get("command")
    if command:
        cmd_str = " ".join(str(part) for part in command)
        print(f"Tests command: {cmd_str}")
    return_code = tests_metadata.get("returncode")
    if return_code is not None:
        print(f"Tests return code: {return_code}")
    print("Tests failed. Re-run them locally, address issues, and reapply the plan.")
    print(f"See execution logs at: {execution_path}")


def _order_clean_findings(findings: list["Finding"]) -> list["Finding"]:
    ordered: list["Finding"] = []
    for category in _CLEAN_ALLOWED_CATEGORIES:
        ordered.extend([f for f in findings if f.category == category])
    return ordered


def _print_clean_summary(findings: list["Finding"]) -> None:
    print("Cleanup findings:")
    current_category = None
    for index, finding in enumerate(findings, start=1):
        if finding.category != current_category:
            current_category = finding.category
            print(f"{current_category}:")
        location = (
            format_location_summary(finding.locations[0])
            if finding.locations
            else "(no location)"
        )
        print(f"  {index}. [{finding.id}] {finding.description} @ {location}")


def _print_docstring_summary(findings: list["Finding"]) -> None:
    print("Docstring findings:")
    for index, finding in enumerate(findings, start=1):
        location = (
            format_location_summary(finding.locations[0])
            if finding.locations
            else "(no location)"
        )
        print(
            f"  {index}. [{finding.id}] ({finding.category}) "
            f"{finding.description} @ {location}"
        )


def _prompt_for_selection(total: int, max_count: int) -> list[int]:
    if total == 0 or max_count <= 0:
        return []

    while True:
        raw = input(
            f"Select up to {max_count} findings by number (comma separated), "
            "or press Enter to cancel: "
        ).strip()
        if not raw:
            return []
        tokens = [part.strip() for part in raw.split(",") if part.strip()]
        indexes: list[int] = []
        seen = set()
        try:
            for token in tokens:
                choice = int(token)
                if choice < 1 or choice > total:
                    raise ValueError
                if choice in seen:
                    continue
                indexes.append(choice - 1)
                seen.add(choice)
                if len(indexes) == max_count:
                    break
        except ValueError:
            print("Invalid selection. Enter numbers like '1,2'.")
            continue
        if indexes:
            return indexes
        print("No selections made.")


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    response = input(prompt).strip().lower()
    if not response:
        return default
    return response in {"y", "yes"}


def _capture_diff_text(diff_command: str | None) -> str:
    if diff_command:
        proc = subprocess.run(
            diff_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            details = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
            raise RuntimeError(f"diff command failed: {details}")
        return proc.stdout.strip() or "(empty diff output)"

    summary = get_diff_stat()
    diff_proc = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_proc.returncode != 0:
        details = (
            diff_proc.stderr.strip() or diff_proc.stdout.strip() or "unknown error"
        )
        raise RuntimeError(f"git diff failed: {details}")
    diff_body = diff_proc.stdout.strip() or "(no diff)"
    return f"{summary}\n\n{diff_body}".strip()


def _load_review_completion():
    target = os.getenv("AI_CLEAN_REVIEW_COMPLETION")
    if not target:
        return lambda prompt: {
            "summary": "Codex completion not configured; showing prompt preview.",
            "risks": [],
            "suggested_checks": [],
            "metadata": {"prompt_preview": prompt[:500]},
        }
    module_name, sep, attr = target.rpartition(":")
    if not sep:
        raise RuntimeError(
            "AI_CLEAN_REVIEW_COMPLETION must be in 'module:callable' format."
        )
    module = importlib.import_module(module_name)
    completion = getattr(module, attr)
    return completion


def _print_review_output(review: dict, *, verbose: bool) -> None:
    summary = str(review.get("summary", "")).strip() or "(no summary)"
    risks = review.get("risks") or []
    checks = review.get("suggested_checks") or []
    print("Summary:\n" + summary)
    print("Risks:")
    if risks:
        for index, risk in enumerate(risks, start=1):
            print(f"  {index}. {risk}")
    else:
        print("  (none)")

    print("Suggested checks:")
    if checks:
        for index, check in enumerate(checks, start=1):
            print(f"  {index}. {check}")
    else:
        print("  (none)")

    if verbose:
        metadata = review.get("metadata") or {}
        if metadata:
            print("Metadata:")
            for key, value in metadata.items():
                print(f"- {key}: {value}")


def _within_file_limit(finding: "Finding", max_files: int) -> bool:
    if max_files <= 0:
        return True
    return len(finding.locations) <= max_files


def _print_organize_summary(findings: list["Finding"]) -> None:
    print("Organize candidates:")
    for index, finding in enumerate(findings, start=1):
        target = finding.metadata.get("target_folder", "(unknown)")
        files = [loc.path for loc in finding.locations]
        print(f"  {index}. [{finding.id}] -> {target} ({len(files)} files)")
        for file_path in files:
            print(f"      - {file_path}")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
