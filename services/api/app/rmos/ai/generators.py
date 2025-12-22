"""
RMOS Candidate Generators (Canonical)

These functions implement the RMOS generator factory pattern:
    make_candidate_generator_for_request(...) -> CandidateGenerator(callable)

This is DOMAIN logic (RMOS-specific), not platform logic.
The generator factory returns a function that can be called repeatedly
to generate candidate rosette designs.

Migrated from: _experimental/ai_core/generators.py (December 2025)
"""

from __future__ import annotations

from typing import Callable, Optional

from .clients import get_ai_client
from .coercion import coerce_to_rosette_spec
from .constraints import constraints_from_context, RosetteGeneratorConstraints
from .structured_generator import generate_constrained_candidate

# RMOS contracts
try:
    from app.rmos.api_contracts import RosetteParamSpec, RmosContext
except (ImportError, AttributeError, ModuleNotFoundError):
    from pydantic import BaseModel

    class RosetteParamSpec(BaseModel):  # type: ignore
        version: str = "1.0"
        rings: list = []
        notes: str = ""

    class RmosContext(BaseModel):  # type: ignore
        material_id: Optional[str] = None
        tool_id: Optional[str] = None
        machine_profile_id: Optional[str] = None

try:
    from app.rmos.models import SearchBudgetSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from pydantic import BaseModel

    class SearchBudgetSpec(BaseModel):  # type: ignore
        max_attempts: int = 50
        time_limit_seconds: float = 30.0
        min_feasibility_score: float = 0.0
        stop_on_first_green: bool = True
        deterministic: bool = True


# Type alias for candidate generators
CandidateGenerator = Callable[[Optional[RosetteParamSpec], int], RosetteParamSpec]


def get_default_candidate_generator() -> CandidateGenerator:
    """
    Returns a simple generator function compatible with CandidateGenerator.

    This version is a backward-compatible stub that returns the previous
    design unchanged, or a minimal fallback design if none exists.
    """
    ai_client = get_ai_client()
    _ = ai_client  # Reserved for future AI-hybrid logic

    def generator(prev: Optional[RosetteParamSpec], attempt: int) -> RosetteParamSpec:
        if prev is not None:
            return prev

        raw = {
            "version": "1.0",
            "rings": [],
            "notes": "Fallback candidate from default generator.",
        }
        return coerce_to_rosette_spec(raw)

    return generator


def make_candidate_generator_for_request(
    *,
    ctx: RmosContext,
    budget: SearchBudgetSpec,
) -> CandidateGenerator:
    """
    Factory that returns a CandidateGenerator bound to a specific RMOS
    context + search budget, using the constraint-aware generator.

    This is the production entry point for AI search loops.
    
    Returns:
        A generator function: (prev_design, attempt_index) -> new_design
        
    Note:
        This implements the RMOS generator factory pattern. It returns
        a FUNCTION that can be called multiple times, not a single result.
        Do NOT replace this with a simple generate_json() call.
    """
    constraints = constraints_from_context(ctx)

    # Apply global policy caps if available
    try:
        from app.rmos.ai_policy import apply_global_policy_to_constraints
        constraints = apply_global_policy_to_constraints(constraints)
    except (ImportError, AttributeError, ModuleNotFoundError):
        pass  # Policy module not available, use unclamped constraints

    def generator(prev: Optional[RosetteParamSpec], attempt: int) -> RosetteParamSpec:
        return generate_constrained_candidate(
            prev_design=prev,
            constraints=constraints,
            budget=budget,
            attempt_index=attempt,
        )

    return generator


__all__ = [
    "CandidateGenerator",
    "get_default_candidate_generator",
    "make_candidate_generator_for_request",
]
