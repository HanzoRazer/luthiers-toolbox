"""
RMOS Feasibility Authority Boundary — RMOS-CONVERGE-001A

One explicit boundary between client-supplied CAM *intent* and the
server-computed safety *decision*.

Governance decisions embodied here
----------------------------------
D1  The server owns safety decisions. A client payload may describe
    geometry, tool, material, machine and CAM intent. It may NOT carry an
    authoritative ``feasibility`` / ``safety`` / ``decision`` /
    ``risk_level`` / ``export_allowed`` that survives into the production
    decision path.
D2  There is no production test hook. Injected feasibility is a test-only
    concern and must be supplied by dependency injection or a fixture, not
    by a request field.
D3  Inability to evaluate is never GREEN. A missing engine yields
    ``UNKNOWN``; a failing engine yields ``ERROR``. Both are blocking under
    ``SafetyPolicy``'s default posture (``RMOS_TREAT_UNKNOWN_AS_RED``).
D4  Where no evaluator's input contract actually matches a CAM mode, fail
    closed with a machine-readable reason rather than inventing substitute
    physics to make the path green.

Two independent guarantees make the boundary provable:

1. ``sanitize_feasibility_input`` removes every authority-shaped key that
   ``SafetyPolicy.extract_safety_decision`` is able to read.
2. Every engine result is *constructed* by the server. No engine echoes a
   caller-supplied ``safety`` block.

Rejected client keys are not discarded silently — they are preserved under
``client_declared_non_authoritative`` for diagnostics, where no consumer can
mistake them for a decision.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Keys a client may not use to assert manufacturing authority.
#
# This list is not decorative: it is exactly the set of locations
# ``SafetyPolicy.extract_safety_decision`` will read a risk level from
# (flat ``risk_level``; nested ``decision.*``; nested ``safety.*``), plus
# ``feasibility`` (the whole payload) and ``export_allowed`` (D1).
AUTHORITY_KEYS: Tuple[str, ...] = (
    "feasibility",
    "safety",
    "decision",
    "risk_level",
    "export_allowed",
)

# Diagnostics bag for rejected client assertions. Deliberately named so that
# no downstream reader can mistake it for a decision.
NON_AUTHORITATIVE_KEY = "client_declared_non_authoritative"

# Machine-readable reason codes.
ENGINE_UNAVAILABLE = "FEASIBILITY_ENGINE_UNAVAILABLE"
ENGINE_ERROR = "FEASIBILITY_ENGINE_ERROR"


def sanitize_feasibility_input(
    payload: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Strip client-supplied authority from a feasibility request.

    Returns ``(sanitized_payload, rejected_keys)``.

    The caller's object is never mutated: a shallow copy is returned. Any
    rejected key/value pair is preserved under ``NON_AUTHORITATIVE_KEY`` so
    a diagnostic trail survives without conferring authority.

    Legitimate design/CAM parameters pass through untouched.
    """
    if not isinstance(payload, dict):
        return {}, []

    sanitized: Dict[str, Any] = dict(payload)
    rejected: Dict[str, Any] = {}

    for key in AUTHORITY_KEYS:
        if key in sanitized:
            rejected[key] = sanitized.pop(key)

    # A caller must not be able to pre-seed the diagnostics bag either.
    sanitized.pop(NON_AUTHORITATIVE_KEY, None)

    if rejected:
        sanitized[NON_AUTHORITATIVE_KEY] = rejected

    return sanitized, sorted(rejected.keys())


def _non_authorizing_result(
    *,
    mode: str,
    tool_id: str,
    context: Optional[str],
    risk_level: str,
    code: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a server-owned result that cannot authorize manufacturing."""
    merged: Dict[str, Any] = {"context": context, "code": code}
    if details:
        merged.update(details)
    return {
        "mode": mode,
        "tool_id": tool_id,
        "safety": {
            "risk_level": risk_level,
            "score": None,
            "block_reason": reason,
            "warnings": [reason],
            "details": merged,
        },
    }


def unavailable_feasibility(
    *,
    mode: str,
    tool_id: str,
    context: Optional[str] = None,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    """
    No substantive evaluator is registered for this mode (D3/D4).

    Yields ``UNKNOWN`` — blocking under the default safety posture. It is
    never GREEN: inability to evaluate is not permission to manufacture.
    """
    reason = f"{ENGINE_UNAVAILABLE}: no substantive feasibility engine for mode '{mode}'"
    if detail:
        reason = f"{reason} ({detail})"
    return _non_authorizing_result(
        mode=mode,
        tool_id=tool_id,
        context=context,
        risk_level="UNKNOWN",
        code=ENGINE_UNAVAILABLE,
        reason=reason,
    )


def error_feasibility(
    *,
    mode: str,
    tool_id: str,
    context: Optional[str] = None,
    error: Optional[BaseException] = None,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    """
    The registered evaluator was reachable but could not produce a verdict.

    Yields ``ERROR`` — blocking. Deliberately *not* YELLOW: an engine that
    cannot evaluate has not established that the operation is survivable,
    and downgrading the failure to keep manufacturing running is the
    fail-open posture this increment removes.
    """
    described = detail or (f"{type(error).__name__}: {error}" if error else "unspecified failure")
    reason = f"{ENGINE_ERROR}: feasibility evaluation failed for mode '{mode}' ({described})"
    return _non_authorizing_result(
        mode=mode,
        tool_id=tool_id,
        context=context,
        risk_level="ERROR",
        code=ENGINE_ERROR,
        reason=reason,
        details={"error": described},
    )


__all__ = [
    "AUTHORITY_KEYS",
    "NON_AUTHORITATIVE_KEY",
    "ENGINE_UNAVAILABLE",
    "ENGINE_ERROR",
    "sanitize_feasibility_input",
    "unavailable_feasibility",
    "error_feasibility",
]
