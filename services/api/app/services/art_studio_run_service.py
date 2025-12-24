"""
Art Studio Run Orchestration Service

Cross-domain orchestration for Art Studio workflows that must be recorded as RunArtifacts.
Lives in services/ because it coordinates multiple domains:
- Art Studio (design specs / snapshots)
- RMOS runs_v2 (artifact persistence + hashing)

Architecture Layer: ORCHESTRATION (Layer 5)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

This service:
- Creates RunArtifacts for feasibility previews and snapshot exports
- Does NOT contain math (delegates feasibility computation to Art Studio/RMOS layers)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .rmos_run_service import create_run_from_feasibility
from ..rmos.runs_v2 import RunArtifact


ART_STUDIO_MODE = "art_studio"


def _normalize_risk_level(value: Any) -> str:
    """
    Normalize risk/risk_bucket fields to the canonical run risk_level string.
    Expected: GREEN/YELLOW/RED/ERROR/UNKNOWN
    """
    if value is None:
        return "UNKNOWN"
    if isinstance(value, str):
        v = value.strip().upper()
        # tolerate "RiskBucket.GREEN" or similar
        v = v.split(".")[-1]
        return v
    # enums: try .value
    v = getattr(value, "value", None)
    if isinstance(v, str):
        return v.strip().upper()
    return "UNKNOWN"


def create_art_studio_feasibility_run(
    *,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    tool_id: str = "rosette",
    status: Optional[str] = None,
    block_reason: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create a RunArtifact for an Art Studio feasibility preview evaluation.
    """
    # Ensure feasibility has the canonical fields RMOS expects
    feasibility = dict(feasibility)
    feasibility.setdefault("details", {})
    feasibility.setdefault("warnings", [])
    feasibility.setdefault("score", feasibility.get("overall_score"))

    # Accept either "risk_level" or "risk_bucket"
    risk_level = _normalize_risk_level(
        feasibility.get("risk_level", feasibility.get("risk_bucket"))
    )
    feasibility["risk_level"] = risk_level

    return create_run_from_feasibility(
        mode=ART_STUDIO_MODE,
        tool_id=tool_id,
        request_summary=request_summary,
        feasibility=feasibility,
        status=status,
        block_reason=block_reason,
        meta=meta or {},
    )


def create_art_studio_snapshot_run(
    *,
    snapshot: Dict[str, Any],
    tool_id: str = "rosette",
    status: str = "OK",
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create a RunArtifact for a snapshot export/import operation.

    Snapshots may include feasibility; if missing, we still persist a run with UNKNOWN risk.
    """
    feasibility = snapshot.get("feasibility") or {
        "risk_level": "UNKNOWN",
        "score": None,
        "warnings": [],
        "details": {"note": "snapshot saved without feasibility"},
    }

    # request_summary should be a lightweight indexable payload (not huge blobs)
    request_summary = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "name": snapshot.get("name"),
        "created_at_utc": snapshot.get("created_at_utc"),
        "design_fingerprint": snapshot.get("design_fingerprint"),
        "has_feasibility": bool(snapshot.get("feasibility")),
    }

    return create_art_studio_feasibility_run(
        request_summary=request_summary,
        feasibility=feasibility,
        tool_id=tool_id,
        status=status,
        meta={"workflow": "snapshot", **(meta or {})},
    )
