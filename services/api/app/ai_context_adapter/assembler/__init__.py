# services/api/app/ai_context_adapter/assembler/__init__.py
"""Envelope assembler for AI context."""

from .default import build_context_envelope

__all__ = [
    "build_context_envelope",
]
