"""Spec backend factory that instantiates configured backends."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

from ai_clean.interfaces import SpecBackend
from ai_clean.spec_backends.openspec import OpenSpecBackend

if TYPE_CHECKING:  # pragma: no cover - only used for hints
    from ai_clean.config import AiCleanConfig

SUPPORTED_SPEC_BACKENDS: Dict[str, Type[SpecBackend]] = {
    "openspec": OpenSpecBackend,
}


def build_spec_backend(config: "AiCleanConfig") -> SpecBackend:
    """Instantiate the configured SpecBackend based on ai-clean.toml settings."""
    backend_type = (config.spec_backend.type or "").strip().lower()
    if not backend_type:
        raise ValueError("spec_backend.type must be set in ai-clean.toml")

    backend_cls = SUPPORTED_SPEC_BACKENDS.get(backend_type)
    if backend_cls is None:
        allowed = ", ".join(sorted(SUPPORTED_SPEC_BACKENDS))
        raise ValueError(
            f"Unsupported spec backend '{backend_type}'. Allowed values: {allowed}"
        )

    backend = backend_cls()
    if not isinstance(backend, SpecBackend):
        raise TypeError(
            f"Backend '{backend_type}' does not implement SpecBackend correctly"
        )
    return backend


__all__ = ["build_spec_backend", "SUPPORTED_SPEC_BACKENDS"]
