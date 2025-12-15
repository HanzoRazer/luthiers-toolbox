# services/api/app/ai_core/__init__.py
"""
AI Core Package - Constraint-aware rosette generation and safety utilities.
"""

from .generator_constraints import (
    RosetteGeneratorConstraints,
    constraints_from_context,
)

from .safety import coerce_to_rosette_spec

from .generators import (
    get_default_candidate_generator,
    make_candidate_generator_for_request,
)

__all__ = [
    "RosetteGeneratorConstraints",
    "constraints_from_context",
    "coerce_to_rosette_spec",
    "get_default_candidate_generator",
    "make_candidate_generator_for_request",
]
