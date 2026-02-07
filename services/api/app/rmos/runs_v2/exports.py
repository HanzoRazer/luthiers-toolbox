"""
RMOS Runs v2 Operator Pack Export

Provides a deterministic ZIP download of run artifacts for shop-floor use.
The operator pack contains everything needed to reproduce a manufacturing run.

Feasibility Enforcement (Phase 2):
- RED: Blocks export by default (requires override + RMOS_ALLOW_RED_OVERRIDE=1)
- YELLOW: Requires override attachment to exist
- GREEN: Proceeds normally
"""
from __future__ import annotations

import datetime
import json
import os
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .store import get_run
from .attachments import put_json_attachment


router = APIRouter(prefix="/api/rmos/runs_v2", tags=["RMOS"])


# =============================================================================
# Feature Flags
# =============================================================================

def _allow_red_override() -> bool:
    """Feature flag: allow override for RED runs (disabled by default)."""
    return os.getenv("RMOS_ALLOW_RED_OVERRIDE", "").strip() in ("1", "true", "TRUE", "yes", "YES")


# =============================================================================
# Override Index (separate from immutable run artifacts)
# =============================================================================

_OVERRIDE_INDEX_LOCK = threading.Lock()


def _overrides_index_path() -> Path:
    """Path to the overrides index file."""
    env = os.environ.get("RMOS_RUN_ATTACHMENTS_DIR")
    if env:
        return Path(env) / "_overrides_index.json"
    return Path(__file__).resolve().parents[3] / "data" / "run_attachments" / "_overrides_index.json"


def _load_overrides_index() -> Dict[str, str]:
    """Load the overrides index (run_id -> override_sha256)."""
    path = _overrides_index_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # WP-1: narrowed from except Exception
        return {}


def _save_overrides_index(index: Dict[str, str]) -> None:
    """Save the overrides index."""
    path = _overrides_index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _register_override(run_id: str, override_sha256: str) -> None:
    """Register an override for a run (atomic update to index)."""
    with _OVERRIDE_INDEX_LOCK:
        index = _load_overrides_index()
        index[run_id] = override_sha256
        _save_overrides_index(index)


def _get_override_sha(run_id: str) -> Optional[str]:
    """Get the override attachment sha256 for a run, if any."""
    index = _load_overrides_index()
    return index.get(run_id)


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


def _has_override(run_id: str) -> bool:
    """Check if run has an override in the index."""
    return _get_override_sha(run_id) is not None


def _risk_level_from_run(run) -> str:
    """
    Prefer decision.risk_level (authoritative), fallback to feasibility.risk_level.
    Returns uppercase string or "UNKNOWN".
    """
    # Check decision first (authoritative)
    if run.decision and getattr(run.decision, "risk_level", None):
        return run.decision.risk_level.upper()
    # Fallback to feasibility
    if run.feasibility and isinstance(run.feasibility, dict):
        return run.feasibility.get("risk_level", "UNKNOWN").upper()
    return "UNKNOWN"


# =============================================================================
# Override Endpoint
# =============================================================================

@router.post("/{run_id}/override")
def create_override(run_id: str, payload: Dict):
    """
    Create an override record as a content-addressed attachment.
    This does NOT mutate feasibility or the run artifact; it only records operator intent
    in a separate index.

    Body (minimal):
      { "reason": "...", "operator": "..." }
    """
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    reason = str((payload or {}).get("reason") or "").strip()
    operator = str((payload or {}).get("operator") or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Override requires non-empty reason")

    override_obj = {
        "run_id": run_id,
        "reason": reason,
        "operator": operator or None,
        # Timestamp is OK in the override artifact; it is not used for feasibility hashes.
        "created_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
    }

    override_att, override_path, override_sha = put_json_attachment(
        override_obj,
        kind="override",
        filename="override.json",
        ext=".json",
    )

    # Register override in the index (does NOT mutate immutable run artifact)
    _register_override(run_id, override_sha)

    return {
        "ok": True,
        "run_id": run_id,
        "override": {
            "reason": reason,
            "operator": operator or None,
        },
        "attachment": {
            "kind": "override",
            "sha256": override_att.sha256,
            "filename": override_att.filename,
            "mime": override_att.mime,
            "size_bytes": override_att.size_bytes,
            "created_at_utc": override_att.created_at_utc,
        },
    }


# =============================================================================
# Operator Pack Export
# =============================================================================

@router.get("/{run_id}/operator-pack")
def export_operator_pack(run_id: str):
    """
    Download a deterministic operator pack ZIP for a run.

    Feasibility Enforcement:
    - GREEN: Proceeds normally
    - YELLOW: Requires override attachment to exist
    - RED: Requires override attachment AND RMOS_ALLOW_RED_OVERRIDE=1

    ZIP contents (canonical names):
      - input.dxf
      - plan.json
      - manifest.json
      - output.nc
      - feasibility.json (optional, included if available)
      - override.json (included if override was applied)
    """
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    # ==========================================================================
    # Feasibility Enforcement Gate
    # ==========================================================================
    risk = _risk_level_from_run(run)

    if risk == "RED":
        if not (_has_override(run_id) and _allow_red_override()):
            raise HTTPException(
                status_code=403,
                detail="Operator pack export blocked: feasibility risk_level=RED (override disabled)",
            )

    if risk == "YELLOW":
        if not _has_override(run_id):
            raise HTTPException(
                status_code=403,
                detail="Operator pack export blocked: feasibility risk_level=YELLOW (override required)",
            )

    # ==========================================================================
    # Gather Attachments
    # ==========================================================================
    attachments = getattr(run, "attachments", None) or []
    att_dxf = _pick_by_kind(attachments, "dxf_input")
    att_plan = _pick_by_kind(attachments, "cam_plan")
    att_manifest = _pick_by_kind(attachments, "manifest")
    att_gcode = _pick_by_kind(attachments, "gcode_output")
    att_feasibility = _pick_by_kind(attachments, "feasibility")

    # Override is stored in separate index, not in run attachments
    override_sha = _get_override_sha(run_id)

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

    # Include override.json if present (from override index)
    if override_sha:
        override_path = _attachment_path_for(override_sha, "override.json")
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
