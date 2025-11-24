## Why
Codex `/cleanup-advanced` can return JSON suggestions, but ai-clean cannot ingest them; findings stay stale and users lose the advanced recommendations.

## What Changes
- Extend ingest to accept a suggestions array (from `/cleanup-advanced`) behind a flag and map valid entries into `Finding` objects.
- Enforce guardrails: paths must match the provided payload/selected files, line ranges within snippets, limits respected, and reject mixed/malformed suggestions.
- Persist accepted suggestions to findings JSON for later planning; surface clear errors when suggestions are invalid.

## Impact
- Affected specs: ingest-cleanup-advanced-suggestions
- Affected code: ingest command module, findings persistence helper, optional config for output file
- Docs/tests: add coverage and usage docs for the suggestions flag
