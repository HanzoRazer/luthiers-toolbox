"""
RunArtifact → RunLogEntry projector.

Deterministic projection from full RunArtifact to flattened RunLogEntry.
This is a lossy transformation by design - the log is an audit surface, not a source of truth.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..runs_v2.schemas import RunArtifact
from .schemas import (
    RunLogEntry,
    InputSummary,
    CAMSummary,
    OutputsSummary,
    AttachmentsSummary,
    HashesSummary,
    LineageSummary,
)


def _extract_rules_triggered(feasibility: Dict[str, Any]) -> List[str]:
    """Extract triggered rule IDs from feasibility evaluation."""
    rules = []

    # Check for rules in various locations
    if "triggered_rules" in feasibility:
        rules.extend(feasibility["triggered_rules"])
    if "rules" in feasibility:
        for rule in feasibility.get("rules", []):
            if isinstance(rule, dict):
                rule_id = rule.get("rule_id") or rule.get("id")
                if rule_id and rule.get("triggered", True):
                    rules.append(rule_id)
            elif isinstance(rule, str):
                rules.append(rule)

    # Check decision details for rule references
    return list(set(rules))  # Dedupe


def _extract_input_summary(artifact: RunArtifact) -> InputSummary:
    """Extract input summary from request_summary."""
    req = artifact.request_summary or {}

    # Determine source type
    source_type = "UNKNOWN"
    if artifact.mode:
        if "dxf" in artifact.mode.lower():
            source_type = "DXF"
        elif "saw" in artifact.mode.lower():
            source_type = "Saw Lab"
        elif "art" in artifact.mode.lower():
            source_type = "Art Studio"
        else:
            source_type = artifact.mode.upper()

    # Extract filename
    filename = None
    if "filename" in req:
        filename = req["filename"]
    elif "input_filename" in req:
        filename = req["input_filename"]
    elif "geometry" in req and isinstance(req["geometry"], dict):
        filename = req["geometry"].get("filename")

    # Extract loop count and bbox
    loop_count = req.get("loop_count")
    bbox = None
    if "bbox" in req:
        bbox = req["bbox"]
    elif "bounds" in req:
        b = req["bounds"]
        if isinstance(b, dict):
            bbox = [b.get("x_min", 0), b.get("y_min", 0), b.get("x_max", 0), b.get("y_max", 0)]
        elif isinstance(b, list):
            bbox = b

    return InputSummary(
        source_type=source_type,
        filename=filename,
        loop_count=loop_count,
        bbox_mm=bbox,
    )


def _extract_cam_summary(artifact: RunArtifact) -> Optional[CAMSummary]:
    """Extract CAM parameters from request_summary."""
    req = artifact.request_summary or {}

    # Look for CAM params in various locations
    cam = req.get("cam") or req.get("cam_params") or req.get("params") or {}

    if not cam:
        return None

    return CAMSummary(
        tool_d_mm=cam.get("tool_d_mm") or cam.get("tool_diameter_mm"),
        stepover=cam.get("stepover") or cam.get("woc"),
        stepdown_mm=cam.get("stepdown_mm") or cam.get("doc_mm") or cam.get("depth_of_cut"),
        z_rough_mm=cam.get("z_rough_mm") or cam.get("z_rough"),
        strategy=cam.get("strategy") or cam.get("toolpath_strategy"),
    )


def _extract_outputs_summary(artifact: RunArtifact) -> Optional[OutputsSummary]:
    """Extract outputs summary."""
    outputs = artifact.outputs
    if not outputs:
        return None

    gcode_lines = None
    gcode_sha256 = artifact.hashes.gcode_sha256 if artifact.hashes else None

    # Count G-code lines if inline
    if outputs.gcode_text:
        gcode_lines = outputs.gcode_text.count("\n") + 1

    inline = bool(outputs.gcode_text)

    return OutputsSummary(
        gcode_lines=gcode_lines,
        gcode_sha256=gcode_sha256,
        inline=inline,
    )


def _extract_attachments_summary(artifact: RunArtifact) -> AttachmentsSummary:
    """Extract attachments summary."""
    attachments = artifact.attachments or []

    has_dxf = False
    has_gcode = False
    has_feasibility = False

    for att in attachments:
        kind = (att.kind or "").lower()
        filename = (att.filename or "").lower()

        if "dxf" in kind or filename.endswith(".dxf"):
            has_dxf = True
        if "gcode" in kind or filename.endswith(".nc") or filename.endswith(".gcode"):
            has_gcode = True
        if "feasibility" in kind:
            has_feasibility = True

    return AttachmentsSummary(
        count=len(attachments),
        has_dxf=has_dxf,
        has_gcode=has_gcode,
        has_feasibility=has_feasibility,
    )


def _extract_hashes_summary(artifact: RunArtifact) -> HashesSummary:
    """Extract hashes summary."""
    h = artifact.hashes
    return HashesSummary(
        feasibility_sha256=h.feasibility_sha256 if h else None,
        toolpaths_sha256=h.toolpaths_sha256 if h else None,
        gcode_sha256=h.gcode_sha256 if h else None,
    )


def _extract_lineage_summary(artifact: RunArtifact) -> LineageSummary:
    """Extract lineage summary."""
    parent_run_id = None

    # Check lineage envelope first
    if artifact.lineage and artifact.lineage.parent_plan_run_id:
        parent_run_id = artifact.lineage.parent_plan_run_id
    # Fall back to legacy field
    elif artifact.parent_run_id:
        parent_run_id = artifact.parent_run_id

    return LineageSummary(parent_run_id=parent_run_id)


def project_run_artifact(artifact: RunArtifact) -> RunLogEntry:
    """
    Project a RunArtifact to a RunLogEntry.

    This is a deterministic, lossy transformation.
    The same RunArtifact will always produce the same RunLogEntry.
    """
    decision = artifact.decision

    # Extract rules triggered
    rules_triggered = _extract_rules_triggered(artifact.feasibility)
    if decision and decision.warnings:
        # Add warning rule IDs if present
        for w in decision.warnings:
            if isinstance(w, str) and w.startswith("F") and len(w) <= 6:
                rules_triggered.append(w)
        rules_triggered = list(set(rules_triggered))

    # Count warnings
    warning_count = len(decision.warnings) if decision and decision.warnings else 0

    # Check for override
    override_applied = False
    if artifact.meta:
        override_applied = artifact.meta.get("override_applied", False)
    # Also check advisory_inputs for override
    for adv in artifact.advisory_inputs or []:
        if adv.kind == "override":
            override_applied = True
            break

    return RunLogEntry(
        run_id=artifact.run_id,
        created_at_utc=artifact.created_at_utc,
        mode=artifact.mode,
        tool_id=artifact.tool_id,
        status=artifact.status,
        risk_level=decision.risk_level if decision else "UNKNOWN",
        rules_triggered=rules_triggered,
        warning_count=warning_count,
        block_reason=decision.block_reason if decision else None,
        override_applied=override_applied,
        input_summary=_extract_input_summary(artifact),
        cam_summary=_extract_cam_summary(artifact),
        outputs=_extract_outputs_summary(artifact),
        attachments=_extract_attachments_summary(artifact),
        hashes=_extract_hashes_summary(artifact),
        lineage=_extract_lineage_summary(artifact),
    )
