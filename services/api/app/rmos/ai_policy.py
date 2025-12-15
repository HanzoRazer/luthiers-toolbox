# services/api/app/rmos/ai_policy.py
"""
AI Policy Module - Global safety caps and policy validation.
Enforces system-wide limits on AI rosette generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .constraint_profiles import RosetteGeneratorConstraints


# ======================
# Global System Caps
# ======================

MAX_SYSTEM_RINGS: int = 12
MAX_SYSTEM_TOTAL_WIDTH_MM: float = 12.0
MAX_SYSTEM_ATTEMPTS: int = 200
MAX_SYSTEM_TIME_LIMIT_SECONDS: float = 60.0


# ======================
# Policy Error
# ======================

@dataclass
class PolicyViolationError(Exception):
    """Raised when a request violates global AI policy."""
    message: str
    
    def __str__(self) -> str:
        return self.message


# ======================
# Constraint Clamping
# ======================

def apply_global_policy_to_constraints(
    constraints: RosetteGeneratorConstraints,
) -> RosetteGeneratorConstraints:
    """
    Clamp a constraint profile to system-wide safety limits.
    
    Returns a new RosetteGeneratorConstraints with values clamped
    to never exceed global caps.
    """
    c = RosetteGeneratorConstraints(
        min_rings=constraints.min_rings,
        max_rings=constraints.max_rings,
        min_ring_width_mm=constraints.min_ring_width_mm,
        max_ring_width_mm=constraints.max_ring_width_mm,
        min_total_width_mm=constraints.min_total_width_mm,
        max_total_width_mm=constraints.max_total_width_mm,
        allow_mosaic=constraints.allow_mosaic,
        allow_segmented=constraints.allow_segmented,
        palette_key=constraints.palette_key,
        bias_simple=constraints.bias_simple,
    )

    # Clamp max_rings
    if c.max_rings > MAX_SYSTEM_RINGS:
        c.max_rings = MAX_SYSTEM_RINGS
    if c.min_rings > c.max_rings:
        c.min_rings = c.max_rings

    # Clamp total width
    if c.max_total_width_mm > MAX_SYSTEM_TOTAL_WIDTH_MM:
        c.max_total_width_mm = MAX_SYSTEM_TOTAL_WIDTH_MM
    if c.min_total_width_mm > c.max_total_width_mm:
        c.min_total_width_mm = c.max_total_width_mm

    return c


# ======================
# Request Validation
# ======================

def validate_request_against_policy(request) -> None:
    """
    Validate a ConstraintFirstRequest against global policy limits.

    Raises PolicyViolationError if something is clearly out-of-bounds.
    
    Args:
        request: A ConstraintFirstRequest-like object with search_budget attribute
        
    Raises:
        PolicyViolationError: If request exceeds system limits
    """
    budget = getattr(request, "search_budget", None)
    if budget is None:
        return  # No budget to validate
    
    max_attempts = getattr(budget, "max_attempts", 0)
    time_limit = getattr(budget, "time_limit_seconds", 0.0)

    if max_attempts > MAX_SYSTEM_ATTEMPTS:
        raise PolicyViolationError(
            f"max_attempts={max_attempts} exceeds system limit "
            f"MAX_SYSTEM_ATTEMPTS={MAX_SYSTEM_ATTEMPTS}"
        )

    if time_limit > MAX_SYSTEM_TIME_LIMIT_SECONDS:
        raise PolicyViolationError(
            f"time_limit_seconds={time_limit} exceeds system limit "
            f"MAX_SYSTEM_TIME_LIMIT_SECONDS={MAX_SYSTEM_TIME_LIMIT_SECONDS}"
        )


def clamp_budget_to_policy(budget) -> None:
    """
    Clamp a search budget's values to system limits in-place.
    
    This is a softer alternative to validate_request_against_policy
    that adjusts values instead of raising errors.
    """
    if budget is None:
        return
    
    if hasattr(budget, "max_attempts"):
        if budget.max_attempts > MAX_SYSTEM_ATTEMPTS:
            budget.max_attempts = MAX_SYSTEM_ATTEMPTS
    
    if hasattr(budget, "time_limit_seconds"):
        if budget.time_limit_seconds > MAX_SYSTEM_TIME_LIMIT_SECONDS:
            budget.time_limit_seconds = MAX_SYSTEM_TIME_LIMIT_SECONDS
