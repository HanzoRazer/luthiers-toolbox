"""
RMOS Operation ZIP Export Service

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Bundle 04: Exports operation artifacts as auditable ZIP files.

ZIP Structure:
    {run_id}.zip/
    ├── meta/
    │   ├── artifact.json      # Full RunArtifact
    │   ├── summary.json       # Lightweight summary
    │   └── hashes.json        # All SHA256 hashes
    ├── inputs/
    │   ├── cam_intent_v1.json # Original intent
    │   └── feasibility.json   # Server feasibility
    ├── outputs/
    │   ├── gcode.nc           # G-code (if generated)
    │   └── plan.json          # Operation plan (if generated)
    └── audit/
        └── lineage.json       # Parent references
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.rmos.runs_v2.store import get_run
from app.rmos.runs_v2.schemas import RunArtifact


class ExportError(Exception):
    """Error during export operation."""
    pass


def export_run_to_zip(run_id: str) -> io.BytesIO:
    """
    Export a run artifact to a ZIP file.

    Args:
        run_id: The run ID to export

    Returns:
        BytesIO containing the ZIP file

    Raises:
        ExportError: If run not found or export fails
    """
    # Fetch artifact
    artifact = get_run(run_id)
    if artifact is None:
        raise ExportError(f"Run not found: {run_id}")

    # Create ZIP in memory
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Meta directory
        _add_json_file(zf, "meta/artifact.json", artifact.model_dump())
        _add_json_file(zf, "meta/summary.json", _build_summary(artifact))
        _add_json_file(zf, "meta/hashes.json", _build_hashes(artifact))

        # Inputs directory
        if artifact.request_summary:
            _add_json_file(zf, "inputs/request_summary.json", artifact.request_summary)

        # Extract cam_intent from meta or request_summary
        cam_intent = (
            artifact.meta.get("cam_intent_v1")
            or artifact.request_summary.get("cam_intent_v1")
        )
        if cam_intent:
            _add_json_file(zf, "inputs/cam_intent_v1.json", cam_intent)

        if artifact.feasibility:
            _add_json_file(zf, "inputs/feasibility.json", artifact.feasibility)

        # Outputs directory
        if artifact.outputs:
            if artifact.outputs.gcode_text:
                zf.writestr("outputs/gcode.nc", artifact.outputs.gcode_text)

            if artifact.outputs.opplan_json:
                _add_json_file(zf, "outputs/plan.json", artifact.outputs.opplan_json)

        # Plan from meta (if present)
        if artifact.meta.get("plan"):
            _add_json_file(zf, "outputs/plan.json", artifact.meta["plan"])

        # Audit directory
        lineage = _build_lineage(artifact)
        _add_json_file(zf, "audit/lineage.json", lineage)

        # Decision details
        if artifact.decision:
            _add_json_file(zf, "audit/decision.json", artifact.decision.model_dump())

    buffer.seek(0)
    return buffer


def _add_json_file(zf: zipfile.ZipFile, path: str, data: Any) -> None:
    """Add a JSON file to the ZIP."""
    content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    zf.writestr(path, content)


def _build_summary(artifact: RunArtifact) -> Dict[str, Any]:
    """Build lightweight summary for quick inspection."""
    return {
        "run_id": artifact.run_id,
        "status": artifact.status,
        "mode": artifact.mode,
        "tool_id": artifact.tool_id,
        "event_type": artifact.event_type,
        "created_at_utc": artifact.created_at_utc.isoformat() if artifact.created_at_utc else None,
        "risk_level": artifact.decision.risk_level if artifact.decision else None,
        "has_gcode": bool(artifact.outputs and artifact.outputs.gcode_text),
        "has_plan": bool(artifact.outputs and artifact.outputs.opplan_json) or bool(artifact.meta.get("plan")),
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _build_hashes(artifact: RunArtifact) -> Dict[str, Any]:
    """Build hash manifest for verification."""
    hashes = {}

    if artifact.hashes:
        if artifact.hashes.feasibility_sha256:
            hashes["feasibility_sha256"] = artifact.hashes.feasibility_sha256
        if artifact.hashes.gcode_sha256:
            hashes["gcode_sha256"] = artifact.hashes.gcode_sha256
        if artifact.hashes.toolpaths_sha256:
            hashes["toolpaths_sha256"] = artifact.hashes.toolpaths_sha256
        if artifact.hashes.opplan_sha256:
            hashes["opplan_sha256"] = artifact.hashes.opplan_sha256

    return {
        "run_id": artifact.run_id,
        "hashes": hashes,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _build_lineage(artifact: RunArtifact) -> Dict[str, Any]:
    """Build lineage information for audit trail."""
    return {
        "run_id": artifact.run_id,
        "parent_run_id": artifact.parent_run_id,
        "parent_plan_run_id": artifact.meta.get("parent_plan_run_id"),
        "request_id": artifact.request_id,
        "workflow_session_id": artifact.workflow_session_id,
        "created_at_utc": artifact.created_at_utc.isoformat() if artifact.created_at_utc else None,
    }


def get_export_filename(run_id: str) -> str:
    """Get the filename for a ZIP export."""
    # Sanitize run_id for filesystem
    safe_id = run_id.replace("/", "_").replace("\\", "_")
    return f"{safe_id}.zip"
