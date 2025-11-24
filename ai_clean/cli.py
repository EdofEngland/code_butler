"""CLI entrypoint for ai-clean."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Callable

from ai_clean.analyzers import analyze_repo
from ai_clean.analyzers.docstrings import find_docstring_gaps
from ai_clean.analyzers.organize import propose_organize_groups
from ai_clean.commands.apply import apply_plan
from ai_clean.commands.ingest import IngestError, ingest_codex_artifact
from ai_clean.commands.plan import run_plan_for_finding
from ai_clean.config import load_config
from ai_clean.factories import get_review_executor
from ai_clean.metadata import ensure_metadata_dirs, resolve_metadata_paths
from ai_clean.models import ExecutionResult, Finding
from ai_clean.planners.orchestrator import plan_from_finding
from ai_clean.plans import load_plan, save_plan

CommandHandler = Callable[[argparse.Namespace], int]


_COMMAND_SPECS: tuple[tuple[str, str], ...] = (
    ("analyze", "Scan a project and propose cleanup plans"),
    ("clean", "Guided basic cleanup for common findings"),
    ("annotate", "Generate docstring improvement plans"),
    ("organize", "Group related files and propose organize moves"),
    (
        "cleanup-advanced",
        "Disabled: run Codex /cleanup-advanced slash command manually",
    ),
    ("plan", "Author a new ButlerSpec plan for a specific finding"),
    ("apply", "Apply a ButlerSpec plan using Codex"),
    ("ingest", "Ingest Codex artifact output into ai-clean results"),
    ("changes-review", "Review executed plans and summarize risks"),
)

_CLEAN_CATEGORIES: set[str] = {"duplicate_block", "large_file", "long_function"}


def _make_handler(command_label: str) -> CommandHandler:
    def _handler(_: argparse.Namespace) -> int:
        print(f"TODO: /{command_label}")
        return 0

    return _handler


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-clean",
        description=(
            "ButlerSpec-governed cleanup assistant. Commands mirror the "
            "Phase 1 system sketch (plan → spec → apply)."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    for command_name, help_text in _COMMAND_SPECS:
        subparser = subparsers.add_parser(command_name, help=help_text)
        if command_name == "analyze":
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "--json",
                action="store_true",
                help="Emit findings as JSON instead of a text table",
            )
            subparser.set_defaults(handler=_run_analyze_command)
            continue
        if command_name == "clean":
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "--path",
                default=None,
                help="Optional sub-path to limit analyzers (relative to root)",
            )
            subparser.set_defaults(handler=_run_clean_command)
            continue
        if command_name == "annotate":
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "path",
                nargs="?",
                default=None,
                help="Optional sub-path to limit docstring analysis (relative to root)",
            )
            subparser.add_argument(
                "--path",
                dest="path_override",
                default=None,
                help="Optional sub-path to limit docstring analysis (relative to root)",
            )
            subparser.add_argument(
                "--mode",
                choices=["missing", "all"],
                default="missing",
                help="Select docstring categories: missing only (default) or all",
            )
            subparser.set_defaults(handler=_run_annotate_command)
            continue
        if command_name == "organize":
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "path",
                nargs="?",
                default=None,
                help="Optional sub-path to limit organize analysis (relative to root)",
            )
            subparser.add_argument(
                "--path",
                dest="path_override",
                default=None,
                help="Optional sub-path to limit organize analysis (relative to root)",
            )
            subparser.set_defaults(handler=_run_organize_command)
            continue
        if command_name == "changes-review":
            subparser.add_argument("plan_id", help="ID of the plan to review")
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.set_defaults(handler=_run_changes_review_command)
            continue
        if command_name == "plan":
            subparser.add_argument("finding_id", help="ID of the finding to plan for")
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "--findings-json",
                default=None,
                help=(
                    "Path to findings JSON (defaults to "
                    ".ai-clean/findings.json under the chosen root)"
                ),
            )
            subparser.set_defaults(handler=_run_plan_command)
            continue
        if command_name == "cleanup-advanced":
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "--findings-json",
                required=True,
                help="Path to findings JSON generated by `ai-clean analyze --json`",
            )
            subparser.add_argument(
                "--json",
                action="store_true",
                help="Emit findings as JSON instead of a text table",
            )
            subparser.set_defaults(handler=_run_cleanup_advanced_command)
            continue
        if command_name == "apply":
            subparser.add_argument("plan_id", help="ID of the plan to apply")
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.set_defaults(handler=_run_apply_command)
            continue
        if command_name == "ingest":
            subparser.add_argument(
                "--plan-id",
                required=True,
                help="Plan ID whose execution result should be updated",
            )
            subparser.add_argument(
                "--artifact",
                required=False,
                help=(
                    "Path to Codex artifact JSON. Defaults to "
                    ".ai-clean/results/<plan>.codex.json under --root."
                ),
            )
            subparser.add_argument(
                "--root",
                default=".",
                help="Path to the repository root (defaults to current directory)",
            )
            subparser.add_argument(
                "--config",
                default=None,
                help="Optional ai-clean configuration file to load",
            )
            subparser.add_argument(
                "--update-findings",
                action="store_true",
                help="When set, ingest suggestions array into findings JSON",
            )
            subparser.add_argument(
                "--findings-json",
                default=None,
                help=(
                    "Optional findings JSON path "
                    "(defaults to .ai-clean/findings.json)"
                ),
            )
            subparser.set_defaults(handler=_run_ingest_command)
            continue
        subparser.set_defaults(handler=_make_handler(command_name))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)

    if command and command not in ("analyze",):
        ensure_metadata_dirs()

    handler: CommandHandler | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


def _run_analyze_command(args: argparse.Namespace) -> int:
    """Run analyzers in read-only mode for the target repository.

    This command reports findings but does not create or modify any
    ai-clean metadata (plans, specs, or execution results).
    """
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    try:
        findings = analyze_repo(root, config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while running analyzers: {exc}", file=sys.stderr)
        return 1

    return _print_findings(findings, args.json)


def _run_clean_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    if args.path:
        raw_path = Path(args.path).expanduser()
        path_filter = (
            (root / raw_path).resolve()
            if not raw_path.is_absolute()
            else raw_path.resolve()
        )
    else:
        path_filter = None

    try:
        findings = analyze_repo(root, config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while running analyzers: {exc}", file=sys.stderr)
        return 1

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while loading configuration: {exc}", file=sys.stderr)
        return 1

    _, plans_dir, _, _ = resolve_metadata_paths(root, config)

    candidates = [
        finding
        for finding in findings
        if finding.category in {"duplicate_block", "large_file", "long_function"}
        and _finding_matches_path(root, finding, path_filter)
    ]
    candidates.sort(key=lambda finding: (finding.category, finding.id))

    if not candidates:
        print("No applicable findings detected.")
        return 0

    _print_candidate_findings(candidates)
    selected_indexes = _prompt_for_indexes(len(candidates))
    if not selected_indexes:
        print("No cleanups selected.")
        return 0

    overall_failure = False
    for index in selected_indexes:
        finding = candidates[index]
        try:
            plan_entries = run_plan_for_finding(root, config_path, finding)
        except NotImplementedError as exc:
            print(str(exc), file=sys.stderr)
            overall_failure = True
            continue
        except FileNotFoundError as exc:
            print(f"Failed to create plan for {finding.id}: {exc}", file=sys.stderr)
            overall_failure = True
            continue
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"Unexpected error while creating plan for {finding.id}: {exc}",
                file=sys.stderr,
            )
            overall_failure = True
            continue

        for plan, plan_path in sorted(plan_entries, key=lambda entry: entry[0].id):
            target_file = plan.metadata.get("target_file", "unknown-target")
            print(f"Plan created: {plan.id} -> {target_file} ({plan_path})")
            decision = _prompt_plan_action(plan.id)
            if decision == "skip":
                continue
            if decision == "save":
                print(
                    f"Saved plan {plan.id}. "
                    f"Run 'ai-clean apply {plan.id}' to execute this plan later."
                )
                continue
            try:
                result, spec_path = apply_plan(plans_dir.parent, config_path, plan.id)
            except FileNotFoundError as exc:
                print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
                overall_failure = True
                continue
            except ValueError as exc:
                print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
                overall_failure = True
                continue
            except Exception as exc:  # pragma: no cover - defensive
                print(
                    f"Unexpected error while applying {plan.id}: {exc}", file=sys.stderr
                )
                overall_failure = True
                continue

    _print_apply_summary(plan.id, spec_path, result)
    if not result.success and not _manual_execution_required(result):
        overall_failure = True

    return 1 if overall_failure else 0


def _run_annotate_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    raw_path: str | None = args.path_override or args.path
    if raw_path:
        candidate = Path(raw_path).expanduser()
        path_filter = (
            (root / candidate).resolve()
            if not candidate.is_absolute()
            else candidate.resolve()
        )
    else:
        path_filter = None

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while loading configuration: {exc}", file=sys.stderr)
        return 1

    _, plans_dir, _, _ = resolve_metadata_paths(root, config)

    try:
        findings = find_docstring_gaps(root, config.analyzers.docstring)
    except Exception as exc:  # pragma: no cover - defensive
        print(
            f"Unexpected error while running docstring analyzer: {exc}", file=sys.stderr
        )
        return 1

    allowed_categories = {"missing_docstring"}
    if args.mode == "all":
        allowed_categories.add("weak_docstring")

    docstring_findings = [
        _ensure_docstring_symbol_name(finding)
        for finding in findings
        if finding.category in allowed_categories
        and _finding_matches_path(root, finding, path_filter)
    ]
    docstring_findings.sort(key=_docstring_sort_key)

    if not docstring_findings:
        print("No docstring findings detected.")
        return 0

    grouped = _group_docstring_findings(docstring_findings)
    _print_docstring_targets(grouped)

    selection = _prompt_module_selection(len(grouped))
    if selection is None:
        print("No modules selected.")
        return 0
    targets = grouped if selection == "all" else [grouped[index] for index in selection]

    created_plans: list[tuple[object, Path]] = []
    overall_failure = False
    for module_path, module_findings in targets:
        for finding in module_findings:
            try:
                plans = plan_from_finding(finding, config)
            except NotImplementedError as exc:
                print(str(exc), file=sys.stderr)
                overall_failure = True
                continue
            except Exception as exc:  # pragma: no cover - defensive
                print(
                    f"Unexpected error while creating plan for {finding.id}: {exc}",
                    file=sys.stderr,
                )
                overall_failure = True
                continue

            for plan in sorted(plans, key=lambda plan: plan.id):
                plan_path = save_plan(plan, root=plans_dir.parent)
                created_plans.append((plan, plan_path))
                target_file = plan.metadata.get("target_file", module_path.as_posix())
                print(f"Plan created: {plan.id} -> {target_file} ({plan_path})")

    if not created_plans:
        print("No plans created.")
        return 1 if overall_failure else 0

    planned_symbols = sum(len(item[1]) for item in targets)
    print(
        f"Created {len(created_plans)} plan(s) for "
        f"{planned_symbols} docstring(s) across {len(targets)} module(s)."
    )

    decision = _prompt_docstring_plan_action()
    if decision == "save":
        print(
            "Plans saved. Run "
            f"'ai-clean apply <PLAN_ID> --root {root}' to execute later."
        )
        return 1 if overall_failure else 0

    applied = 0
    for plan, _ in created_plans:
        try:
            result, spec_path = apply_plan(plans_dir.parent, config_path, plan.id)
        except FileNotFoundError as exc:
            print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
            overall_failure = True
            continue
        except ValueError as exc:
            print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
            overall_failure = True
            continue
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Unexpected error while applying {plan.id}: {exc}", file=sys.stderr)
            overall_failure = True
            continue

    _print_apply_summary(plan.id, spec_path, result)
    applied += 1
    if not result.success and not _manual_execution_required(result):
        overall_failure = True

    print(f"Planned {len(created_plans)} docstring(s); applied {applied} plan(s).")
    return 1 if overall_failure else 0


def _run_organize_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    raw_path: str | None = args.path_override or args.path
    if raw_path:
        candidate = Path(raw_path).expanduser()
        path_filter = (
            (root / candidate).resolve()
            if not candidate.is_absolute()
            else candidate.resolve()
        )
    else:
        path_filter = None

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while loading configuration: {exc}", file=sys.stderr)
        return 1

    _, plans_dir, _, _ = resolve_metadata_paths(root, config)

    try:
        findings = propose_organize_groups(root, config.analyzers.organize)
    except Exception as exc:  # pragma: no cover - defensive
        print(
            f"Unexpected error while running organize analyzer: {exc}", file=sys.stderr
        )
        return 1

    candidates = [
        _normalize_organize_finding(finding)
        for finding in findings
        if finding.category == "organize_candidate"
        and _finding_matches_path(root, finding, path_filter)
    ]
    candidates.sort(key=_organize_sort_key)

    if not candidates:
        print("No organize candidates detected.")
        return 0

    _print_organize_candidates(candidates)
    selected_indexes = _prompt_for_organize_indexes(len(candidates))
    if not selected_indexes:
        print("No organize plans selected.")
        return 0

    overall_failure = False
    created_plans: list[tuple[object, Path]] = []
    applied = 0

    for index in selected_indexes:
        finding = candidates[index]
        topic = str(finding.metadata.get("topic", ""))
        member_count = len(
            finding.metadata.get("files") or finding.metadata.get("members") or []
        )
        try:
            plans = plan_from_finding(finding, config)
        except NotImplementedError as exc:
            print(str(exc), file=sys.stderr)
            overall_failure = True
            continue
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"Unexpected error while creating plan for {finding.id}: {exc}",
                file=sys.stderr,
            )
            overall_failure = True
            continue

        for plan in sorted(plans, key=lambda plan: plan.id):
            plan_path = save_plan(plan, root=plans_dir.parent)
            print(
                f"Plan created: {plan.id} | topic={topic or 'unknown'} | "
                f"files={member_count} | {plan_path}"
            )
            decision = _prompt_organize_plan_action(plan.id)
            if decision == "save":
                print(
                    "Saved plan. Run "
                    f"'ai-clean apply {plan.id} --root {root}' to execute later."
                )
                created_plans.append((plan, plan_path))
                continue
            try:
                result, spec_path = apply_plan(plans_dir.parent, config_path, plan.id)
            except FileNotFoundError as exc:
                print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
                overall_failure = True
                created_plans.append((plan, plan_path))
                continue
            except ValueError as exc:
                print(f"Failed to apply plan {plan.id}: {exc}", file=sys.stderr)
                overall_failure = True
                created_plans.append((plan, plan_path))
                continue
            except Exception as exc:  # pragma: no cover - defensive
                print(
                    f"Unexpected error while applying {plan.id}: {exc}", file=sys.stderr
                )
                overall_failure = True
                created_plans.append((plan, plan_path))
                continue

            _print_apply_summary(plan.id, spec_path, result)
            applied += 1
            created_plans.append((plan, plan_path))
            if not result.success and not _manual_execution_required(result):
                overall_failure = True

    if created_plans:
        print(
            f"Created {len(created_plans)} organize plan(s); applied {applied} plan(s)."
        )

    return 1 if overall_failure else 0


def _run_changes_review_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    plan_id = args.plan_id
    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while loading configuration: {exc}", file=sys.stderr)
        return 1

    _, plans_dir, specs_dir, results_dir = resolve_metadata_paths(root, config)

    try:
        plan = load_plan(plan_id, root=plans_dir.parent)
    except FileNotFoundError:
        plan_path = (plans_dir / f"{plan_id}.json").resolve()
        print(
            f"CleanupPlan not found for plan_id {plan_id!r} at {plan_path}",
            file=sys.stderr,
        )
        return 1

    spec_path = (specs_dir / f"{plan_id}-spec.butler.yaml").resolve()
    spec_text: str | None
    if spec_path.is_file():
        try:
            spec_text = spec_path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Failed to read ButlerSpec: {exc}", file=sys.stderr)
            return 1
    else:
        spec_text = None

    exec_result, exec_warning = _load_execution_result(results_dir, plan_id)
    diff_text = exec_result.git_diff or "" if exec_result else ""
    warnings: list[str] = []
    if spec_text is None:
        warnings.append(
            "ButlerSpec not found for plan "
            f"{plan_id} ({_display_path(spec_path, root)})"
        )
    if exec_warning:
        warnings.append(exec_warning)
    if not diff_text.strip():
        warnings.append("Git diff not available; review based on plan/spec only.")
    if exec_result:
        tests_meta = (
            (exec_result.metadata or {}).get("tests") if exec_result.metadata else None
        )
        tests_note = _tests_warning(tests_meta, exec_result.tests_passed)
        if tests_note:
            warnings.append(tests_note)

    review_diff = _compose_review_diff(diff_text, spec_text)
    review_exec_result = _prepare_execution_result_for_review(
        plan_id, exec_result, diff_text, spec_path
    )

    try:
        review_handle = get_review_executor(config)
        reviewer = review_handle.reviewer
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Failed to initialize review executor: {exc}", file=sys.stderr)
        return 1

    try:
        review_payload = reviewer.review_change(
            plan, review_diff, review_exec_result, plan_id=plan_id
        )
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Failed to run review: {exc}", file=sys.stderr)
        return 1

    _print_review_summary(plan_id, review_payload, warnings)
    return 0


def _run_cleanup_advanced_command(args: argparse.Namespace) -> int:
    payload_path = Path(args.findings_json).expanduser().resolve()
    command = f"codex /cleanup-advanced {shlex.quote(str(payload_path))}"
    message = (
        "Advanced cleanup is disabled: Codex integration requires the "
        "/cleanup-advanced slash command. No Codex prompts were run.\n"
        f"Run from Codex CLI with your payload:\n{command}"
    )
    print(message, file=sys.stderr)
    return 1


def _run_apply_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    plan_id = args.plan_id

    try:
        result, spec_path = apply_plan(root, config_path, plan_id)
    except FileNotFoundError as exc:
        print(f"Failed to load plan or configuration: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Plan failed validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while applying plan: {exc}", file=sys.stderr)
        return 1

    _print_apply_summary(plan_id, spec_path, result)
    if _manual_execution_required(result):
        return 0
    return 0 if result.success else 1


def _run_ingest_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    plan_id = args.plan_id

    try:
        config = load_config(config_path)
    except Exception as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        return 1

    _, _, _, results_dir = resolve_metadata_paths(root, config)
    if args.artifact:
        artifact_path = Path(args.artifact).expanduser()
        if not artifact_path.is_absolute():
            artifact_path = (root / artifact_path).resolve()
        else:
            artifact_path = artifact_path.resolve()
    else:
        artifact_path = (results_dir / f"{plan_id}.codex.json").resolve()

    if args.findings_json:
        findings_path = Path(args.findings_json).expanduser()
        if not findings_path.is_absolute():
            findings_path = (root / findings_path).resolve()
        else:
            findings_path = findings_path.resolve()
    else:
        findings_path = None

    try:
        result, summary = ingest_codex_artifact(
            plan_id=plan_id,
            artifact_path=artifact_path,
            results_dir=results_dir,
            root=root,
            update_findings=args.update_findings,
            findings_path=findings_path,
            max_suggestions=config.analyzers.advanced.max_suggestions,
            max_suggestion_files=config.analyzers.advanced.max_files,
        )
    except (IngestError, FileNotFoundError) as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1

    _print_ingest_summary(
        plan_id,
        artifact_path,
        result,
        summary.tests_status,
        (summary.diff_added, summary.diff_removed),
        summary.suggestions_ingested,
    )
    return 0 if result.success else 1


def _load_findings_from_json(path: Path) -> list[Finding]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):  # pragma: no cover - defensive
        raise ValueError("Findings JSON must be an array of Finding objects")
    return [Finding.model_validate(item) for item in payload]


def _resolve_findings_path(root: Path, findings_arg: str | None) -> Path:
    if findings_arg:
        return Path(findings_arg).expanduser().resolve()
    return (root / ".ai-clean" / "findings.json").resolve()


def _run_plan_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = _resolve_config_path(root, args.config)
    findings_path = _resolve_findings_path(root, args.findings_json)

    try:
        findings = _load_findings_from_json(findings_path)
    except FileNotFoundError:
        print(
            f"Failed to load findings JSON: {findings_path}",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while loading findings: {exc}", file=sys.stderr)
        return 1

    finding_id = args.finding_id
    target: Finding | None = None
    for item in findings:
        if item.id == finding_id:
            target = item
            break
    if target is None:
        print(
            f"Finding with id {finding_id!r} not found in findings JSON.",
            file=sys.stderr,
        )
        return 1

    try:
        plans_with_paths = run_plan_for_finding(root, config_path, target)
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error while creating plans: {exc}", file=sys.stderr)
        return 1

    if not plans_with_paths:
        return 0

    for plan, path in sorted(plans_with_paths, key=lambda item: item[0].id):
        steps_preview = ""
        if plan.steps:
            steps_preview = (
                f"{len(plan.steps)} steps (first: {plan.steps[0].description})"
            )
        constraints_count = len(plan.constraints) if plan.constraints else 0
        tests_count = len(plan.tests_to_run) if plan.tests_to_run else 0
        print(
            f"{plan.id} | {plan.title} | {plan.intent} | "
            f"{steps_preview} | constraints={constraints_count}, "
            f"tests_to_run={tests_count} | {path}"
        )
    return 0


def _finding_matches_path(
    root: Path, finding: Finding, path_filter: Path | None
) -> bool:
    if path_filter is None:
        return True

    for location in finding.locations:
        location_path = location.path
        resolved = (
            (root / location_path).resolve()
            if not location_path.is_absolute()
            else location_path.resolve()
        )
        try:
            resolved.relative_to(path_filter)
            return True
        except ValueError:
            continue
    return False


def _organize_sort_key(finding: Finding) -> tuple[int, str, str]:
    metadata = finding.metadata or {}
    topic = metadata.get("topic") or ""
    members = metadata.get("files") or metadata.get("members") or []
    first_member = members[0] if members else ""
    return (-len(members), str(topic), str(first_member))


def _normalize_organize_finding(finding: Finding) -> Finding:
    metadata = dict(finding.metadata)
    if "files" not in metadata and "members" in metadata:
        metadata["files"] = list(metadata["members"])
    return finding.model_copy(update={"metadata": metadata})


def _print_organize_candidates(findings: list[Finding]) -> None:
    for index, finding in enumerate(findings, start=1):
        topic = finding.metadata.get("topic", "unknown")
        members = finding.metadata.get("files") or finding.metadata.get("members") or []
        print(f"{index}. topic={topic} ({len(members)} files)")
        for member in members:
            print(f"   - {member}")


def _prompt_for_organize_indexes(total: int) -> list[int]:
    prompt = (
        "Select organize groups by index (comma-separated), or press Enter for none: "
    )
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return []

        if raw == "" or raw.lower() in {"n", "none"}:
            return []

        parts = [part.strip() for part in raw.split(",") if part.strip()]
        indexes: list[int] = []
        invalid = False
        for part in parts:
            if not part.isdigit():
                invalid = True
                break
            value = int(part)
            if value < 1 or value > total:
                invalid = True
                break
            if value - 1 not in indexes:
                indexes.append(value - 1)
        if invalid:
            print("Invalid selection. Enter indexes like 1 or 1,3,4.")
            continue
        return indexes


def _prompt_organize_plan_action(plan_id: str) -> str:
    prompt = f"Plan {plan_id}: (S)ave only or (A)pply now [S]: "
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "save"

        if raw in {"", "s", "save"}:
            return "save"
        if raw in {"a", "apply"}:
            return "apply"
        print("Invalid choice. Enter S or A.")


def _docstring_sort_key(finding: Finding) -> tuple[str, str, str]:
    location_path = finding.locations[0].path if finding.locations else Path("")
    symbol_name = (
        finding.metadata.get("symbol_name")
        or finding.metadata.get("qualified_name")
        or ""
    )
    return (location_path.as_posix(), symbol_name, finding.id)


def _group_docstring_findings(
    findings: list[Finding],
) -> list[tuple[Path, list[Finding]]]:
    grouped: dict[str, list[Finding]] = {}
    for finding in findings:
        location_path = finding.locations[0].path if finding.locations else Path("")
        key = location_path.as_posix()
        grouped.setdefault(key, []).append(finding)

    ordered: list[tuple[Path, list[Finding]]] = []
    for key in sorted(grouped.keys()):
        members = grouped[key]
        members.sort(key=_docstring_sort_key)
        ordered.append((Path(key), members))
    return ordered


def _print_docstring_targets(groups: list[tuple[Path, list[Finding]]]) -> None:
    for index, (path, findings) in enumerate(groups, start=1):
        categories = ", ".join(sorted({finding.category for finding in findings}))
        label = "docstring" if len(findings) == 1 else "docstrings"
        print(f"{index}. {path.as_posix()} ({len(findings)} {label}; {categories})")


def _prompt_module_selection(total: int) -> list[int] | str | None:
    prompt = (
        "Select modules by index (comma-separated), 'a' for all modules, "
        "or press Enter to cancel: "
    )
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if raw in {"", "n", "none", "cancel"}:
            return None
        if raw in {"a", "all"}:
            return "all"

        parts = [part.strip() for part in raw.split(",") if part.strip()]
        indexes: list[int] = []
        invalid = False
        for part in parts:
            if not part.isdigit():
                invalid = True
                break
            value = int(part)
            if value < 1 or value > total:
                invalid = True
                break
            if value - 1 not in indexes:
                indexes.append(value - 1)
        if invalid:
            print("Invalid selection. Enter indexes like 1 or 1,3,4, or 'a' for all.")
            continue
        return indexes


def _prompt_docstring_plan_action() -> str:
    prompt = "Apply docstring plans now? (S)ave only or (A)pply now [S]: "
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "save"

        if raw in {"", "s", "save"}:
            return "save"
        if raw in {"a", "apply"}:
            return "apply"
        print("Invalid choice. Enter S or A.")


def _ensure_docstring_symbol_name(finding: Finding) -> Finding:
    symbol_name = finding.metadata.get("symbol_name")
    if symbol_name:
        return finding

    qualified_name = finding.metadata.get("qualified_name") or ""
    derived_name = str(qualified_name).split(".")[-1] if qualified_name else ""
    if not derived_name and finding.locations:
        derived_name = finding.locations[0].path.stem
    metadata = dict(finding.metadata)
    metadata["symbol_name"] = derived_name or finding.id
    return finding.model_copy(update={"metadata": metadata})


def _print_candidate_findings(findings: list[Finding]) -> None:
    for index, finding in enumerate(findings, start=1):
        summary = _format_finding_summary(finding)
        print(f"{index}. {summary}")


def _format_finding_summary(finding: Finding) -> str:
    location = finding.locations[0] if finding.locations else None
    location_text = ""
    if location:
        location_text = (
            f" @ {location.path.as_posix()}:{location.start_line}-{location.end_line}"
        )
    return f"{finding.category} | {finding.id} | {finding.description}{location_text}"


def _prompt_for_indexes(total: int) -> list[int]:
    prompt = "Select findings by index (comma-separated), or press Enter for none: "
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return []

        if raw == "" or raw.lower() in {"n", "none"}:
            return []

        parts = [part.strip() for part in raw.split(",") if part.strip()]
        indexes: list[int] = []
        invalid = False
        for part in parts:
            if not part.isdigit():
                invalid = True
                break
            value = int(part)
            if value < 1 or value > total:
                invalid = True
                break
            if value - 1 not in indexes:
                indexes.append(value - 1)
        if invalid:
            print("Invalid selection. Enter indexes like 1 or 1,3,4.")
            continue
        return indexes


def _prompt_plan_action(plan_id: str) -> str:
    prompt = f"Plan {plan_id}: (S)ave only, (A)pply now, or (K)skip this plan [S]: "
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "save"

        if raw in {"", "s", "save"}:
            return "save"
        if raw in {"a", "apply"}:
            return "apply"
        if raw in {"k", "skip"}:
            return "skip"
        print("Invalid choice. Enter S, A, or K.")


def _print_apply_summary(plan_id: str, spec_path: str, result: ExecutionResult) -> None:
    print(f"Spec path: {spec_path}")
    command = _resolve_slash_command(spec_path, result)
    if command:
        print(f"Run in Codex: {command}")
    print(f"Apply success: {result.success}")
    _print_tests_status(result)
    if result.git_diff:
        print("Git diff stat:")
        print(result.git_diff)
    if result.stdout:
        print("Executor stdout:")
        print(result.stdout)
    if result.stderr:
        print("Executor stderr:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)


def _resolve_slash_command(spec_path: str, result: ExecutionResult) -> str | None:
    metadata = result.metadata or {}
    command = metadata.get("slash_command") if isinstance(metadata, dict) else None
    if isinstance(command, str) and command.strip():
        return command.strip()
    if spec_path:
        return f"codex /butler-exec {shlex.quote(spec_path)}"
    return None


def _manual_execution_required(result: ExecutionResult) -> bool:
    metadata = result.metadata or {}
    return bool(
        isinstance(metadata, dict) and metadata.get("manual_execution_required")
    )


def _print_findings(findings: list[Finding], as_json: bool) -> int:
    if as_json:
        payload = [finding.model_dump(mode="json") for finding in findings]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if not findings:
        print("No findings detected.")
        return 0

    for finding in findings:
        print(f"{finding.id} | {finding.category} | {finding.description}")
        for location in finding.locations:
            rel_path = location.path.as_posix()
            print(f"  - {rel_path}:{location.start_line}-{location.end_line}")
    return 0


def _resolve_config_path(root: Path, config_arg: str | None) -> Path | None:
    if config_arg:
        return Path(config_arg).expanduser().resolve()
    return root / "ai-clean.toml"


def _load_execution_result(
    results_dir: Path, plan_id: str
) -> tuple[ExecutionResult | None, str | None]:
    path = (results_dir / f"{plan_id}.json").resolve()
    if not path.is_file():
        return None, "ExecutionResult not found; apply/test details unavailable."
    try:
        return ExecutionResult.from_json(path.read_text()), None
    except Exception as exc:
        return None, f"ExecutionResult could not be parsed: {exc}"


def _compose_review_diff(diff_text: str, spec_text: str | None) -> str:
    base = diff_text.strip() if diff_text else "(no diff available)"
    if spec_text:
        return f"{base}\n\nButlerSpec:\n{spec_text.strip()}"
    return base


def _prepare_execution_result_for_review(
    plan_id: str,
    exec_result: ExecutionResult | None,
    diff_text: str,
    spec_path: Path,
) -> ExecutionResult:
    if spec_path.name.endswith(".butler.yaml"):
        spec_id = spec_path.name[: -len(".butler.yaml")]
    else:
        spec_id = spec_path.stem if spec_path.name else f"{plan_id}-spec"
    if exec_result:
        updates: dict[str, object] = {}
        if diff_text and not exec_result.git_diff:
            updates["git_diff"] = diff_text
        if not exec_result.spec_id and spec_id:
            updates["spec_id"] = spec_id
        if updates:
            return exec_result.model_copy(update=updates)
        return exec_result
    return ExecutionResult(
        spec_id=spec_id,
        plan_id=plan_id,
        success=False,
        tests_passed=None,
        stdout="",
        stderr="",
        git_diff=diff_text or None,
        metadata={"missing_execution_result": True},
    )


def _normalize_review_payload(payload: object) -> dict[str, object]:
    if isinstance(payload, str):
        return {
            "summary": payload.strip() or "(no summary provided)",
            "risk_grade": "unknown",
            "manual_checks": [],
        }
    if not isinstance(payload, dict):
        return {
            "summary": "(no summary provided)",
            "risk_grade": "unknown",
            "manual_checks": [],
        }
    manual_checks_raw = payload.get("manual_checks", [])
    manual_checks = (
        [str(item).strip() for item in manual_checks_raw if str(item).strip()]
        if isinstance(manual_checks_raw, list)
        else []
    )
    summary = str(payload.get("summary", "")).strip() or "(no summary provided)"
    risk_grade = str(payload.get("risk_grade", "unknown")).strip() or "unknown"
    normalized: dict[str, object] = {
        "summary": summary,
        "risk_grade": risk_grade,
        "manual_checks": manual_checks,
    }
    if "constraints" in payload:
        normalized["constraints"] = payload["constraints"]
    return normalized


def _print_review_summary(
    plan_id: str, review_payload: object, warnings: list[str]
) -> None:
    review = _normalize_review_payload(review_payload)
    summary = review.get("summary", "(no summary provided)")
    risk = review.get("risk_grade", "unknown")
    manual_checks = review.get("manual_checks") or []
    constraint_notes: list[str] = []
    constraints = review.get("constraints")
    if isinstance(constraints, list):
        constraint_notes.extend(
            [str(item).strip() for item in constraints if str(item).strip()]
        )
    elif isinstance(constraints, str) and constraints.strip():
        constraint_notes.append(constraints.strip())
    constraint_notes.extend(warnings)

    print("Summary of Changes:")
    print(summary)
    print()
    print("Risk Assessment:")
    print(risk)
    print()
    print("Manual QA Suggestions:")
    if manual_checks:
        for check in manual_checks:
            print(f"- {check}")
    else:
        print("None noted.")

    if constraint_notes:
        print()
        print("Constraint Validation Notes:")
        for note in constraint_notes:
            print(f"- {note}")


def _print_tests_status(result: ExecutionResult) -> None:
    tests_meta = (result.metadata or {}).get("tests") if result.metadata else None
    if not tests_meta:
        print(f"Tests status: unknown (tests_passed={result.tests_passed})")
        return

    status = str(tests_meta.get("status", "unknown"))
    parts = [f"Tests status: {status}"]
    command = tests_meta.get("command")
    if command:
        parts.append(f"command={command}")
    reason = tests_meta.get("reason") or tests_meta.get("error")
    if reason:
        parts.append(f"reason={reason}")
    exit_code = tests_meta.get("exit_code")
    if exit_code is not None:
        parts.append(f"exit_code={exit_code}")
    timeout = tests_meta.get("timeout_seconds")
    if timeout is not None:
        parts.append(f"timeout_seconds={timeout}")
    print("; ".join(parts))
    print(f"Tests passed: {result.tests_passed}")

    if status == "ran":
        stdout = str(tests_meta.get("stdout") or "")
        stderr = str(tests_meta.get("stderr") or "")
        if stdout.strip():
            print("Tests stdout:")
            print(_truncate_text(stdout))
        if stderr.strip():
            print("Tests stderr:", file=sys.stderr)
            print(_truncate_text(stderr), file=sys.stderr)


def _tests_warning(tests_meta: object, tests_passed: bool | None) -> str | None:
    if not isinstance(tests_meta, dict):
        return "Tests status unknown; no metadata recorded."

    status = str(tests_meta.get("status", "unknown"))
    command = tests_meta.get("command")
    exit_code = tests_meta.get("exit_code")
    timeout = tests_meta.get("timeout_seconds")
    if status == "not_configured":
        return "Tests not configured; configure tests.default_command."
    if status == "apply_failed":
        return "Tests skipped because apply failed."
    if status == "command_not_found":
        return f"Tests command not found: {command or '<unknown>'}"
    if status == "timed_out":
        return f"Tests timed out after {timeout or '?'} seconds."
    if status == "skipped":
        return "Tests skipped."
    if status == "ran" and (
        tests_passed is False or (exit_code is not None and exit_code != 0)
    ):
        return f"Tests failed (exit_code={exit_code})."
    return None


def _print_ingest_summary(
    plan_id: str,
    artifact_path: Path,
    result: ExecutionResult,
    tests_status: str,
    diff_stats: tuple[int, int],
    suggestions_ingested: int,
) -> None:
    added, removed = diff_stats
    print(f"Ingested artifact: {artifact_path}")
    print(f"Plan: {plan_id}")
    print(f"Apply success: {result.success}")
    print(f"Tests status: {tests_status}; tests_passed={result.tests_passed}")
    if added or removed:
        print(f"Diff stat: +{added} / -{removed}")
    else:
        print("Diff stat: none")
    if suggestions_ingested:
        print(f"Ingested suggestions: {suggestions_ingested}")


def _truncate_text(text: str, limit: int = 400) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
