"""Shared type aliases for ai-clean interfaces."""

from __future__ import annotations

from typing import Any, Union

StructuredReview = Union[dict[str, Any], str]

__all__ = ["StructuredReview"]
