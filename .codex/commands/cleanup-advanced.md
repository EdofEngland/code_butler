# /cleanup-advanced — Generate advanced cleanup suggestions

Purpose: produce bounded, advisory-only cleanup suggestions from a provided findings/snippets payload. This command does NOT edit files.

Invocation: `codex /cleanup-advanced <PAYLOAD_PATH>`
- Arguments: `<PAYLOAD_PATH>` MUST be a JSON file. Prefer an absolute path; if using a relative path, run from the repository root that contains the referenced files.
- Auth/environment: handled by Codex CLI. Do not request credentials or open browsers.

Expected payload (JSON):
```json
{
  "findings": [
    {
      "id": "dup-123",
      "description": "Tighten helper",
      "path": "src/app.py",
      "start_line": 10,
      "end_line": 18,
      "change_type": "refine_function"
    }
  ],
  "snippets": [
    {
      "path": "src/app.py",
      "content": "<file excerpt>",
      "start_line": 1,
      "end_line": 40
    }
  ],
  "limits": {
    "max_files": 3,
    "max_suggestions": 5,
    "max_snippet_lines": 40
  },
  "model": "gpt-4o-mini",
  "prompt_hash": "<hash to echo back>"
}
```

Guardrails:
- Do NOT propose edits outside the provided file paths/spans. No new files, renames, signature changes, or architecture rewrites.
- Respect limits: reject if findings/snippets exceed `limits.max_files` or `limits.max_suggestions`, or if snippets exceed `limits.max_snippet_lines`.
- No code fences, no prose summaries; output MUST be JSON only.
- If payload is missing/invalid or limits are exceeded, respond with `Error: <reason>` and no JSON array.

Output contract:
- On success, emit a JSON array (and nothing else) of suggestions with fields:
  - `description`, `path`, `start_line`, `end_line`, `change_type`, `model`, `prompt_hash`
- Paths must stay within the provided findings/snippets; line ranges must fall within the provided spans.
- On failure, emit `Error: <reason>` (no JSON payload).

Sample success response:
```json
[
  {
    "description": "Extract repeated literal to constant",
    "path": "src/app.py",
    "start_line": 12,
    "end_line": 18,
    "change_type": "extract_constant",
    "model": "gpt-4o-mini",
    "prompt_hash": "<hash>"
  }
]
```
