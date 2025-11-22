# Proposal: Phase 2.3 – Docstring Analyzer

## Why
This change is part of 2 – Analyzers and introduces Docstring Analyzer so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement a **doc analyzer** to support `/annotate`: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement a **doc analyzer** to support `/annotate`:

  - For each module:

    - Missing or empty module docstring → `missing_docstring` finding.
  - For each public class/function (no leading `_`):

    - Missing or trivial docstring → `missing_docstring` or `weak_docstring`.

- Each issue becomes a `Finding`:

  - Category as above.
  - Description: symbol name, path, short context.
  - Locations: definition line(s).

- Configuration (`[analyzers.docstring]` in `ai-clean.toml`):
  - `min_docstring_length` (default 32 chars) and `min_symbol_lines` (default 5 lines) – positive integers validated at load time.
  - `weak_markers`: list of tokens (e.g., `"TODO"`, `"fixme"`, `"tbd"`) treated as weak docstrings even if longer than the min length.
  - `ignore_dirs`: directory names to skip (inherits defaults from other analyzers).
  - `important_symbols_only`: boolean toggle; when true, only symbols with `lines_of_code >= min_symbol_lines` are analyzed to reduce noise.
  - Validation emits deterministic `ValueError`s for zero/negative thresholds or malformed marker lists.

- Optional: consider only “important” functions (e.g., above a size threshold) for v0 via the `important_symbols_only` flag.

- Assumptions / Non-goals:
  - Analyzer ignores private symbols (names starting with `_`) and generated/vendor directories listed in `ignore_dirs`.
  - Docstring quality checks focus on presence/length/marker heuristics, not style-guide enforcement or content semantics.

## Impact / Risks
- Unlocks later phases that depend on Docstring Analyzer.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
