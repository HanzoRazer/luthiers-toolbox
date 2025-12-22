"""
RMOS AI Domain Layer (Canonical)

Purpose:
- RMOS-specific AI logic (rosette candidate generators, coercion, constraints)
- Uses app/ai/* platform for transport/safety/observability
- Contains domain knowledge (rosette schemas, RMOS budgets, constraint profiles)

Architecture Boundary:
- app/ai/* = platform-only (transport, safety, cost, audit) - NO domain logic
- app/rmos/ai/* = RMOS domain AI logic - uses platform, owns rosette semantics

Migrated from: _experimental/ai_core/* (December 2025)
"""
from __future__ import annotations

from .generators import (
    make_candidate_generator_for_request,
    get_default_candidate_generator,
    CandidateGenerator,
)

from .coercion import (
    coerce_to_rosette_spec,
)

from .constraints import (
    constraints_from_context,
    RosetteGeneratorConstraints,
)

from .clients import (
    get_ai_client,
)

__all__ = [
    # Generators
    "make_candidate_generator_for_request",
    "get_default_candidate_generator",
    "CandidateGenerator",
    # Coercion
    "coerce_to_rosette_spec",
    # Constraints
    "constraints_from_context",
    "RosetteGeneratorConstraints",
    # Clients
    "get_ai_client",
]
