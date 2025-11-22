## Context
- Phase 2.1 introduces ai-clean’s first analyzer module. The analyzer reads Python source, normalizes sliding windows, and emits ButlerSpec findings.
- Results must be deterministic so later phases (planning/spec generation) can reliably reference finding IDs and ranges.
- Analyzer thresholds are configuration-driven to match ButlerSpec’s “one plan per file” governance and allow operators to tune behavior without code changes.

## Goals / Non-Goals
- Goals:
  - Define how duplicate detection windows are produced, normalized, and hashed.
  - Describe deterministic ordering + ID generation so findings remain stable across runs.
  - Record where analyzer settings originate in config parsing.
- Non-Goals:
  - Designing orchestrator wiring or other analyzers (covered in later phases).
  - Describing Codex execution, CLI wiring, or review flows.

## Decisions
1. **Analyzer module layout**
   - Create `ai_clean/analyzers` with `duplicate.py` to host the core logic.
   - Export `find_duplicate_blocks` via `ai_clean/analyzers/__init__.py` for reuse by future orchestrator work.
2. **Window normalization + hashing**
   - Use a configurable fixed window (`settings.window_size`) with line-based sliding.
   - Normalize each window by `textwrap.dedent`, stripping trailing whitespace and discarding fully blank/comment-only windows.
   - Generate deterministic IDs via `sha1(normalized_text).hexdigest()[:8]` to keep IDs short yet unique enough for local repos.
3. **Deterministic ordering**
   - Collect windows sorted by `(relative_path, start_line)` before grouping.
   - Sort group locations lexicographically before emitting findings and ensure findings are yielded in stable order.
4. **Configuration sourcing**
   - Introduce `DuplicateAnalyzerConfig` under `AiCleanConfig.analyzers.duplicate`.
   - Keys: `window_size`, `min_occurrences`, `ignore_dirs`.
   - `ignore_dirs` defaults to `(".git", "__pycache__", ".venv")` to avoid noisy vendor caches.

## Risks / Trade-offs
- **Risk:** SHA1 collisions in extremely large repos.
  - *Mitigation:* include metadata preview + normalized text snippet; collisions would still produce identical findings.
- **Risk:** Sliding windows may skip semantically meaningful duplicates if they cross logical boundaries.
  - *Mitigation:* keep window size configurable and document defaults for tuning.
- **Risk:** Config parsing adds runtime coupling between analyzers and loader.
  - *Mitigation:* isolate config dataclasses so other modules can reuse them.

## Migration / Follow-ups
- Later phases should reference this design when wiring analyzers into `/analyze` and ensure orchestrator respects the deterministic ordering rules defined above.
