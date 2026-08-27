"""Deterministic aggregation and normalization helpers.

This module performs no repository access. It only:

* normalizes and compares full/short SHAs;
* computes the top-level status/decision from claim results;
* summarizes claim counts.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from .models import (
    ClaimResult,
    ClaimVerdict,
    ExecutionDecision,
    GroundingStatus,
)

_HEX_RE = re.compile(r"^[0-9a-f]+$")

# A short SHA must be at least this long to be accepted as an unambiguous
# prefix match. Values shorter than this are treated as ambiguous rather than
# silently matching (GA-007).
MIN_SHA_PREFIX = 7


def normalize_sha(value: str) -> str:
    """Lowercase and strip a SHA-like string. Does not validate length."""
    return (value or "").strip().lower()


def is_hex_sha(value: str) -> bool:
    v = normalize_sha(value)
    return bool(v) and bool(_HEX_RE.match(v)) and len(v) <= 40


class ShaComparison:
    """Result of comparing an expected (possibly short) SHA to an observed SHA."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"  # expected prefix too short to be trustworthy
    INVALID = "INVALID"  # not a hex SHA


def compare_sha(expected: str, observed: str) -> str:
    """Compare an expected SHA (full or short prefix) against an observed SHA.

    Returns one of the :class:`ShaComparison` constants. A short prefix shorter
    than :data:`MIN_SHA_PREFIX` is reported as ``AMBIGUOUS`` and must never be
    treated as a high-confidence proof of equality.
    """
    exp = normalize_sha(expected)
    obs = normalize_sha(observed)
    if not is_hex_sha(exp) or not is_hex_sha(obs):
        return ShaComparison.INVALID
    if len(exp) < MIN_SHA_PREFIX:
        return ShaComparison.AMBIGUOUS
    if len(exp) == len(obs):
        return ShaComparison.MATCH if exp == obs else ShaComparison.MISMATCH
    # Prefix comparison: expected is treated as a prefix of the full observed SHA.
    if len(exp) < len(obs):
        return ShaComparison.MATCH if obs.startswith(exp) else ShaComparison.MISMATCH
    # expected longer than observed -> observed cannot fully confirm it.
    return ShaComparison.MISMATCH


def summarize(results: List[ClaimResult]) -> dict:
    """Compute the summary counts block."""
    matched = sum(1 for r in results if r.verdict is ClaimVerdict.MATCH)
    mismatched = sum(1 for r in results if r.verdict is ClaimVerdict.MISMATCH)
    insufficient = sum(
        1 for r in results if r.verdict is ClaimVerdict.INSUFFICIENT_EVIDENCE
    )
    blocked = sum(1 for r in results if r.verdict is ClaimVerdict.BLOCKED)
    return {
        "checked": len(results),
        "matched": matched,
        "mismatched": mismatched,
        "insufficient": insufficient,
        "blocked": blocked,
    }


def material_divergences(results: List[ClaimResult]) -> List[str]:
    """Claim ids that are material AND mismatched."""
    return [
        r.claim_id
        for r in results
        if r.material and r.verdict is ClaimVerdict.MISMATCH
    ]


def blocked_checks(results: List[ClaimResult]) -> List[str]:
    """Claim ids whose evidence source failed (any materiality)."""
    return [r.claim_id for r in results if r.verdict is ClaimVerdict.BLOCKED]


def aggregate_status(
    results: List[ClaimResult],
) -> Tuple[GroundingStatus, ExecutionDecision]:
    """Deterministic aggregation (spec section 7).

    Precedence (material claims only drive STOP):

    1. any material MISMATCH        -> STALE / STOP
    2. any material BLOCKED         -> BLOCKED / STOP
    3. any material INSUFFICIENT    -> INSUFFICIENT_EVIDENCE / STOP
    4. otherwise                    -> MATCH / PROCEED

    Non-material divergences remain visible in the claim list but do not change
    a PROCEED decision.
    """
    has_material_mismatch = any(
        r.material and r.verdict is ClaimVerdict.MISMATCH for r in results
    )
    if has_material_mismatch:
        return GroundingStatus.STALE, ExecutionDecision.STOP

    has_material_blocked = any(
        r.material and r.verdict is ClaimVerdict.BLOCKED for r in results
    )
    if has_material_blocked:
        return GroundingStatus.BLOCKED, ExecutionDecision.STOP

    has_material_insufficient = any(
        r.material and r.verdict is ClaimVerdict.INSUFFICIENT_EVIDENCE
        for r in results
    )
    if has_material_insufficient:
        return GroundingStatus.INSUFFICIENT_EVIDENCE, ExecutionDecision.STOP

    return GroundingStatus.MATCH, ExecutionDecision.PROCEED
