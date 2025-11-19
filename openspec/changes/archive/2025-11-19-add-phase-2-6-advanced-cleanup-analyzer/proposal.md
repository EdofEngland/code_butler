## Why
Let Codex suggest small, advisory cleanups based on curated context.

## What Changes
- Feed curated files/snippets plus existing findings into a constrained Codex prompt focused on small cleanups.
- Parse structured suggestions into advanced_cleanup findings with descriptions, locations, and metadata.
- Limit number of suggestions and scope per run; treat outputs as advisory.

## Impact
- Captures Codex insights while keeping scope bounded and review-friendly.
- Advanced findings stay advisory to avoid unintended auto-apply.
