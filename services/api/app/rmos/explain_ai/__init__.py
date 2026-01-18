"""
Phase 5 — AI-Assisted Explanation (Advisory Only)

This module provides deterministic (and optionally LLM-backed) explanations
for run artifacts. All output is advisory-only and never changes the
authoritative feasibility/decision.
"""

from .engine import generate_assistant_explanation
from .schemas import AssistantExplanation, AssistantExplanationBasedOn

__all__ = [
    "generate_assistant_explanation",
    "AssistantExplanation",
    "AssistantExplanationBasedOn",
]
