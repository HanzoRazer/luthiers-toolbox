"""
RMOS Runs v2 Compatibility Layer

Conversion utilities between v1 (dataclass/single-file) and v2 (Pydantic/date-partitioned).

GOVERNANCE:
- v1 records may lack REQUIRED fields (feasibility_sha256, risk_level)
- Conversion must synthesize these fields for compliance
- Legacy fields preserved in meta with v1_ prefix
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .schemas import (
    RunArtifact,
    RunDecision,
    RunOutputs,
    Hashes,
    RunAttachment,
)
from .hashing import sha256_json


def convert_v1_to_v2(raw: Dict[str, Any]) -> RunArtifact:
    """
    Convert v1 artifact dict to v2 RunArtifact.

    GOVERNANCE - Required field synthesis:
    - feasibility_sha256: Use request_hash, or compute from feasibility
    - risk_level: Map from gate_decision, or default to "UNKNOWN"
    """
    # Extract run_id (REQUIRED)
    run_id = raw.get("run_id", "")
    if not run_id:
        raise ValueError("run_id is REQUIRED for conversion")

    # Parse created_at
    created_at_raw = raw.get("created_at_utc")
    if isinstance(created_at_raw, str):
        try:
            created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        except Exception:
            created_at = datetime.now(timezone.utc)
    elif isinstance(created_at_raw, datetime):
        created_at = created_at_raw
    else:
        created_at = datetime.now(timezone.utc)

    # Map mode/tool_id (REQUIRED)
    mode = raw.get("mode") or raw.get("workflow_mode") or "unknown"
    tool_id = raw.get("tool_id") or "unknown"

    # Map status (REQUIRED)
    status = raw.get("status", "OK")
    if status not in ("OK", "BLOCKED", "ERROR"):
        status = "OK"

    # Build request_summary (REQUIRED)
    request_summary = raw.get("request_summary") or {}

    # Build feasibility (REQUIRED)
    feasibility = raw.get("feasibility") or {}

    # Synthesize risk_level (REQUIRED)
    decision_raw = raw.get("decision") or {}
    if isinstance(decision_raw, dict):
        risk_level = decision_raw.get("risk_level")
        score = decision_raw.get("score")
        block_reason = decision_raw.get("block_reason")
        warnings = decision_raw.get("warnings") or []
        details = decision_raw.get("details") or {}
    else:
        risk_level = None
        score = None
        block_reason = None
        warnings = []
        details = {}

    # Map gate_decision to risk_level if not present
    if not risk_level:
        gate = raw.get("gate_decision")
        if gate == "GO":
            risk_level = "GREEN"
        elif gate == "NO_GO":
            risk_level = "RED"
        elif gate == "CONDITIONAL":
            risk_level = "YELLOW"
        else:
            risk_level = "UNKNOWN"  # REQUIRED field default

    decision = RunDecision(
        risk_level=risk_level,
        score=score,
        block_reason=block_reason,
        warnings=warnings,
        details=details,
    )

    # Synthesize feasibility_sha256 (REQUIRED)
    feasibility_sha256 = (
        raw.get("request_hash") or
        raw.get("feasibility_hash") or
        (sha256_json(feasibility) if feasibility else None)
    )
    if not feasibility_sha256:
        # Last resort: compute from entire raw record
        feasibility_sha256 = sha256_json({"run_id": run_id, "created_at": str(created_at)})

    hashes = Hashes(
        feasibility_sha256=feasibility_sha256,
        toolpaths_sha256=raw.get("toolpaths_hash"),
        gcode_sha256=raw.get("gcode_hash"),
    )

    # Build outputs
    outputs = RunOutputs(
        gcode_path=raw.get("gcode_path"),
        opplan_path=raw.get("opplan_path"),
    )

    # Convert attachments
    attachments_raw = raw.get("attachments") or []
    attachments = []
    for att in attachments_raw:
        if isinstance(att, dict):
            try:
                attachments.append(RunAttachment(
                    sha256=att.get("sha256", ""),
                    kind=att.get("kind", "unknown"),
                    mime=att.get("mime", "application/octet-stream"),
                    filename=att.get("filename", "unknown"),
                    size_bytes=att.get("size_bytes", 0),
                ))
            except Exception:
                continue

    # Preserve legacy fields in meta
    meta = dict(raw.get("meta") or {})
    legacy_fields = [
        "workflow_session_id", "material_id", "machine_id",
        "toolchain_id", "post_processor_id", "geometry_ref",
        "geometry_hash", "event_type", "parent_run_id",
        "drift_detected", "drift_summary", "engine_version",
        "toolchain_version", "config_fingerprint", "notes", "errors"
    ]
    for field in legacy_fields:
        if field in raw and raw[field] is not None:
            meta[f"v1_{field}"] = raw[field]

    # Mark as converted
    meta["converted_from_v1"] = True
    meta["conversion_timestamp"] = datetime.now(timezone.utc).isoformat()

    return RunArtifact(
        run_id=run_id,
        created_at_utc=created_at,
        mode=mode,
        tool_id=tool_id,
        status=status,
        request_summary=request_summary,
        feasibility=feasibility,
        decision=decision,
        hashes=hashes,
        outputs=outputs,
        attachments=attachments if attachments else None,
        meta=meta,
    )


def convert_v2_to_v1(artifact: RunArtifact) -> Dict[str, Any]:
    """
    Convert v2 RunArtifact back to v1 dict format.

    For backward compatibility with systems expecting v1 format.
    """
    result: Dict[str, Any] = {
        "run_id": artifact.run_id,
        "created_at_utc": artifact.created_at_utc.isoformat(),
        "workflow_mode": artifact.mode,
        "mode": artifact.mode,
        "tool_id": artifact.tool_id,
        "status": artifact.status,
        "request_summary": artifact.request_summary,
        "feasibility": artifact.feasibility,
        "decision": artifact.decision.model_dump(),
        "request_hash": artifact.hashes.feasibility_sha256,
        "toolpaths_hash": artifact.hashes.toolpaths_sha256,
        "gcode_hash": artifact.hashes.gcode_sha256,
    }

    # Restore legacy fields from meta
    meta = artifact.meta or {}
    for key, value in meta.items():
        if key.startswith("v1_"):
            result[key[3:]] = value

    # Map risk_level back to gate_decision
    risk = artifact.decision.risk_level
    if risk == "GREEN":
        result["gate_decision"] = "GO"
    elif risk == "RED":
        result["gate_decision"] = "NO_GO"
    elif risk == "YELLOW":
        result["gate_decision"] = "CONDITIONAL"
    else:
        result["gate_decision"] = "UNKNOWN"

    # Convert attachments
    if artifact.attachments:
        result["attachments"] = [
            {
                "sha256": a.sha256,
                "kind": a.kind,
                "mime": a.mime,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "created_at_utc": a.created_at_utc.isoformat(),
            }
            for a in artifact.attachments
        ]

    # Copy outputs
    if artifact.outputs:
        result["gcode_path"] = artifact.outputs.gcode_path
        result["opplan_path"] = artifact.outputs.opplan_path

    return result


def validate_v1_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a v1 record and report missing fields.
    
    Returns dict with validation results.
    """
    issues = []
    
    if not raw.get("run_id"):
        issues.append("missing run_id")
    
    if not raw.get("request_hash") and not raw.get("feasibility_hash"):
        if not raw.get("feasibility"):
            issues.append("no hash and no feasibility to compute from")
    
    decision = raw.get("decision") or {}
    if not decision.get("risk_level"):
        if not raw.get("gate_decision"):
            issues.append("no risk_level and no gate_decision to map from")
    
    return {
        "run_id": raw.get("run_id"),
        "valid": len(issues) == 0,
        "issues": issues,
        "can_convert": "missing run_id" not in issues,
    }
