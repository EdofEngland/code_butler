# Proposal: Phase 2.6 – Codex-Powered Advanced Cleanup Analyzer

## Why
This change is part of 2 – Analyzers and introduces Codex-Powered Advanced Cleanup Analyzer so the ButlerSpec-governed ai-clean workflow keeps momentum.
It focuses on Implement an **advanced cleanup analyzer** that uses Codex, but only to propose **small cleanup ideas**, not to apply them: while keeping Codex as the execution engine and ButlerSpec metadata as the authoritative plan.

## What Changes
- Implement an **advanced cleanup analyzer** that uses Codex, but only to propose **small cleanup ideas**, not to apply them:

  - Input:

    - Selected files/snippets.
    - Summary of existing findings.
    - Prompt template: “Suggest small, local cleanup changes only; no API redesigns, no API surface changes” plus injected snippets + prior findings.

  - Output (Codex):

    - Structured suggestions: description + target file + line ranges + suggested change type.
    - JSON payload for deterministic parsing: `[{"description": "...", "path": "...", "start_line": 10, "end_line": 20, "change_type": "extract_constant"}]`.

- Convert each suggestion into a `Finding`:

  - `category = "advanced_cleanup"`.
  - Detailed metadata (target file/lines, description, `change_type`, Codex model, prompt hash).

- Guardrails:

  - Hard limit on number of suggestions and files per run.
  - These findings stay advisory until turned into `CleanupPlan`s.
  - Reject suggestions tagged with disallowed change types (e.g., “refactor architecture”, “rewrite module”).
  - Log dropped suggestions and include reasons in metadata for traceability.

- Non-goals:
  - The analyzer never applies changes or modifies files.
  - It does not attempt to rewrite prompts based on Codex output; prompt tuning happens manually.
  - Suggestions are limited to the supplied snippets/files; it does not explore the entire repo automatically.

## Impact / Risks
- Unlocks later phases that depend on Codex-Powered Advanced Cleanup Analyzer.
- Reinforces ButlerSpec guardrails: one-plan-per-file, specs on disk, Codex apply pipeline.
- Scope stays limited to the tasks below; new needs require separate proposals.
