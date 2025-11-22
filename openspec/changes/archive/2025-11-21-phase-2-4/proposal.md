# Proposal: Phase 2.4 – Organize Seed Analyzer

## Why
This change is part of 2 – Analyzers and introduces Organize Seed Analyzer so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement an **organize-seed** analyzer to emit `organize_candidate` findings: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement an **organize-seed** analyzer to emit `organize_candidate` findings:

  - For each file, infer topic from:

    - File name,
    - Top-level imports,
    - Module docstring.
    - Deterministic heuristics:
      - Tokenize filename stem (split on `_`/`-`), lowercase, drop stopwords.
      - Collect first-segment import names and module docstring keywords (also tokenized/lowercased).
      - Weight signals equally; break ties by alphabetical topic label so identical repos yield the same topic choice.
      - Skip files without any meaningful signals to avoid noisy groupings.

  - Group files by rough responsibility (e.g., `logs`, `api`, `cli`, `db`).

- For each proposed group:

  - Emit `Finding`:

    - `category = "organize_candidate"`.
    - Description: suggested folder path + member files.
    - Locations: file paths only.

- Keep proposals small and conservative (2–5 files per finding).
- Configuration (`[analyzers.organize]`):
  - `min_group_size` / `max_group_size` (defaults 2 and 5) and `max_groups` (default 5) define how many files per finding and how many findings are emitted.
  - `ignore_dirs` inherits defaults from other analyzers to avoid vendor/generated code.
  - Validation enforces `2 <= min_group_size <= max_group_size <= 10` and raises deterministic errors otherwise.
- Assumptions / Non-goals:
  - Analyzer only suggests groupings; it does not move files or rename modules.
  - Files already inside stable directories (e.g., `tests/`, `migrations/`) are skipped unless explicitly included.
  - Ambiguous files (conflicting signals) remain ungrouped to keep proposals conservative.

## Impact / Risks
- Unlocks later phases that depend on Organize Seed Analyzer.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
