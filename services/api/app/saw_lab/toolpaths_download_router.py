# services/api/app/saw_lab/toolpaths_download_router.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


@router.get("/toolpaths/{toolpaths_artifact_id}/download/gcode")
def download_toolpaths_gcode(toolpaths_artifact_id: str):
    """
    Convenience download:
      toolpaths artifact -> gcode attachment sha256 -> redirect to global attachment fetch
    Requires:
      - /api/rmos/attachments/{sha256} exists (global attachment route)
      - toolpaths artifact payload.attachments.gcode_sha256 exists
    """
    if not toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    from app.rmos.runs_v2 import store as runs_store

    art = runs_store.get_run(toolpaths_artifact_id)
    if not isinstance(art, dict):
        raise HTTPException(status_code=404, detail="toolpaths artifact not found")

    payload = art.get("payload") or art.get("data") or {}
    if not isinstance(payload, dict):
        payload = {}

    attachments = payload.get("attachments") or {}
    if not isinstance(attachments, dict):
        attachments = {}

    sha = attachments.get("gcode_sha256") or attachments.get("gcode") or attachments.get("sha256")
    if not isinstance(sha, str) or not sha:
        raise HTTPException(status_code=409, detail="toolpaths artifact has no gcode attachment sha256")

    # Redirect to RMOS global attachment fetch (single source of truth)
    return RedirectResponse(url=f"/api/rmos/attachments/{sha}", status_code=302)
