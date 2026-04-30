"""
Fretboard Ecosphere API v1

Public API surface for the canonical fretboard ecosphere:

    POST /fretboard/compute       Build ecosphere from request (free)
    POST /fretboard/scala         Export ecosphere temperament as Scala (free)
    GET  /fretboard/presets       List preset request shapes (free)
    GET  /fretboard/presets/{name} Get full preset request (free)
    GET  /fretboard/schema        Return JSON schema for FretboardEcosphere (free)

DXF endpoint added in Commit 2.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.instrument_geometry.neck.fretboard_ecosphere import (
    FretboardInput,
    FretboardEcosphere,
    build_ecosphere,
)
from app.instrument_geometry.neck.fretboard_presets import (
    FRETBOARD_PRESETS,
    get_preset,
    list_presets,
)
from app.calculators.scala_loader import (
    scala_scale_from_cents,
    serialize_scala_to_text,
)


router = APIRouter(prefix="/fretboard", tags=["Fretboard Ecosphere"])


# =============================================================================
# POST /compute
# =============================================================================

@router.post(
    "/compute",
    response_model=FretboardEcosphere,
    summary="Build canonical fretboard ecosphere",
)
def post_compute(req: FretboardInput) -> FretboardEcosphere:
    """Build the canonical fretboard ecosphere from validated input.

    The ecosphere is the single source of truth for all downstream
    projections (DXF, SVG, JSON, G-code). All temperaments are honest
    after Phase 1.5: 19-TET produces real 19-TET math, Pythagorean
    uses real ratios, etc.
    """
    try:
        return build_ecosphere(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# =============================================================================
# POST /scala — content-negotiated export
# =============================================================================

@router.post(
    "/scala",
    summary="Export ecosphere temperament as Scala scale",
    responses={
        200: {
            "description": "Scala scale (JSON or .scl text per Accept header)",
            "content": {
                "application/json": {},
                "application/octet-stream": {},
            },
        },
    },
)
def post_scala(req: FretboardInput, request: Request) -> Response:
    """Build an ecosphere and export its temperament as a Scala scale.

    Accept header controls format:
      application/json (default)  -> structured JSON with cents, ratios, frequencies
      application/octet-stream    -> downloadable .scl file
      text/plain                  -> .scl text inline
    """
    try:
        eco = build_ecosphere(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cents = eco.to_scala_intervals()
    description = f"Generated from FretboardEcosphere temperament={req.temperament.value}"
    scale = scala_scale_from_cents(cents, description=description)
    accept = request.headers.get("accept", "application/json").lower()

    if "octet-stream" in accept or "text/plain" in accept:
        scl_text = serialize_scala_to_text(scale)
        media_type = (
            "text/plain" if "text/plain" in accept else "application/octet-stream"
        )
        filename = (
            f"{req.temperament.value}_{req.fret_count}fret.scl"
            .replace("/", "_").replace(" ", "_")
        )
        return Response(
            content=scl_text,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    return JSONResponse(content={
        "description": scale.description,
        "pitch_count": scale.pitch_count,
        "pitches": [
            {
                "source": p.source_text,
                "cents": p.cents,
                "ratio": list(p.ratio) if p.ratio else None,
                "frequency_ratio": p.frequency_ratio,
            }
            for p in scale.pitches
        ],
    })


# =============================================================================
# GET /presets
# =============================================================================

@router.get(
    "/presets",
    summary="List available preset configurations",
)
def get_presets() -> Dict[str, List[Dict[str, Any]]]:
    """Return summary of all available presets.

    Wrapped in {items: [...]} per OWASP recommendation against bare arrays.
    """
    return {"items": list_presets()}


@router.get(
    "/presets/{name}",
    response_model=FretboardInput,
    summary="Get full preset request shape by name",
)
def get_preset_by_name(name: str) -> FretboardInput:
    """Return the full FretboardInput for a named preset.

    Use the result as a starting point - POST it to /compute as-is or
    modify before POSTing.
    """
    try:
        return get_preset(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# GET /schema
# =============================================================================

@router.get(
    "/schema",
    summary="JSON Schema for FretboardEcosphere",
)
def get_schema() -> Dict[str, Any]:
    """Return Pydantic-generated JSON schema for client validation."""
    return FretboardEcosphere.model_json_schema()
