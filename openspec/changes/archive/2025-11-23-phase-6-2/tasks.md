## 1. Git branch helper

- [x] 1.1 Create `ai_clean/git.py` with a private `_run_git(args: list[str]) -> subprocess.CompletedProcess` wrapper that runs `git` commands with `check=True` and surfaces stderr on failure.
- [x] 1.2 Implement `current_branch() -> str` using `_run_git(["rev-parse", "--abbrev-ref", "HEAD"])`.
- [x] 1.3 Implement `ensure_on_refactor_branch(base_branch: str, refactor_branch: str)`:
  - [x] 1.3.1 If `current_branch()` matches `refactor_branch`, return immediately.
  - [x] 1.3.2 Otherwise run `git fetch origin {base_branch}` and `git fetch origin {refactor_branch}` (ignore if missing).
  - [x] 1.3.3 Create or fast-forward a local `refactor_branch` from `origin/{base_branch}` via `git checkout -B {refactor_branch} origin/{base_branch}`.
  - [x] 1.3.4 Set upstream `git branch --set-upstream-to=origin/{refactor_branch} {refactor_branch}` when the remote exists; surface conflicts/errors without retries.
- [x] 1.4 Do not commit or merge; let failures (non-zero git return codes) propagate.

## 2. Tests

- [x] 2.1 Add unit tests (e.g., `tests/test_git.py`) that monkeypatch `subprocess.run` to assert the command sequence for each branch state: already on refactor branch, branch missing, and fast-forward creation.
- [x] 2.2 Add a test that a failing git command raises `subprocess.CalledProcessError` and does not swallow stderr.
