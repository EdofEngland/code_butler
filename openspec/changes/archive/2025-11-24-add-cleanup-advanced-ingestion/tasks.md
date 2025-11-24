## 1. CLI flag and parsing
- [x] 1.1 Add `--update-findings` (or similar) to ingest to opt into suggestions handling.
- [x] 1.2 Parse suggestions array from the artifact when the flag is set; ignore if not present or flag absent.

## 2. Validation and mapping
- [x] 2.1 Validate each suggestion against the `/cleanup-advanced` schema (description, path, start_line, end_line, change_type, model, prompt_hash).
- [x] 2.2 Enforce path/line constraints: paths must come from the payload/selected files; line ranges within snippet bounds; respect max suggestions/files limits.
- [x] 2.3 Reject mixed spec payloads or malformed/extra fields with clear errors.
- [x] 2.4 Convert accepted suggestions into `Finding` objects with analyzer/metadata annotations.

## 3. Persistence and docs/tests
- [x] 3.1 Persist accepted findings to the chosen findings JSON (existing or `findings-ingested.json`), without dropping preexisting findings unless requested.
- [x] 3.2 Add tests for valid/invalid suggestions ingestion and path/limit enforcement.
- [x] 3.3 Document the flag, expected payload, and how ingested suggestions flow into planning.
