"""
MRP-3B: DXF Translator API Endpoint

POST /api/export/translate/dxf
  - Accepts Export Object JSON (BodyExportObject)
  - Selects governed DXF translator (R12 or R2000)
  - Returns DXF file bytes
  - Enforces gate status (RED = 422)

Sprint: MRP-3B
"""

import os
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.auth.deps import get_optional_principal
from app.auth.principal import Principal
from app.cam.translators.dxf import (
    BodyOutlineDxfTranslator,
    DXF_R12_TRANSLATOR_ID,
    DXF_R2000_TRANSLATOR_ID,
)
from app.cam.translators.base import TranslatorErrorCode
from app.cam.translator_capability_registry import get_translator_capability
from app.export.body_export_bridge import BodyExportObject
from app.middleware.rate_limit import limiter


router = APIRouter(tags=["Export", "Translate", "DXF", "MRP"])


# ─── Rate Limit Configuration ────────────────────────────────────────────────

DXF_TRANSLATE_RATE_FREE = os.getenv("DXF_TRANSLATE_RATE_FREE", "10/hour")
DXF_TRANSLATE_RATE_AUTH = os.getenv("DXF_TRANSLATE_RATE_AUTH", "100/hour")


# ─── Request/Response Models ─────────────────────────────────────────────────


class TranslateErrorResponse(BaseModel):
    """Error response for translation failures."""
    ok: bool = False
    error: str
    gate: Optional[str] = None
    reasons: list = Field(default_factory=list)


class TranslateMetadata(BaseModel):
    """Metadata about the translation (returned as JSON if requested)."""
    export_id: str
    translator_id: str
    translator_version: str
    gate_status: str
    output_format: str
    output_size_bytes: int
    entities_translated: int
    provenance_hash: Optional[str] = None
    ibg_session_id: Optional[str] = None
    instrument_spec: Optional[str] = None


# ─── Helper Functions ────────────────────────────────────────────────────────


def _get_translator(version: str) -> BodyOutlineDxfTranslator:
    """Get translator instance for the requested version."""
    if version.lower() == "r12":
        return BodyOutlineDxfTranslator(dxf_version="R12")
    elif version.lower() == "r2000":
        return BodyOutlineDxfTranslator(dxf_version="R2000")
    else:
        raise ValueError(f"Unknown DXF version: {version}")


def _build_filename(export_id: str, version: str) -> str:
    """Build filename for Content-Disposition header."""
    clean_id = export_id.replace("/", "_").replace("\\", "_")
    return f"{clean_id}_{version.lower()}.dxf"


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post(
    "/dxf",
    summary="Translate Export Object to DXF",
    description="""
Translate a BodyExportObject to DXF format using the governed translator layer.

**Version selection:**
- `version=r12` (default): R12 format with LINE entities (free tier, maximum compatibility)
- `version=r2000`: R2000 format with LWPOLYLINE entities (paid tier, modern CAM)

**Gate enforcement:**
- GREEN gate: Translation proceeds normally
- YELLOW gate: Translation proceeds with warning headers
- RED gate: Translation blocked, returns 422

**Response:**
- Success: DXF file bytes with `application/dxf` content type
- Headers include provenance metadata (X-Export-ID, X-Translator-ID, etc.)

**Rate limits:** 10/hour unauthenticated, 100/hour authenticated
    """,
    responses={
        200: {
            "description": "DXF file bytes",
            "content": {"application/dxf": {}},
        },
        400: {
            "description": "Invalid request (unknown version, malformed input)",
            "model": TranslateErrorResponse,
        },
        422: {
            "description": "Export Object not translatable (red gate)",
            "model": TranslateErrorResponse,
        },
    },
)
@limiter.limit(DXF_TRANSLATE_RATE_FREE)
async def translate_to_dxf(
    request: Request,
    export_object: BodyExportObject,
    version: Literal["r12", "r2000", "R12", "R2000"] = Query(
        default="r12",
        description="DXF version: r12 (free tier) or r2000 (paid tier)",
    ),
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> Response:
    """
    Translate Export Object to DXF file.

    Uses the governed DXF translator from MRP-3A to serialize
    the Export Object geometry into DXF format.
    """
    # Normalize version
    version_normalized = version.upper()

    # Validate version
    if version_normalized not in ("R12", "R2000"):
        raise HTTPException(
            status_code=400,
            detail=TranslateErrorResponse(
                ok=False,
                error="INVALID_VERSION",
                reasons=[f"Unknown DXF version: {version}. Use 'r12' or 'r2000'."],
            ).model_dump(),
        )

    # Check gate status at API boundary (red gate blocks)
    gate_status = export_object.validation.gate_status
    if gate_status == "red":
        raise HTTPException(
            status_code=422,
            detail=TranslateErrorResponse(
                ok=False,
                error="EXPORT_OBJECT_NOT_TRANSLATABLE",
                gate="red",
                reasons=export_object.validation.issues,
            ).model_dump(),
        )

    # Get translator
    try:
        translator = _get_translator(version_normalized)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=TranslateErrorResponse(
                ok=False,
                error="TRANSLATOR_ERROR",
                reasons=[str(e)],
            ).model_dump(),
        )

    # Verify translator is in capability registry
    cap = get_translator_capability(translator.translator_id)
    if cap is None:
        raise HTTPException(
            status_code=500,
            detail=TranslateErrorResponse(
                ok=False,
                error="TRANSLATOR_NOT_REGISTERED",
                reasons=[f"Translator {translator.translator_id} not in capability registry"],
            ).model_dump(),
        )

    # Execute translation
    result = translator.translate(export_object)

    if not result.success:
        # Map error codes to HTTP status
        error_code = result.errors[0].code if result.errors else TranslatorErrorCode.SERIALIZATION_FAILED

        if error_code == TranslatorErrorCode.GATE_RED:
            raise HTTPException(
                status_code=422,
                detail=TranslateErrorResponse(
                    ok=False,
                    error="EXPORT_OBJECT_NOT_TRANSLATABLE",
                    gate="red",
                    reasons=[e.message for e in result.errors],
                ).model_dump(),
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=TranslateErrorResponse(
                    ok=False,
                    error="TRANSLATION_FAILED",
                    reasons=[e.message for e in result.errors],
                ).model_dump(),
            )

    # Build response with DXF bytes
    filename = _build_filename(export_object.export_id, version_normalized)

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Export-ID": export_object.export_id,
        "X-Translator-ID": translator.translator_id,
        "X-Translator-Version": translator.translator_version,
        "X-Governance-Gate": gate_status,
    }

    # Add provenance headers if available
    if result.provenance:
        if result.provenance.source_hash:
            headers["X-Provenance-Hash"] = result.provenance.source_hash
        if result.provenance.ibg_session_id:
            headers["X-IBG-Session-ID"] = result.provenance.ibg_session_id
        if result.provenance.instrument_spec:
            headers["X-Instrument-Spec"] = result.provenance.instrument_spec

    # Add warning header for yellow gate
    if gate_status == "yellow":
        warnings = export_object.validation.warnings
        if warnings:
            headers["X-Governance-Warnings"] = "; ".join(warnings[:3])

    return Response(
        content=result.output_bytes,
        media_type="application/dxf",
        headers=headers,
    )


@router.post(
    "/dxf/metadata",
    response_model=TranslateMetadata,
    summary="Get translation metadata without DXF bytes",
    description="""
Dry-run translation to get metadata and statistics without returning DXF bytes.

Useful for:
- Pre-flight validation
- Estimating output size
- Checking provenance
    """,
)
@limiter.limit(DXF_TRANSLATE_RATE_FREE)
async def translate_metadata_only(
    request: Request,
    export_object: BodyExportObject,
    version: Literal["r12", "r2000", "R12", "R2000"] = Query(
        default="r12",
        description="DXF version: r12 (free tier) or r2000 (paid tier)",
    ),
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> TranslateMetadata:
    """
    Get translation metadata without generating full DXF output.
    """
    version_normalized = version.upper()

    if version_normalized not in ("R12", "R2000"):
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_VERSION", "message": f"Unknown version: {version}"},
        )

    gate_status = export_object.validation.gate_status
    if gate_status == "red":
        raise HTTPException(
            status_code=422,
            detail=TranslateErrorResponse(
                ok=False,
                error="EXPORT_OBJECT_NOT_TRANSLATABLE",
                gate="red",
                reasons=export_object.validation.issues,
            ).model_dump(),
        )

    translator = _get_translator(version_normalized)
    result = translator.translate(export_object)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "TRANSLATION_FAILED", "reasons": [e.message for e in result.errors]},
        )

    return TranslateMetadata(
        export_id=export_object.export_id,
        translator_id=translator.translator_id,
        translator_version=translator.translator_version,
        gate_status=gate_status,
        output_format=result.output_format,
        output_size_bytes=result.statistics.get("output_size_bytes", 0),
        entities_translated=result.statistics.get("entities_translated", 0),
        provenance_hash=result.provenance.source_hash if result.provenance else None,
        ibg_session_id=result.provenance.ibg_session_id if result.provenance else None,
        instrument_spec=result.provenance.instrument_spec if result.provenance else None,
    )
