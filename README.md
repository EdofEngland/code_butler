# ai-clean

ai-clean is a ButlerSpec-governed cleanup assistant that keeps Codex as the
executor while persisting every plan/spec/result on disk. The Phase 1 milestone
focuses on wiring up the `/plan → spec → apply` loop outlined in
[`docs/butlerspec_plan.md#phase-1-system-sketch`](docs/butlerspec_plan.md#phase-1-system-sketch).

## Command overview

Each CLI entrypoint exists today as a placeholder so future phases can fill in
real logic without changing the surface area:

- `/analyze` – scan a repository and emit `Finding` objects ready for planning.
- `/clean` – execute previously approved cleanup plans.
- `/annotate` – generate docstring or documentation improvements.
- `/organize` – suggest file moves or project structure fixes.
- `/cleanup-advanced` – run Codex-powered deep cleanup workflows.
- `/plan` – author a ButlerSpec plan for a specific file or finding.
- `/apply` – apply a ButlerSpec plan using Codex as the executor.
- `/changes-review` – review executed plans, summarize results, and capture risks.

Run `python -m ai_clean.cli --help` (or `ai-clean --help` after
`pip install -e .`) to view the current command roster.

### Analyzer CLI usage

Run `ai-clean analyze` to execute all analyzers against a repository. Useful
flags:

- `--root PATH` (default `.`) – repository root to scan.
- `--config FILE` – optional configuration file override.
- `--json` – emit JSON findings instead of a human-readable table.

Example:

```
$ ai-clean analyze --root src --config ai-clean.toml
dup-1a2b3c | duplicate_block | Found 2 duplicate windows starting with 'value = 1'
  - src/dup_a.py:1-2
  - src/dup_b.py:1-2
```

### Advanced cleanup workflow

The `/cleanup-advanced` command consumes findings from `/analyze --json`, passes
them through the Codex-powered analyzer, and prints advisory suggestions. Usage:

```
$ ai-clean analyze --root src --json > findings.json
$ ai-clean cleanup-advanced --root src --findings-json findings.json
adv-1f0a3c | advanced_cleanup | Consider extracting constant for API base URL
  - src/api_client.py:10-12
```

These suggestions are informational only; they help seed future `/plan` work and
never apply changes automatically.

### `/analyze` duplicate detection

Phase 2.1 wires `/analyze` to a duplicate code analyzer that walks Python files,
builds normalized sliding windows, and emits deterministic `duplicate_block`
findings. Windows default to five lines, comment-only slices are ignored, and
directories such as `.git`, `__pycache__`, and `.venv` are skipped. Each finding
records every affected file + line range along with metadata describing the
window size and normalized snippet.

Example output:

```
$ ai-clean /analyze
duplicate_block (dup-1a2b3c4d): Found 2 duplicate windows starting with 'def shared_block():'
  - alpha.py:1-5
  - beta.py:1-5
```

Configuration lives under `[analyzers.duplicate]` in `ai-clean.toml`:

- `window_size` (default `5`) – number of lines included in each sliding window.
- `min_occurrences` (default `2`) – minimum number of identical windows required
  before a finding is emitted.
- `ignore_dirs` (default `[".git", "__pycache__", ".venv"]`) – directory names
  excluded from traversal.

### Structure analyzer

The structure analyzer flags large files and long functions. Files exceeding
`max_file_lines` (default `400`) yield `large_file` findings with file-level
locations, while functions longer than `max_function_lines` (default `60`) produce
`long_function` findings covering the function span. A single file can generate
multiple findings when it contains several long functions.

Example output:

```
$ ai-clean /analyze
large_file (large-file-97b5dc42): File big_module.py has 812 lines (> 400)
  - big_module.py:1-812
long_function (long-func-11c0a32e): Function data_loader has 143 lines (> 60)
  - big_module.py:120-262
```

Configuration lives under `[analyzers.structure]` in `ai-clean.toml`:

- `max_file_lines` – file length threshold (default `400`).
- `max_function_lines` – function length threshold (default `60`).
- `ignore_dirs` – directories skipped during traversal (defaults are merged with
  the duplicate analyzer ignore list).

### Docstring analyzer

The docstring analyzer scans modules, classes, and functions for missing or weak
documentation. Modules without a top-level docstring and public symbols lacking
docstrings emit `missing_docstring` findings. Symbols with trivial docstrings
shorter than `min_docstring_length` or containing tokens such as `TODO` emit
`weak_docstring` findings. Private symbols (names starting with `_`) are ignored.

Example output:

```
$ ai-clean /analyze
missing_docstring (doc-missing_docstring-44a5c1d2): Module api/handler.py is missing a docstring
  - api/handler.py:1-1
weak_docstring (doc-weak_docstring-d201ac44): Function handler.process in api/handler.py contains a weak docstring marker
  - api/handler.py:42-88
```

Configure behavior under `[analyzers.docstring]` in `ai-clean.toml`:

- `min_docstring_length` (default `32`) – minimum characters before a docstring
  is considered substantive.
- `min_symbol_lines` (default `5`) – symbol size threshold used when
  `important_symbols_only = true` (shorter symbols are skipped entirely).
- `weak_markers` – tokens treated as weak docstrings regardless of length
  (defaults to `"todo"`, `"fixme"`, `"tbd"`).
- `important_symbols_only` (default `true`) – skip symbols smaller than
  `min_symbol_lines` to reduce noise.
- `ignore_dirs` – directories excluded from traversal.

### Organize analyzer

The organize analyzer suggests regrouping files that appear to share a topic
based on filename tokens, imports, and module docstrings. It emits
`organize_candidate` findings with conservative group sizes so future `/organize`
workflows can consider moving those files under a shared directory.

Example output:

```
$ ai-clean /analyze
organize_candidate (organize-api-01): Consider regrouping 2 files under "api/"
  - api_client.py:1-1
  - api_routes.py:1-1
```

Configuration lives under `[analyzers.organize]` in `ai-clean.toml`:

- `min_group_size` / `max_group_size` – enforce group bounds (defaults `2` and
  `5`).
- `max_groups` – cap the number of suggestions per run (default `5`).
- `ignore_dirs` – directories excluded from topic inference (defaults align with
  other analyzers).
