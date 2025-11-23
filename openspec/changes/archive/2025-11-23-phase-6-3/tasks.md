## 1. Diff summary helper

- [x] 1.1 Add `get_diff_stat() -> str` to `ai_clean/git.py` (or companion module) that runs `git diff --stat` via the shared `_run_git` wrapper, using `capture_output=True` and `text=True`.
- [x] 1.2 Trim trailing whitespace/newlines from the returned stdout; return an empty string when there is no diff (exit code 0 with empty output).
- [x] 1.3 Propagate non-zero git errors (e.g., repository missing) without retries so callers can surface them.

## 2. Tests

- [x] 2.1 Add a unit test (e.g., `tests/test_git.py`) that monkeypatches subprocess to return a fake diff stat and asserts the helper returns the cleaned string.
- [x] 2.2 Add a test that when stdout is empty the helper returns `""` but does not raise.
- [x] 2.3 Add a test that a non-zero return code bubbles up as `subprocess.CalledProcessError`.
