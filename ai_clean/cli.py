"""Placeholder CLI for ai-clean with enumerated subcommands."""

from __future__ import annotations

import argparse
from typing import Callable, Iterable, Tuple

from ai_clean.analyzers.orchestrator import analyze_repo, format_location_summary

CommandDef = Tuple[str, Iterable[str], str]


COMMANDS: Tuple[CommandDef, ...] = (
    ("analyze", ["/analyze"], "Scan a path and report findings."),
    ("clean", ["/clean"], "Guided cleanup flow for structural issues (placeholder)."),
    ("annotate", ["/annotate"], "Docstring-focused improvements (placeholder)."),
    ("organize", ["/organize"], "Suggest small file movements (placeholder)."),
    (
        "cleanup-advanced",
        ["/cleanup-advanced"],
        "Advisory advanced cleanups powered by Codex (placeholder).",
    ),
    ("plan", ["/plan"], "Generate a plan for a finding (placeholder)."),
    ("apply", ["/apply"], "Apply a stored plan (placeholder)."),
    (
        "changes-review",
        ["/changes-review"],
        "Summarize changes and risks after apply (placeholder).",
    ),
)


def _placeholder_handler(command_name: str) -> Callable[[argparse.Namespace], int]:
    def handler(_: argparse.Namespace) -> int:
        print(
            f"Command '{command_name}' is a placeholder; no actions are performed yet."
        )
        return 0

    return handler


def _analyze_handler(args: argparse.Namespace) -> int:
    root = args.path
    findings = analyze_repo(root)
    if not findings:
        print("No findings.")
        return 0

    for finding in findings:
        loc_summary = "; ".join(
            format_location_summary(loc) for loc in finding.locations
        )
        print(
            f"[{finding.id}] {finding.category} - {finding.description} :: "
            f"{loc_summary}"
        )
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
            sub.set_defaults(func=_analyze_handler)
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


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
