"""Codex prompt runner interfaces used by advanced analyzers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class PromptAttachment:
    path: Path
    content: str


class CodexPromptRunner(Protocol):
    def run(self, prompt: str, attachments: Sequence[PromptAttachment]) -> str:
        """Execute the prompt and return Codex output as text."""


__all__ = ["CodexPromptRunner", "PromptAttachment"]
