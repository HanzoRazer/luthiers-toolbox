"""
RMOS Runs v2 Operator Pack Export

Provides a deterministic ZIP download of run artifacts for shop-floor use.
The operator pack contains everything needed to reproduce a manufacturing run.
"""
from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .store import get_run


router = APIRouter(prefix="/api/rmos/runs_v2", tags=["RMOS"])


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


@router.get("/{run_id}/operator-pack")
def download_operator_pack(run_id: str):
    """
    Download a deterministic operator pack ZIP for a run.

    ZIP contents (canonical names):
      - input.dxf
      - plan.json
      - manifest.json
      - output.nc
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    att_dxf = _pick_by_kind(run.attachments, "dxf_input")
    att_plan = _pick_by_kind(run.attachments, "cam_plan")
    att_manifest = _pick_by_kind(run.attachments, "manifest")
    att_gcode = _pick_by_kind(run.attachments, "gcode_output")

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
