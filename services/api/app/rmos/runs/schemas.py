"""
RMOS Run Artifact Schemas

Defines the immutable RunArtifact structure for audit-grade tracking
of all approval and toolpath generation events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal, List

RunStatus = Literal["OK", "BLOCKED", "ERROR"]


@dataclass
class RunAttachment:
    """Metadata for an attachment stored in content-addressed storage."""
    sha256: str
    kind: str                 # "geometry" | "toolpaths" | "gcode" | "debug"
    mime: str                 # "application/json" | "text/plain"
    filename: str             # display name
    size_bytes: int
    created_at_utc: str


@dataclass
class RunArtifact:
    """
    Immutable run artifact for audit-grade tracking.
    
    Every approval attempt and toolpath generation creates a RunArtifact,
    whether successful or blocked. This provides complete audit trail.
    """
    run_id: str
    created_at_utc: str

    # Linkage
    workflow_session_id: Optional[str] = None

    # Context
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None
    workflow_mode: Optional[str] = None

    # Execution metadata
    toolchain_id: Optional[str] = None          # e.g. "rosette_cam_v1"
    post_processor_id: Optional[str] = None     # e.g. "grbl", "fanuc"

    # Geometry references
    geometry_ref: Optional[str] = None          # e.g. "RosetteParamSpec:v1"
    geometry_hash: Optional[str] = None         # sha256 of canonical geometry

    # Decision spine
    event_type: str = "unknown"                 # "approval" | "toolpaths" | "fork_replay"
    status: RunStatus = "OK"

    # Authoritative feasibility
    feasibility: Optional[Dict[str, Any]] = None

    # Payload hashes
    request_hash: Optional[str] = None
    toolpaths_hash: Optional[str] = None
    gcode_hash: Optional[str] = None

    # Attachments
    attachments: Optional[List[RunAttachment]] = None

    # Provenance (fork / lineage)
    parent_run_id: Optional[str] = None
    fork_of_event_type: Optional[str] = None
    fork_reason: Optional[str] = None

    # Replay gate metadata
    drift_detected: Optional[bool] = None
    drift_summary: Optional[Dict[str, Any]] = None
    override_note: Optional[str] = None
    gate_policy_id: Optional[str] = None
    gate_policy_version: Optional[str] = None
    gate_decision: Optional[str] = None   # "ALLOWED" | "BLOCKED" | "OVERRIDDEN"

    # Version stamps
    engine_version: Optional[str] = None
    toolchain_version: Optional[str] = None
    post_processor_version: Optional[str] = None
    config_fingerprint: Optional[str] = None

    # Misc
    notes: Optional[str] = None
    errors: Optional[List[str]] = None
