"""Completeness guard + validate-and-persist for RMOS Run Artifact Store.

Enforces required invariants per ``RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md``
before persisting artifacts. Creates BLOCKED artifacts when invariants are
missing so the audit trail is never broken.

Extracted from ``store.py`` (WP-3).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import RunArtifact, Hashes, RunDecision, RunOutputs


# =============================================================================
# Required Invariants
# =============================================================================

REQUIRED_INVARIANTS = [
    ("hashes.feasibility_sha256", "feasibility_sha256 is required for audit"),
    ("decision.risk_level", "risk_level is required for safety classification"),
]


class CompletenessViolation:
    """Details of a completeness violation."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.field}: {self.reason}"


# =============================================================================
# Public helpers
# =============================================================================

def check_completeness(
    *,
    feasibility_sha256: Optional[str] = None,
    risk_level: Optional[str] = None,
    feasibility: Optional[Dict[str, Any]] = None,
) -> List[CompletenessViolation]:
    """Check if required invariants are present."""
    violations: List[CompletenessViolation] = []

    # Check feasibility_sha256
    if not feasibility_sha256:
        # Try to extract from feasibility dict
        if feasibility and isinstance(feasibility, dict):
            feasibility_sha256 = feasibility.get("sha256") or feasibility.get("hash")
        if not feasibility_sha256:
            violations.append(CompletenessViolation(
                "hashes.feasibility_sha256",
                "Required for audit trail - hash of server-computed feasibility",
            ))

    # Check risk_level
    if not risk_level or not risk_level.strip():
        violations.append(CompletenessViolation(
            "decision.risk_level",
            "Required for safety classification - must be GREEN, YELLOW, RED, UNKNOWN, or ERROR",
        ))

    return violations


def create_blocked_artifact_for_violations(
    *,
    run_id: str,
    mode: str,
    tool_id: str,
    violations: List[CompletenessViolation],
    request_summary: Optional[Dict[str, Any]] = None,
    feasibility: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """Create a BLOCKED artifact when required invariants are missing."""
    violation_details = "; ".join(str(v) for v in violations)
    block_reason = f"Completeness guard: missing required fields - {violation_details}"

    # Use placeholder hash if not provided (indicates incomplete data)
    placeholder_hash = "0" * 64

    return RunArtifact(
        run_id=run_id,
        mode=mode,
        tool_id=tool_id,
        status="BLOCKED",
        request_summary=request_summary or {},
        feasibility=feasibility or {},
        decision=RunDecision(
            risk_level="ERROR",
            block_reason=block_reason,
            warnings=[f"Completeness violation: {v}" for v in violations],
            details={"violations": [{"field": v.field, "reason": v.reason} for v in violations]},
        ),
        hashes=Hashes(
            feasibility_sha256=placeholder_hash,  # Placeholder - incomplete data
        ),
        outputs=RunOutputs(),
        meta={"completeness_guard": True, "violation_count": len(violations)},
    )


def validate_and_persist(
    *,
    run_id: str,
    mode: str,
    tool_id: str,
    status: str,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    feasibility_sha256: Optional[str] = None,
    risk_level: Optional[str] = None,
    decision_score: Optional[float] = None,
    decision_warnings: Optional[List[str]] = None,
    decision_details: Optional[Dict[str, Any]] = None,
    outputs: Optional[RunOutputs] = None,
    block_reason: Optional[str] = None,
    toolpaths_sha256: Optional[str] = None,
    gcode_sha256: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """Validate completeness and persist artifact."""
    # Check completeness
    violations = check_completeness(
        feasibility_sha256=feasibility_sha256,
        risk_level=risk_level,
        feasibility=feasibility,
    )

    if violations:
        # Create BLOCKED artifact for audit trail
        artifact = create_blocked_artifact_for_violations(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            violations=violations,
            request_summary=request_summary,
            feasibility=feasibility,
        )
    else:
        # All required fields present - create normal artifact
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status=status,
            request_summary=request_summary,
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level,
                score=decision_score,
                block_reason=block_reason,
                warnings=decision_warnings or [],
                details=decision_details or {},
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256,
                toolpaths_sha256=toolpaths_sha256,
                gcode_sha256=gcode_sha256,
            ),
            outputs=outputs or RunOutputs(),
            meta=meta or {},
        )

    # Persist (always - for audit trail)
    from .store import _get_default_store
    store = _get_default_store()
    store.put(artifact)

    return artifact
