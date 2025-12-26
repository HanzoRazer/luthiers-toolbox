from __future__ import annotations

import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .schemas_manifest_v1 import TapToneBundleManifestV1
from .importer import import_acoustics_bundle
from .persist_glue import persist_import_plan

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])


class ImportByPathRequest(BaseModel):
    package_root: str = Field(..., description="Server-side path containing manifest.json + attachments/")
    session_id: Optional[str] = None
    batch_label: Optional[str] = None


class ImportResponse(BaseModel):
    run_id: str
    run_json_path: str
    attachments_written: int
    attachments_deduped: int
    index_updated: bool
    mode: str = "acoustics"
    event_type: Optional[str] = None
    bundle_id: Optional[str] = None
    bundle_sha256: Optional[str] = None


def _extract_zip_to_tempdir(zip_bytes: bytes) -> Path:
    """
    Extract zip to a temporary directory.
    We expect the zip to contain:
      manifest.json
      attachments/<relpath...>
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="rmos_acoustics_import_")).resolve()
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            # Basic safety: reject absolute paths and parent traversal
            for name in z.namelist():
                if name.startswith("/") or name.startswith("\\"):
                    raise HTTPException(status_code=400, detail="Zip contains absolute paths.")
                norm = name.replace("\\", "/")
                if ".." in norm.split("/"):
                    raise HTTPException(status_code=400, detail="Zip contains path traversal entries ('..').")
            z.extractall(tmpdir)
        return tmpdir
    except zipfile.BadZipFile:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Invalid zip file.")
    except HTTPException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Zip extraction failed: {e!s}")


def _load_manifest_or_400(package_root: Path) -> TapToneBundleManifestV1:
    manifest_path = package_root / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=400, detail=f"manifest.json not found at {manifest_path}")
    try:
        return TapToneBundleManifestV1.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Manifest validation failed: {e!s}")


def _validate_package_layout_or_400(package_root: Path) -> None:
    attachments_dir = package_root / "attachments"
    if not attachments_dir.exists() or not attachments_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"attachments/ dir not found at {attachments_dir}")


@router.post("/import-zip", response_model=ImportResponse)
async def import_acoustics_zip(
    file: UploadFile = File(..., description="Zip containing manifest.json + attachments/..."),
    session_id: Optional[str] = Form(default=None),
    batch_label: Optional[str] = Form(default=None),
) -> ImportResponse:
    """
    Upload a zip export package and import it into RMOS runs_v2 store.

    Zip must contain:
      - manifest.json
      - attachments/<relpath...>
    """
    # Read into memory (acceptable for typical bundles; you can stream later if needed)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    tmpdir = _extract_zip_to_tempdir(data)
    try:
        package_root = tmpdir
        _validate_package_layout_or_400(package_root)
        manifest = _load_manifest_or_400(package_root)

        plan = import_acoustics_bundle(
            manifest=manifest,
            session_id=session_id,
            batch_label=batch_label,
        )

        res = persist_import_plan(plan=plan, package_root=package_root, manifest=manifest)

        # Return useful indexing fields
        return ImportResponse(
            run_id=res.run_id,
            run_json_path=str(res.run_json_path),
            attachments_written=res.attachments_written,
            attachments_deduped=res.attachments_deduped,
            index_updated=res.index_updated,
            event_type=plan.run_meta.get("event_type"),
            bundle_id=plan.run_meta.get("bundle_id"),
            bundle_sha256=plan.run_meta.get("bundle_sha256"),
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@router.post("/import-path", response_model=ImportResponse)
def import_acoustics_path(req: ImportByPathRequest) -> ImportResponse:
    """
    Import a server-staged package root containing manifest.json + attachments/.
    """
    package_root = Path(req.package_root).expanduser().resolve()
    if not package_root.exists() or not package_root.is_dir():
        raise HTTPException(status_code=400, detail=f"package_root not found or not a dir: {package_root}")

    _validate_package_layout_or_400(package_root)
    manifest = _load_manifest_or_400(package_root)

    plan = import_acoustics_bundle(
        manifest=manifest,
        session_id=req.session_id,
        batch_label=req.batch_label,
    )

    res = persist_import_plan(plan=plan, package_root=package_root, manifest=manifest)

    return ImportResponse(
        run_id=res.run_id,
        run_json_path=str(res.run_json_path),
        attachments_written=res.attachments_written,
        attachments_deduped=res.attachments_deduped,
        index_updated=res.index_updated,
        event_type=plan.run_meta.get("event_type"),
        bundle_id=plan.run_meta.get("bundle_id"),
        bundle_sha256=plan.run_meta.get("bundle_sha256"),
    )
