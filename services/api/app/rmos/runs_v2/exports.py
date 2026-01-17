"""
RMOS Runs v2 Operator Pack Export

Provides a deterministic ZIP download of run artifacts for shop-floor use.
The operator pack contains everything needed to reproduce a manufacturing run.

Feasibility Enforcement (Phase 2):
- RED: Blocks export by default (requires allow_red_override feature flag)
- YELLOW: Requires explicit override with audit trail
- GREEN: Proceeds normally
"""
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .store import get_run, persist_run
from .attachments import put_json_attachment
from .schemas import RunAttachment


router = APIRouter(prefix="/api/rmos/runs_v2", tags=["RMOS"])


# =============================================================================
# Feature Flags
# =============================================================================

def _allow_red_override() -> bool:
    """Feature flag: allow override for RED runs (disabled by default)."""
    return os.getenv("RMOS_ALLOW_RED_OVERRIDE", "false").lower() in ("true", "1", "yes")


# =============================================================================
# Override Schema
# =============================================================================

class OverrideRecord(BaseModel):
    """
    Auditable override record for feasibility warnings.

    Overrides are additive - they never mutate the original feasibility result.
    The override attachment documents who approved proceeding despite warnings.
    """
    overridden_at_utc: str = Field(..., description="ISO timestamp of override")
    overridden_by: str = Field(..., description="User/operator ID who approved")
    reason: str = Field(..., description="Justification for override")
    original_risk_level: str = Field(..., description="Risk level being overridden")
    warnings_acknowledged: list[str] = Field(default_factory=list, description="Warnings acknowledged")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Optional client metadata")


def _attachments_root_dir() -> Path:
    """
    Runs v2 attachments are stored content-addressed:
      {ROOT}/{sha[0:2]}/{sha[2:4]}/{sha}{ext}

    We read the root from environment if present; otherwise fall back to the
    repo default used in this codebase: services/api/data/run_attachments.
    """
    env = os.environ.get("RMOS_RUN_ATTACHMENTS_DIR")
    if env:
        return Path(env)
    # Default for this repo structure
    return Path(__file__).resolve().parents[3] / "data" / "run_attachments"


def _attachment_path_for(sha256: str, filename: str) -> Path:
    ext = Path(filename).suffix or ""
    root = _attachments_root_dir()
    return root / sha256[0:2] / sha256[2:4] / f"{sha256}{ext}"


def _attachments_dir_for_sha(sha256: str) -> Path:
    root = _attachments_root_dir()
    return root / sha256[0:2] / sha256[2:4]


def _guess_mime_from_suffix(suffix: str) -> str:
    s = suffix.lower()
    if s == ".dxf":
        return "application/dxf"
    if s in (".json",):
        return "application/json"
    if s in (".nc", ".gcode", ".tap", ".txt"):
        return "text/plain"
    if s in (".zip",):
        return "application/zip"
    return "application/octet-stream"


def _resolve_attachment_file(sha256: str) -> Tuple[Path, str]:
    """
    Attachments are stored as:
      {root}/{aa}/{bb}/{sha256}{ext}
    But the API caller only has sha. We locate the file by globbing sha256.*
    in the correct subdir and picking the first match.
    """
    d = _attachments_dir_for_sha(sha256)
    if not d.exists():
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Prefer common extensions first for determinism
    preferred = [".dxf", ".json", ".nc", ".gcode", ".tap", ".txt"]
    for ext in preferred:
        p = d / f"{sha256}{ext}"
        if p.exists():
            return p, ext

    matches = sorted(d.glob(f"{sha256}*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Attachment not found")

    p = matches[0]
    return p, p.suffix or ""


@router.get("/attachments/{sha256}")
def download_attachment(sha256: str):
    """
    Read-only attachment fetch by sha256.
    Best-effort filename + mime based on stored extension.
    """
    sha256 = (sha256 or "").strip()
    if len(sha256) != 64:
        raise HTTPException(status_code=422, detail="sha256 must be 64 hex chars")

    path, ext = _resolve_attachment_file(sha256)
    mime = _guess_mime_from_suffix(ext)
    filename = f"{sha256}{ext}"

    f = open(path, "rb")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(f, media_type=mime, headers=headers)


def _pick_by_kind(attachments, kind: str):
    for a in attachments or []:
        if getattr(a, "kind", None) == kind:
            return a
    return None


def _get_risk_level(run) -> str:
    """Extract risk level from run artifact."""
    # Check feasibility first (authoritative)
    if run.feasibility and isinstance(run.feasibility, dict):
        return run.feasibility.get("risk_level", "UNKNOWN")
    # Fallback to decision
    if run.decision:
        return run.decision.risk_level or "UNKNOWN"
    return "UNKNOWN"


def _get_warnings(run) -> list[str]:
    """Extract warnings from run artifact."""
    warnings = []
    if run.feasibility and isinstance(run.feasibility, dict):
        warnings.extend(run.feasibility.get("warnings", []))
        warnings.extend(run.feasibility.get("blocking_reasons", []))
    if run.decision and run.decision.warnings:
        for w in run.decision.warnings:
            if w not in warnings:
                warnings.append(w)
    return warnings


def _has_override(run) -> bool:
    """Check if run has an override attachment."""
    for att in run.attachments or []:
        if getattr(att, "kind", None) == "override":
            return True
    return False


@router.get("/{run_id}/operator-pack")
def download_operator_pack(
    run_id: str,
    override_by: Optional[str] = Query(None, description="User ID for override (required for YELLOW)"),
    override_reason: Optional[str] = Query(None, description="Reason for override (required for YELLOW)"),
):
    """
    Download a deterministic operator pack ZIP for a run.

    Feasibility Enforcement:
    - GREEN: Proceeds normally
    - YELLOW: Requires override_by and override_reason parameters
    - RED: Blocked by default (requires RMOS_ALLOW_RED_OVERRIDE=true env var)

    ZIP contents (canonical names):
      - input.dxf
      - plan.json
      - manifest.json
      - output.nc
      - feasibility.json (optional, included if available)
      - override.json (included if override was applied)
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # ==========================================================================
    # Feasibility Enforcement Gate
    # ==========================================================================
    risk_level = _get_risk_level(run)
    warnings = _get_warnings(run)
    has_existing_override = _has_override(run)

    if risk_level == "RED":
        if not _allow_red_override():
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "FEASIBILITY_RED_BLOCKED",
                    "message": f"Run {run_id} has RED feasibility status and cannot be exported.",
                    "risk_level": risk_level,
                    "warnings": warnings,
                    "resolution": "Fix the blocking issues or contact admin to enable RED override.",
                },
            )
        # RED with feature flag: still requires override params
        if not override_by or not override_reason:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "OVERRIDE_REQUIRED",
                    "message": "RED override requires override_by and override_reason parameters.",
                    "risk_level": risk_level,
                    "warnings": warnings,
                },
            )

    if risk_level == "YELLOW" and not has_existing_override:
        if not override_by or not override_reason:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "OVERRIDE_REQUIRED",
                    "message": f"Run {run_id} has YELLOW feasibility status. Override required.",
                    "risk_level": risk_level,
                    "warnings": warnings,
                    "required_params": ["override_by", "override_reason"],
                },
            )

    # ==========================================================================
    # Create Override Attachment (if override provided and not already present)
    # ==========================================================================
    att_override = _pick_by_kind(run.attachments, "override")
    override_created = False

    if override_by and override_reason and not att_override:
        # Create auditable override record
        override_record = OverrideRecord(
            overridden_at_utc=datetime.now(timezone.utc).isoformat(),
            overridden_by=override_by,
            reason=override_reason,
            original_risk_level=risk_level,
            warnings_acknowledged=warnings,
            client_info=None,
        )

        # Store override attachment
        try:
            att_override, _, _ = put_json_attachment(
                override_record.model_dump(),
                kind="override",
                filename="override.json",
            )
            override_created = True

            # Add to run's attachments and persist (additive, doesn't mutate feasibility)
            if run.attachments is None:
                run.attachments = []
            run.attachments.append(att_override)
            persist_run(run)
        except Exception as e:
            # Non-fatal: override storage failed but we can still export
            # Log warning but proceed
            pass

    # ==========================================================================
    # Gather Attachments
    # ==========================================================================
    att_dxf = _pick_by_kind(run.attachments, "dxf_input")
    att_plan = _pick_by_kind(run.attachments, "cam_plan")
    att_manifest = _pick_by_kind(run.attachments, "manifest")
    att_gcode = _pick_by_kind(run.attachments, "gcode_output")
    att_feasibility = _pick_by_kind(run.attachments, "feasibility")  # Optional

    missing = [
        name
        for name, att in [
            ("dxf_input", att_dxf),
            ("cam_plan", att_plan),
            ("manifest", att_manifest),
            ("gcode_output", att_gcode),
        ]
        if att is None
    ]
    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"Run {run_id} is missing required attachments: {missing}",
        )

    # Resolve attachment paths from sha + ext
    paths: Dict[str, Path] = {
        "input.dxf": _attachment_path_for(att_dxf.sha256, att_dxf.filename),
        "plan.json": _attachment_path_for(att_plan.sha256, att_plan.filename),
        "manifest.json": _attachment_path_for(att_manifest.sha256, att_manifest.filename),
        "output.nc": _attachment_path_for(att_gcode.sha256, att_gcode.filename),
    }

    # Include feasibility.json if available (optional, not required for older runs)
    if att_feasibility:
        feas_path = _attachment_path_for(att_feasibility.sha256, att_feasibility.filename)
        if feas_path.exists():
            paths["feasibility.json"] = feas_path

    # Include override.json if present (either existing or just created)
    if att_override:
        override_path = _attachment_path_for(att_override.sha256, att_override.filename)
        if override_path.exists():
            paths["override.json"] = override_path

    for name, p in paths.items():
        if not p.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Attachment file missing on disk for {name}: {p}",
            )

    # Build ZIP without loading large files fully into memory.
    spooled = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)  # 10MB in-memory, then spills to disk
    with zipfile.ZipFile(spooled, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, src in paths.items():
            zf.write(src, arcname=arcname)

    spooled.seek(0)

    headers = {
        "Content-Disposition": f'attachment; filename="operator_pack_{run_id}.zip"'
    }
    return StreamingResponse(spooled, media_type="application/zip", headers=headers)
