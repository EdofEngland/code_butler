"""Helpers for running the Codex-powered advanced cleanup analyzer."""

from __future__ import annotations

import json
from pathlib import Path

from ai_clean.analyzers.advanced import collect_advanced_cleanup_ideas
from ai_clean.config import load_config
from ai_clean.factories import get_codex_prompt_runner
from ai_clean.models import Finding


def run_advanced_cleanup(
    root: Path, config_path: Path | None, findings_json: Path
) -> list[Finding]:
    config = load_config(config_path)
    runner = get_codex_prompt_runner(config)
    findings = _load_findings(findings_json)
    return collect_advanced_cleanup_ideas(root, findings, config, runner)


def _load_findings(path: Path) -> list[Finding]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):  # pragma: no cover - defensive
        raise ValueError("Findings JSON must be an array of Finding objects")
    return [Finding.model_validate(item) for item in payload]


__all__ = ["run_advanced_cleanup"]
