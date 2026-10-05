"""Versioned test policy for the advisory screening gate.

``max_test_removal_mm`` and ``min_test_remaining_thickness_mm`` are Phase I
test-policy thresholds only. These values are not validated production
engineering limits and carry no manufacturing authority. A number such as
0.6 may appear only when a test constructs a policy; it is not a constant
of the gate.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.physical_engineering.errors import ValidatorConfigurationError
from app.physical_engineering.evidence import is_finite_number, text_token


@dataclass(frozen=True)
class ValidationPolicyV1:
    """Mandatory and explicit. The gate supplies no numeric defaults."""

    policy_id: str
    policy_version: str
    max_test_removal_mm: float
    min_test_remaining_thickness_mm: float

    def __post_init__(self):
        if not text_token(self.policy_id) or not text_token(self.policy_version):
            raise ValidatorConfigurationError("validation policy identity is required")
        if not is_finite_number(self.max_test_removal_mm) or self.max_test_removal_mm <= 0:
            raise ValidatorConfigurationError(
                "max_test_removal_mm must be a finite number greater than zero"
            )
        if (
            not is_finite_number(self.min_test_remaining_thickness_mm)
            or self.min_test_remaining_thickness_mm < 0
        ):
            raise ValidatorConfigurationError(
                "min_test_remaining_thickness_mm must be a finite number that is not negative"
            )
