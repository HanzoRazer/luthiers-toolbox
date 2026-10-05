"""Versioned test policy for the advisory screening gate.

``max_test_removal_mm`` and ``min_test_remaining_thickness_mm`` are thresholds
for this gate's tests. They are not validated physical limits and they have
no production engineering authority. A number such as 0.6 may appear only when
a test constructs a policy; it is not a constant of the gate.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationPolicyV1:
    """Mandatory, versioned, and explicit. The gate supplies no numeric defaults."""

    policy_id: str
    policy_version: str
    max_test_removal_mm: float
    min_test_remaining_thickness_mm: float
    required_evidence_kinds: tuple[str, ...]
