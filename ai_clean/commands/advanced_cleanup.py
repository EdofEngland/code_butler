"""Helpers for running the Codex-powered advanced cleanup analyzer (disabled)."""

from __future__ import annotations

from pathlib import Path

from ai_clean.models import Finding


def run_advanced_cleanup(
    root: Path, config_path: Path | None, findings_json: Path
) -> list[Finding]:
    raise RuntimeError(
        "Advanced cleanup is disabled: Codex integration requires a cleanup-advanced "
        "slash command. No Codex prompts were run. "
        f"Use 'codex /cleanup-advanced {findings_json.resolve()}' from Codex CLI."
    )


__all__ = ["run_advanced_cleanup"]
