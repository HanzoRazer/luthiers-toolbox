"""
AI Safety Layer - Policy Enforcement

Centralized safety checks for all AI operations.
All AI applications must call these checks before generation.

INVARIANT: Safety enforcement is centralized here.
Domain apps call: ai.safety.assert_allowed()
"""

from .policy import (
    SafetyCategory,
    SafetyLevel,
    BLOCKED_TERMS,
    check_prompt_safety,
    is_category_allowed,
)

from .enforcement import (
    assert_allowed,
    SafetyViolationError,
    log_safety_check,
)

__all__ = [
    # Policy
    "SafetyCategory",
    "SafetyLevel",
    "BLOCKED_TERMS",
    "check_prompt_safety",
    "is_category_allowed",
    # Enforcement
    "assert_allowed",
    "SafetyViolationError",
    "log_safety_check",
]
