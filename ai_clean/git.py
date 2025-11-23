"""Git helpers for branch management and diff summaries."""

from __future__ import annotations

import subprocess
from typing import List


def _run_git(
    args: List[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a git command with text output and optional checking."""

    return subprocess.run(
        ["git", *args],
        check=check,
        capture_output=True,
        text=True,
    )


def current_branch() -> str:
    """Return the currently checked-out branch name."""

    result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def ensure_on_refactor_branch(base_branch: str, refactor_branch: str) -> None:
    """Ensure the working tree is on the refactor branch, creating it if needed."""

    if current_branch() == refactor_branch:
        return

    _run_git(["fetch", "origin", base_branch])

    refactor_remote_exists = True
    try:
        _run_git(["fetch", "origin", refactor_branch])
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or "").lower()
        if "couldn't find remote ref" in message:
            refactor_remote_exists = False
        else:
            raise

    _run_git(["checkout", "-B", refactor_branch, f"origin/{base_branch}"])

    if refactor_remote_exists:
        _run_git(
            [
                "branch",
                "--set-upstream-to",
                f"origin/{refactor_branch}",
                refactor_branch,
            ]
        )


def get_diff_stat() -> str:
    """Return a git diff --stat summary for the working tree."""

    result = _run_git(["diff", "--stat"])
    return result.stdout.strip()


__all__ = ["current_branch", "ensure_on_refactor_branch", "get_diff_stat"]
