"""
MRP-4A: Multi-Target Translation API Endpoint

POST /api/export/translate/{target}
  - Accepts Export Object JSON
  - Routes to governed translator for target format
  - Returns serialized artifact
  - Enforces gate status (RED = 422)

Supported targets:
  - dxf: DXF geometry file (R12 or R2000)
  - svg: SVG visualization

Sprint: MRP-4A
"""

import os
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.auth.deps import get_optional_principal
from app.auth.principal import Principal
from app.cam.translators.base.contracts import TranslatorErrorCode, TranslatorOptions
from app.cam.translators.base.negotiation import (
    resolve_translator,
    get_supported_targets,
    get_supported_versions,
    get_default_version,
    TargetNotSupportedError,
    VersionNotSupportedError,
    TranslatorResolutionError,
)
from app.cam.translators.base.registry import get_translator_registry
from app.export.body_export_bridge import BodyExportObject
from app.middleware.rate_limit import limiter


router = APIRouter(tags=["Export", "Translate", "MRP"])


# ─── Rate Limit Configuration ────────────────────────────────────────────────

TRANSLATE_RATE_FREE = os.getenv("TRANSLATE_RATE_FREE", "10/hour")
TRANSLATE_RATE_AUTH = os.getenv("TRANSLATE_RATE_AUTH", "100/hour")


# ─── Content Type Mapping ────────────────────────────────────────────────────

TARGET_CONTENT_TYPES = {
    "dxf": "application/dxf",
    "svg": "image/svg+xml",
    "step": "application/step",
    "pdf": "application/pdf",
}


# ─── Request/Response Models ─────────────────────────────────────────────────


class TranslateErrorResponse(BaseModel):
    """Error response for translation failures."""
    ok: bool = False
    error: str
    gate: Optional[str] = None
    reasons: list = Field(default_factory=list)
    supported_targets: Optional[list] = None
    supported_versions: Optional[list] = None


class TranslateMetadata(BaseModel):
    """Metadata about the translation."""
    export_id: str
    target: str
    translator_id: str
    translator_version: str
    gate_status: str
    output_format: str
    output_size_bytes: int
    entities_translated: int
    provenance_hash: Optional[str] = None
    ibg_session_id: Optional[str] = None
    instrument_spec: Optional[str] = None


class TargetInfoResponse(BaseModel):
    """Information about a translation target."""
    target: str
    supported: bool
    versions: list
    default_version: Optional[str]
    translator_ids: list


class TargetsListResponse(BaseModel):
    """List of supported translation targets."""
    targets: list


# ─── Helper Functions ────────────────────────────────────────────────────────


def _build_filename(export_id: str, target: str, version: Optional[str]) -> str:
    """Build filename for Content-Disposition header."""
    clean_id = export_id.replace("/", "_").replace("\\", "_")
    suffix = f"_{version.lower()}" if version else ""
    return f"{clean_id}{suffix}.{target}"


def _get_content_type(target: str) -> str:
    """Get content type for target format."""
    return TARGET_CONTENT_TYPES.get(target, "application/octet-stream")


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/targets",
    response_model=TargetsListResponse,
    summary="List supported translation targets",
)
async def list_targets() -> TargetsListResponse:
    """List all supported translation target formats."""
    return TargetsListResponse(targets=get_supported_targets())


@router.get(
    "/targets/{target}",
    response_model=TargetInfoResponse,
    summary="Get information about a translation target",
)
async def get_target_info(
    target: str = Path(..., description="Target format (e.g., 'dxf', 'svg')"),
) -> TargetInfoResponse:
    """Get detailed information about a translation target."""
    registry = get_translator_registry()

    versions = get_supported_versions(target)
    default = get_default_version(target)
    translator_ids = registry.list_for_target(target)

    return TargetInfoResponse(
        target=target,
        supported=len(translator_ids) > 0,
        versions=versions,
        default_version=default,
        translator_ids=translator_ids,
    )


@router.post(
    "/{target}",
    summary="Translate Export Object to target format",
    description="""
Translate a BodyExportObject to the specified target format using the governed translator layer.

**Supported targets:**
- `dxf`: DXF geometry file (version: r12, r2000)
- `svg`: SVG visualization (version: 1.1)

**Version selection:**
- Use `version` query parameter to select specific format version
- Defaults to most compatible version for each target

**Gate enforcement:**
- GREEN gate: Translation proceeds normally
- YELLOW gate: Translation proceeds with warning headers
- RED gate: Translation blocked, returns 422

**Rate limits:** 10/hour unauthenticated, 100/hour authenticated
    """,
    responses={
        200: {"description": "Translated artifact bytes"},
        400: {
            "description": "Invalid request (unknown target/version)",
            "model": TranslateErrorResponse,
        },
        422: {
            "description": "Export Object not translatable (red gate)",
            "model": TranslateErrorResponse,
        },
    },
)
@limiter.limit(TRANSLATE_RATE_FREE)
async def translate_to_target(
    request: Request,
    export_object: BodyExportObject,
    target: str = Path(
        ...,
        description="Target format (e.g., 'dxf', 'svg')",
    ),
    version: Optional[str] = Query(
        default=None,
        description="Format version (e.g., 'r12', 'r2000' for DXF)",
    ),
    embed_provenance: bool = Query(
        default=True,
        description="Embed provenance in output",
    ),
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> Response:
    """
    Translate Export Object to target format.

    Uses the governed translator layer to serialize the Export Object
    into the specified target format.
    """
    target_lower = target.lower()

    # Check gate status at API boundary
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

    # Resolve translator
    try:
        translator = resolve_translator(
            target=target_lower,
            version=version,
            require_governed=True,
        )
    except TargetNotSupportedError as e:
        raise HTTPException(
            status_code=400,
            detail=TranslateErrorResponse(
                ok=False,
                error="TARGET_NOT_SUPPORTED",
                reasons=[str(e)],
                supported_targets=get_supported_targets(),
            ).model_dump(),
        )
    except VersionNotSupportedError as e:
        raise HTTPException(
            status_code=400,
            detail=TranslateErrorResponse(
                ok=False,
                error="VERSION_NOT_SUPPORTED",
                reasons=[str(e)],
                supported_versions=e.available_versions,
            ).model_dump(),
        )
    except TranslatorResolutionError as e:
        raise HTTPException(
            status_code=500,
            detail=TranslateErrorResponse(
                ok=False,
                error="TRANSLATOR_ERROR",
                reasons=[str(e)],
            ).model_dump(),
        )

    # Build options
    options = TranslatorOptions(
        version=version,
        embed_provenance=embed_provenance,
    )

    # Execute translation
    result = translator.translate(export_object, options)

    if not result.success:
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

    # Build response
    filename = _build_filename(export_object.export_id, target_lower, version)
    content_type = _get_content_type(target_lower)

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Export-ID": export_object.export_id,
        "X-Target-Format": target_lower,
        "X-Translator-ID": translator.translator_id,
        "X-Translator-Version": translator.translator_version,
        "X-Governance-Gate": gate_status,
    }

    if result.provenance:
        if result.provenance.source_hash:
            headers["X-Provenance-Hash"] = result.provenance.source_hash
        if result.provenance.ibg_session_id:
            headers["X-IBG-Session-ID"] = result.provenance.ibg_session_id
        if result.provenance.instrument_spec:
            headers["X-Instrument-Spec"] = result.provenance.instrument_spec

    if gate_status == "yellow":
        warnings = export_object.validation.warnings
        if warnings:
            headers["X-Governance-Warnings"] = "; ".join(warnings[:3])

    return Response(
        content=result.output_bytes,
        media_type=content_type,
        headers=headers,
    )


@router.post(
    "/{target}/metadata",
    response_model=TranslateMetadata,
    summary="Get translation metadata without artifact bytes",
)
@limiter.limit(TRANSLATE_RATE_FREE)
async def translate_metadata_only(
    request: Request,
    export_object: BodyExportObject,
    target: str = Path(..., description="Target format"),
    version: Optional[str] = Query(default=None, description="Format version"),
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> TranslateMetadata:
    """Get translation metadata without generating full output."""
    target_lower = target.lower()

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

    try:
        translator = resolve_translator(target_lower, version, require_governed=True)
    except (TargetNotSupportedError, VersionNotSupportedError, TranslatorResolutionError) as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)},
        )

    options = TranslatorOptions(version=version, embed_provenance=True)
    result = translator.translate(export_object, options)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "TRANSLATION_FAILED", "reasons": [e.message for e in result.errors]},
        )

    return TranslateMetadata(
        export_id=export_object.export_id,
        target=target_lower,
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
