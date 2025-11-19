"""Git-related helpers for CLI workflows."""

from __future__ import annotations

import subprocess
from typing import Sequence


class GitError(RuntimeError):
    """Wrap git command failures with stderr context."""


def _run_git(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        command = " ".join(args)
        raise GitError(
            f"git {command} failed with code {result.returncode}: " f"{result.stderr}"
        )
    return result


def ensure_on_refactor_branch(base_branch: str, refactor_branch: str) -> None:
    """Ensure the local repo is on the refactor branch synchronized with base."""
    current = _run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if current == refactor_branch:
        return

    _run_git(["fetch", "origin", base_branch])

    try:
        _run_git(["rev-parse", "--verify", refactor_branch])
    except GitError:
        _run_git(["branch", refactor_branch, f"origin/{base_branch}"])

    _run_git(["checkout", refactor_branch])
    _run_git(["merge", "--ff-only", f"origin/{base_branch}"])


def get_diff_stat(include_staged: bool = True) -> str:
    """Return git diff --stat output for working tree and optionally staged files."""
    parts = []
    working = _run_git(["diff", "--stat"]).stdout.strip()
    if working:
        parts.append(working)

    if include_staged:
        staged = _run_git(["diff", "--stat", "--cached"]).stdout.strip()
        if staged:
            parts.append(staged)

    summary = "\n".join(parts).strip()
    if not summary:
        summary = "(no changes)"
    return f"Changes:\n{summary}"


__all__ = ["ensure_on_refactor_branch", "get_diff_stat", "GitError"]
