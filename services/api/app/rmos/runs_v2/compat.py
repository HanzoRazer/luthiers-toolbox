"""
RMOS Runs v1 -> v2 Compatibility Layer

Provides conversion utilities for migrating from dataclass-based
v1 artifacts to Pydantic-based v2 artifacts.

Key Conversions:
- dataclass -> Pydantic BaseModel
- Flat hash fields -> nested Hashes model
- Optional feasibility_sha256 -> Required
- Optional risk_level -> Required (defaults to UNKNOWN)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    RunArtifact,
    RunDecision,
    Hashes,
    RunOutputs,
    RunAttachment,
    AdvisoryInputRef,
)
from .hashing import sha256_of_obj


def convert_v1_to_v2(v1_data: Dict[str, Any]) -> RunArtifact:
    """
    Convert a v1 run artifact dict to a v2 RunArtifact.

    Handles field mapping and required field defaults.

    Args:
        v1_data: Dictionary from v1 store (could be from dataclass asdict)

    Returns:
        RunArtifact (v2 Pydantic model)
    """
    # Extract run_id (required)
    run_id = v1_data.get("run_id", "")
    if not run_id:
        raise ValueError("run_id is required")

    # Parse created_at_utc
    created_at = v1_data.get("created_at_utc")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            created_at = datetime.now(timezone.utc)
    elif created_at is None:
        created_at = datetime.now(timezone.utc)

    # Build Hashes (handle v1 flat fields)
    feasibility = v1_data.get("feasibility") or {}
    request_hash = v1_data.get("request_hash")

    # Compute feasibility_sha256 if missing
    if request_hash and len(request_hash) == 64:
        feasibility_sha256 = request_hash
    else:
        feasibility_sha256 = sha256_of_obj(feasibility) if feasibility else sha256_of_obj({})

    hashes = Hashes(
        feasibility_sha256=feasibility_sha256,
        toolpaths_sha256=v1_data.get("toolpaths_hash"),
        gcode_sha256=v1_data.get("gcode_hash"),
        opplan_sha256=v1_data.get("opplan_hash"),
    )

    # Build RunDecision (handle v1 nested or flat)
    v1_decision = v1_data.get("decision")
    if isinstance(v1_decision, dict):
        risk_level = v1_decision.get("risk_level") or v1_decision.get("risk_bucket") or "UNKNOWN"
        score = v1_decision.get("score")
        block_reason = v1_decision.get("block_reason")
        warnings = v1_decision.get("warnings") or []
        details = v1_decision.get("details") or {}
    else:
        # Extract from feasibility if available
        risk_level = feasibility.get("risk_bucket") or feasibility.get("risk_level") or "UNKNOWN"
        score = feasibility.get("score")
        block_reason = feasibility.get("block_reason")
        warnings = feasibility.get("warnings") or []
        details = {}

    decision = RunDecision(
        risk_level=risk_level,
        score=score,
        block_reason=block_reason,
        warnings=warnings,
        details=details,
    )

    # Build RunOutputs
    outputs = RunOutputs(
        gcode_text=v1_data.get("gcode_text"),
        gcode_path=v1_data.get("gcode_path"),
        opplan_json=v1_data.get("opplan_json"),
        opplan_path=v1_data.get("opplan_path"),
        preview_svg_path=v1_data.get("preview_svg_path"),
    )

    # Convert attachments
    v1_attachments = v1_data.get("attachments") or []
    attachments = []
    for att in v1_attachments:
        if isinstance(att, dict):
            attachments.append(RunAttachment(
                sha256=att.get("sha256", ""),
                kind=att.get("kind", "unknown"),
                mime=att.get("mime", "application/octet-stream"),
                filename=att.get("filename", "attachment"),
                size_bytes=att.get("size_bytes", 0),
                created_at_utc=att.get("created_at_utc", datetime.now(timezone.utc).isoformat()),
            ))

    # Convert advisory inputs
    v1_advisory = v1_data.get("advisory_inputs") or []
    advisory_inputs = []
    for adv in v1_advisory:
        if isinstance(adv, dict):
            advisory_inputs.append(AdvisoryInputRef(
                advisory_id=adv.get("advisory_id", ""),
                kind=adv.get("kind", "unknown"),
                engine_id=adv.get("engine_id"),
                engine_version=adv.get("engine_version"),
                request_id=adv.get("request_id"),
            ))

    # Build the v2 artifact
    artifact = RunArtifact(
        # Identity
        run_id=run_id,
        created_at_utc=created_at,
        # Context
        mode=v1_data.get("mode") or v1_data.get("workflow_mode") or "unknown",
        tool_id=v1_data.get("tool_id") or "unknown",
        # Outcome
        status=v1_data.get("status") or "OK",
        # Inputs
        request_summary=v1_data.get("request_summary") or {},
        # Authoritative
        feasibility=feasibility,
        decision=decision,
        hashes=hashes,
        # Outputs
        outputs=outputs,
        # Advisory
        advisory_inputs=advisory_inputs,
        # Legacy attachments
        attachments=attachments if attachments else None,
        # Metadata
        meta=v1_data.get("meta") or {},
        # Legacy fields
        workflow_session_id=v1_data.get("workflow_session_id"),
        material_id=v1_data.get("material_id"),
        machine_id=v1_data.get("machine_id"),
        workflow_mode=v1_data.get("workflow_mode"),
        toolchain_id=v1_data.get("toolchain_id"),
        post_processor_id=v1_data.get("post_processor_id"),
        geometry_ref=v1_data.get("geometry_ref"),
        geometry_hash=v1_data.get("geometry_hash"),
        event_type=v1_data.get("event_type") or "unknown",
        parent_run_id=v1_data.get("parent_run_id"),
        drift_detected=v1_data.get("drift_detected"),
        drift_summary=v1_data.get("drift_summary"),
        gate_policy_id=v1_data.get("gate_policy_id"),
        gate_decision=v1_data.get("gate_decision"),
        engine_version=v1_data.get("engine_version"),
        toolchain_version=v1_data.get("toolchain_version"),
        config_fingerprint=v1_data.get("config_fingerprint"),
        notes=v1_data.get("notes"),
        errors=v1_data.get("errors"),
        explanation_status=v1_data.get("explanation_status") or "NONE",
        explanation_summary=v1_data.get("explanation_summary"),
    )

    return artifact


def convert_v2_to_v1_dict(artifact: RunArtifact) -> Dict[str, Any]:
    """
    Convert a v2 RunArtifact to v1-compatible dict.

    Useful for backward compatibility with clients expecting v1 format.

    Args:
        artifact: RunArtifact (v2 Pydantic model)

    Returns:
        Dictionary in v1 format
    """
    created_at = artifact.created_at_utc
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    v1: Dict[str, Any] = {
        "run_id": artifact.run_id,
        "created_at_utc": created_at,
        "event_type": artifact.event_type,
        "status": artifact.status,
        # Context
        "tool_id": artifact.tool_id,
        "mode": artifact.mode,
        "workflow_session_id": artifact.workflow_session_id,
        "material_id": artifact.material_id,
        "machine_id": artifact.machine_id,
        "workflow_mode": artifact.workflow_mode,
        "toolchain_id": artifact.toolchain_id,
        "post_processor_id": artifact.post_processor_id,
        # Geometry
        "geometry_ref": artifact.geometry_ref,
        "geometry_hash": artifact.geometry_hash,
        # Hashes (flattened from v2 nested model)
        "request_hash": artifact.hashes.feasibility_sha256,
        "toolpaths_hash": artifact.hashes.toolpaths_sha256,
        "gcode_hash": artifact.hashes.gcode_sha256,
        "opplan_hash": artifact.hashes.opplan_sha256,
        # Feasibility
        "feasibility": artifact.feasibility,
        "request_summary": artifact.request_summary,
        # Decision
        "decision": {
            "risk_level": artifact.decision.risk_level,
            "score": artifact.decision.score,
            "block_reason": artifact.decision.block_reason,
            "warnings": artifact.decision.warnings,
            "details": artifact.decision.details,
        },
        # Drift
        "parent_run_id": artifact.parent_run_id,
        "drift_detected": artifact.drift_detected,
        "drift_summary": artifact.drift_summary,
        # Gating
        "gate_policy_id": artifact.gate_policy_id,
        "gate_decision": artifact.gate_decision,
        # Versions
        "engine_version": artifact.engine_version,
        "toolchain_version": artifact.toolchain_version,
        "config_fingerprint": artifact.config_fingerprint,
        # Notes
        "notes": artifact.notes,
        "errors": artifact.errors,
        # Meta
        "meta": artifact.meta,
        # Attachments
        "attachments": [
            {
                "sha256": a.sha256,
                "kind": a.kind,
                "mime": a.mime,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "created_at_utc": a.created_at_utc,
            }
            for a in (artifact.attachments or [])
        ],
        # Advisory (new in v2, include for forward compat)
        "advisory_inputs": [
            {
                "advisory_id": a.advisory_id,
                "kind": a.kind,
                "engine_id": a.engine_id,
                "engine_version": a.engine_version,
                "request_id": a.request_id,
            }
            for a in (artifact.advisory_inputs or [])
        ],
    }

    return v1


def validate_v2_artifact(artifact: RunArtifact) -> List[str]:
    """
    Validate a v2 artifact against governance requirements.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Check required fields
    if not artifact.run_id:
        errors.append("run_id is required")

    if not artifact.hashes.feasibility_sha256:
        errors.append("hashes.feasibility_sha256 is required")
    elif len(artifact.hashes.feasibility_sha256) != 64:
        errors.append("hashes.feasibility_sha256 must be 64 hex characters")

    if not artifact.decision.risk_level:
        errors.append("decision.risk_level is required")

    if not artifact.mode:
        errors.append("mode is required")

    if not artifact.tool_id:
        errors.append("tool_id is required")

    if artifact.status not in ("OK", "BLOCKED", "ERROR"):
        errors.append(f"status must be OK, BLOCKED, or ERROR (got: {artifact.status})")

    return errors
