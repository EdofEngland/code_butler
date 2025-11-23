from __future__ import annotations

import subprocess

import pytest

from ai_clean import git


class _Result:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def test_ensure_on_refactor_branch_noop_when_already_on_target(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return _Result(stdout="refactor\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    git.ensure_on_refactor_branch("main", "refactor")

    assert calls == [["git", "rev-parse", "--abbrev-ref", "HEAD"]]


def test_ensure_on_refactor_branch_creates_from_base(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1:3] == ["rev-parse", "--abbrev-ref"]:
            return _Result(stdout="main\n")
        if cmd[1:3] == ["fetch", "origin"] and cmd[3] == "refactor":
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=cmd,
                output="",
                stderr="fatal: couldn't find remote ref refactor\n",
            )
        return _Result(stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    git.ensure_on_refactor_branch("main", "refactor")

    assert calls == [
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        ["git", "fetch", "origin", "main"],
        ["git", "fetch", "origin", "refactor"],
        ["git", "checkout", "-B", "refactor", "origin/main"],
    ]


def test_ensure_on_refactor_branch_sets_upstream_when_remote_exists(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1:3] == ["rev-parse", "--abbrev-ref"]:
            return _Result(stdout="main\n")
        return _Result(stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    git.ensure_on_refactor_branch("main", "refactor")

    assert calls == [
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        ["git", "fetch", "origin", "main"],
        ["git", "fetch", "origin", "refactor"],
        ["git", "checkout", "-B", "refactor", "origin/main"],
        [
            "git",
            "branch",
            "--set-upstream-to",
            "origin/refactor",
            "refactor",
        ],
    ]


def test_run_git_propagates_failures(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=2, cmd=cmd, stderr="err")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        git._run_git(["status"])


def test_ensure_on_refactor_branch_raises_on_fetch_error(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1:3] == ["rev-parse", "--abbrev-ref"]:
            return _Result(stdout="main\n")
        if cmd[1:3] == ["fetch", "origin"] and cmd[3] == "refactor":
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=cmd,
                output="",
                stderr="fatal: connection refused",
            )
        return _Result(stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        git.ensure_on_refactor_branch("main", "refactor")
    assert calls[:2] == [
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        ["git", "fetch", "origin", "main"],
    ]


def test_get_diff_stat_returns_cleaned_output(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == ["git", "diff", "--stat"]
        return _Result(stdout=" file.py | 2 +- \n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert git.get_diff_stat() == "file.py | 2 +-"


def test_get_diff_stat_empty_output(monkeypatch):
    def fake_run(cmd, **kwargs):
        return _Result(stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert git.get_diff_stat() == ""


def test_get_diff_stat_propagates_failure(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="err")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        git.get_diff_stat()
