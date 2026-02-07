from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import hashlib
import zipfile
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .schemas_manifest_v1 import TapToneBundleManifestV1
from .importer import import_acoustics_bundle
from .persist_glue import persist_import_plan, ValidationSummary, _get_runs_root
from ..runs_v2.ingest_audit import (
    append_event,
    build_event,
    IngestEventError,
    IngestEventValidation,
)

router = APIRouter(tags=["rmos", "acoustics"])  # prefix set once in main.py (Issue B fix)

# Environment variable to allow legacy packs without validation_report.json
ALLOW_MISSING_VALIDATION_REPORT = os.environ.get("ACOUSTICS_ALLOW_MISSING_VALIDATION_REPORT", "").lower() in ("1", "true", "yes")

def _compute_zip_sha256(data: bytes) -> str:
    """Compute SHA256 of zip bytes."""
    return hashlib.sha256(data).hexdigest()


def _write_ingest_event_safe(
    outcome: str,
    *,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    uploader_filename: Optional[str] = None,
    zip_sha256: Optional[str] = None,
    zip_size_bytes: Optional[int] = None,
    http_status: Optional[int] = None,
    error: Optional[IngestEventError] = None,
    validation: Optional[IngestEventValidation] = None,
    run_id: Optional[str] = None,
    bundle_id: Optional[str] = None,
    bundle_sha256: Optional[str] = None,
) -> None:
    """
    Best-effort event write - never raises, never blocks import flow.
    """
    try:
        root = _get_runs_root()
        event = build_event(
            outcome=outcome,
            session_id=session_id,
            batch_label=batch_label,
            uploader_filename=uploader_filename,
            zip_sha256=zip_sha256,
            zip_size_bytes=zip_size_bytes,
            http_status=http_status,
            error=error,
            validation=validation,
            run_id=run_id,
            bundle_id=bundle_id,
            bundle_sha256=bundle_sha256,
        )
        append_event(root, event)
    except (OSError, ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
        pass  # Best-effort: never block import flow





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


class ValidationReportSummary(BaseModel):
    """Extracted summary from validation_report.json for indexing."""
    passed: bool
    errors_count: int
    warnings_count: int
    schema_id: Optional[str] = None


def _extract_validation_report_from_zip(
    zip_bytes: bytes,
    *,
    allow_missing_report: bool = False,
) -> Optional[ValidationReportSummary]:
    """
    Extract and validate validation_report.json from ZIP root.
    
    Returns:
        ValidationReportSummary if present and valid (passed=true)
        None if missing and allow_missing_report=True (UNKNOWN state)
    
    Raises:
        HTTPException 400 for malformed ZIP or invalid JSON
        HTTPException 422 for semantic failures (missing report, passed=false)
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            try:
                raw = zf.read("validation_report.json")
            except KeyError:
                if allow_missing_report:
                    return None
                raise HTTPException(status_code=422, detail={
                    "error": "validation_failed",
                    "message": "viewer_pack rejected: validation_report.json missing at ZIP root.",
                    "reason": "missing_validation_report",
                    "report_excerpt": [],
                    "errors_count": None,
                    "warnings_count": None,
                })
        report = json.loads(raw.decode("utf-8"))
    except HTTPException:
        raise
    except zipfile.BadZipFile as e:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_zip",
            "message": f"ZIP file is corrupt or invalid: {e}",
        })
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_validation_report_json",
            "message": f"validation_report.json is not valid JSON: {e}",
        })
    except (UnicodeDecodeError, OSError, KeyError) as e:  # WP-1: narrowed from except Exception
        raise HTTPException(status_code=400, detail={
            "error": "invalid_validation_report_json",
            "message": f"Failed to read validation_report.json: {e}",
        })

    schema_id = report.get("schema_id")
    passed = report.get("passed")
    errors = report.get("errors") or []
    warnings = report.get("warnings") or []
    
    errors_count = len(errors) if isinstance(errors, list) else 0
    warnings_count = len(warnings) if isinstance(warnings, list) else 0

    if passed is not True:
        # Extract first few errors for the response
        excerpt = errors[:5] if isinstance(errors, list) else []
        raise HTTPException(status_code=422, detail={
            "error": "validation_failed",
            "message": "viewer_pack rejected: validation_report.json indicates passed=false.",
            "reason": "passed_false",
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "report_excerpt": excerpt,
        })

    return ValidationReportSummary(
        passed=True,
        errors_count=errors_count,
        warnings_count=warnings_count,
        schema_id=schema_id,
    )


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
    except (OSError, ValueError) as e:  # WP-1: narrowed from except Exception
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Zip extraction failed: {e!s}")


def _load_manifest_or_400(package_root: Path) -> TapToneBundleManifestV1:
    manifest_path = package_root / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=400, detail=f"manifest.json not found at {manifest_path}")
    try:
        return TapToneBundleManifestV1.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:  # WP-1: narrowed from except Exception
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
      - validation_report.json (required, must have passed=true)

    Status codes:
      - 400: Malformed ZIP or invalid JSON
      - 422: Missing validation_report.json or passed=false

    Set ACOUSTICS_ALLOW_MISSING_VALIDATION_REPORT=true/1 for legacy packs
    (missing report allowed -> UNKNOWN state, but passed=false still rejects).

    Ingest events are written to {runs_root}/ingest_events/ on all paths:
      - 200: outcome=accepted
      - 400/422: outcome=rejected
      - 500: outcome=quarantined
    """
    # Read into memory (acceptable for typical bundles; you can stream later if needed)
    data = await file.read()
    uploader_filename = file.filename

    if not data:
        _write_ingest_event_safe(
            outcome="rejected",
            session_id=session_id,
            batch_label=batch_label,
            uploader_filename=uploader_filename,
            http_status=400,
            error={"code": "empty_upload", "message": "Empty upload."},
        )
        raise HTTPException(status_code=400, detail="Empty upload.")

    # Compute zip identity early for event tracking
    zip_sha256 = _compute_zip_sha256(data)
    zip_size_bytes = len(data)

    # Common event fields
    event_base = {
        "session_id": session_id,
        "batch_label": batch_label,
        "uploader_filename": uploader_filename,
        "zip_sha256": zip_sha256,
        "zip_size_bytes": zip_size_bytes,
    }

    try:
        # Validate the pack BEFORE any persistence
        allow_missing = ALLOW_MISSING_VALIDATION_REPORT
        validation_report = _extract_validation_report_from_zip(data, allow_missing_report=allow_missing)

        # Convert to persist layer type (avoiding Pydantic model in dataclass context)
        validation_summary: Optional[ValidationSummary] = None
        if validation_report is not None:
            validation_summary = ValidationSummary(
                passed=validation_report.passed,
                errors_count=validation_report.errors_count,
                warnings_count=validation_report.warnings_count,
            )

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

            res = persist_import_plan(
                plan=plan,
                package_root=package_root,
                manifest=manifest,
                validation_summary=validation_summary,
            )

            # Write accepted event
            _write_ingest_event_safe(
                outcome="accepted",
                **event_base,
                http_status=200,
                run_id=res.run_id,
                bundle_id=plan.run_meta.get("bundle_id"),
                bundle_sha256=plan.run_meta.get("bundle_sha256"),
            )

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

    except HTTPException as e:
        # 400 or 422 - rejected
        detail = e.detail if isinstance(e.detail, dict) else {"message": str(e.detail)}
        validation_info = None
        if detail.get("error") == "validation_failed":
            validation_info = IngestEventValidation(
                passed=False,
                errors_count=detail.get("errors_count"),
                warnings_count=detail.get("warnings_count"),
                reason=detail.get("reason"),
            )
        _write_ingest_event_safe(
            outcome="rejected",
            **event_base,
            http_status=e.status_code,
            error=IngestEventError(
                code=detail.get("error", "http_error"),
                message=detail.get("message", str(e.detail)),
            ),
            validation=validation_info,
        )
        raise

    except (OSError, ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        # 500 - quarantined
        _write_ingest_event_safe(
            outcome="quarantined",
            **event_base,
            http_status=500,
            error=IngestEventError(
                code="internal_error",
                message=str(e),
            ),
        )
        raise HTTPException(status_code=500, detail=f"Import failed: {e!s}")



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
