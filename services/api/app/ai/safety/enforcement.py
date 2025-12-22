"""
AI Safety Enforcement - Hard Stop Helpers

Provides the assert_allowed() function that all AI applications
must call before generation. Raises on RED level.
"""
from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

from .policy import (
    SafetyCategory,
    SafetyLevel,
    SafetyCheckResult,
    check_prompt_safety,
)

logger = logging.getLogger(__name__)


class SafetyViolationError(Exception):
    """
    Raised when a prompt violates safety policy.

    This exception should result in an HTTP 400 response.
    """

    def __init__(
        self,
        message: str,
        blocked_terms: list[str],
        category: SafetyCategory,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.blocked_terms = blocked_terms
        self.category = category
        self.request_id = request_id

    def to_dict(self) -> dict:
        return {
            "error": "safety_violation",
            "message": str(self),
            "blocked_terms": self.blocked_terms,
            "category": self.category.value,
            "request_id": self.request_id,
        }


def assert_allowed(
    prompt: str,
    category: Optional[SafetyCategory] = None,
    request_id: Optional[str] = None,
    strict: bool = True,
) -> SafetyCheckResult:
    """
    Assert that a prompt is allowed for AI generation.

    This is the main entry point for safety enforcement.
    All AI applications must call this before generation.

    Args:
        prompt: The user's prompt text
        category: Optional category override
        request_id: Optional request ID for logging
        strict: If True, raise on RED level. If False, just return result.

    Returns:
        SafetyCheckResult if allowed

    Raises:
        SafetyViolationError: If prompt is blocked (RED level) and strict=True
    """
    result = check_prompt_safety(prompt, category)

    # Log the check
    log_safety_check(result, request_id)

    # Enforce on RED
    if result.level == SafetyLevel.RED and strict:
        raise SafetyViolationError(
            message=f"Prompt blocked due to policy violation: {', '.join(result.blocked_terms_found)}",
            blocked_terms=result.blocked_terms_found,
            category=result.category,
            request_id=request_id,
        )

    return result


def log_safety_check(
    result: SafetyCheckResult,
    request_id: Optional[str] = None,
) -> None:
    """
    Log a safety check result for audit purposes.

    Args:
        result: The safety check result
        request_id: Optional request ID for correlation
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "level": result.level.value,
        "category": result.category.value,
        "is_allowed": result.is_allowed,
        "blocked_terms": result.blocked_terms_found,
        "warnings": result.warnings,
    }

    if result.level == SafetyLevel.RED:
        logger.warning(f"SAFETY_BLOCKED: {log_data}")
    elif result.level == SafetyLevel.YELLOW:
        logger.info(f"SAFETY_CAUTION: {log_data}")
    else:
        logger.debug(f"SAFETY_PASSED: {log_data}")
