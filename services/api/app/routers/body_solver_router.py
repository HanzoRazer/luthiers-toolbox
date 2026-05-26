"""
Body Solver Router — Integration layer for Body Outline Editor ↔ IBG

Endpoints:
  POST /api/body/solve-from-dxf — Upload partial DXF, receive solved model (free tier)
  POST /api/body/solve-from-landmarks — Submit user-provided landmarks (paid tier)
  GET  /api/body/session/{session_id} — Retrieve previously solved session
  PUT  /api/body/session/{session_id}/landmarks — Override landmarks and re-solve (paid tier)

Sprint: IBG-2B — Production infrastructure (Redis sessions, auth, rate limiting)
"""

from __future__ import annotations

import asyncio
import base64
import json
import tempfile
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth.deps import get_current_principal, get_optional_principal
from app.auth.principal import Principal
from app.instrument_geometry.body.ibg import InstrumentBodyGenerator
from app.instrument_geometry.body.ibg.body_contour_solver import LandmarkPoint
from app.instrument_geometry.body.ibg.session_store import get_session_store
from app.middleware.rate_limit import limiter, rate_limit_tier
from app.util.ibg_dxf_export_lifecycle import IbgDxfExportBlockedError


router = APIRouter(prefix="/api/body", tags=["Body Solver"])


def _ibg_export_blocked_response(exc: IbgDxfExportBlockedError) -> HTTPException:
    """Map fail-closed IBG export to HTTP 422."""
    return HTTPException(
        status_code=422,
        detail={
            "error": "ibg_dxf_export_blocked",
            "message": str(exc),
            "r1_required": True,
        },
    )


# ─── Rate Limit Configuration ────────────────────────────────────────────────


IBG_RATE_LIMIT_FREE = os.getenv("IBG_RATE_LIMIT_FREE", "10/hour")
IBG_RATE_LIMIT_PAID = os.getenv("IBG_RATE_LIMIT_PAID", "100/hour")


# ─── Pydantic Models ──────────────────────────────────────────────────────────


class LandmarkInput(BaseModel):
    """Landmark point from user input."""
    label: str
    x_mm: float
    y_mm: float
    source: str = "user_input"
    confidence: float = 1.0


class SolveOptions(BaseModel):
    """Options for solve endpoints."""
    return_json: bool = True
    return_side_heights: bool = True
    return_zone_radii: bool = True
    return_dxf: bool = False


class SolveFromLandmarksRequest(BaseModel):
    """Request body for solve-from-landmarks endpoint."""
    instrument_spec: str
    landmarks: List[LandmarkInput]
    options: SolveOptions = Field(default_factory=SolveOptions)


class OverrideLandmarksRequest(BaseModel):
    """Request body for landmark override endpoint."""
    override_landmarks: List[LandmarkInput] = Field(default_factory=list)
    add_landmarks: List[LandmarkInput] = Field(default_factory=list)


# ─── Helper Functions ─────────────────────────────────────────────────────────


def _create_session(model, gen) -> str:
    """Create a new session and store the model."""
    store = get_session_store()
    session_data = {
        "instrument_spec": gen.spec_name,
        "landmarks": [
            {
                "label": lm.label,
                "x_mm": lm.x_mm,
                "y_mm": lm.y_mm,
                "source": lm.source,
                "confidence": lm.confidence,
            }
            for lm in model.landmarks.values()
        ],
        "model": _model_to_dict(model),
    }
    return store.create(session_data)


def _get_session(session_id: str) -> dict:
    """Get session or raise 404."""
    store = get_session_store()
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _update_session(session_id: str, data: dict) -> None:
    """Update session or raise 404."""
    store = get_session_store()
    if not store.update(session_id, data):
        raise HTTPException(status_code=404, detail="Session not found")


def _model_to_dict(model) -> dict:
    """Convert SolvedBodyModel to serializable dict."""
    return {
        "body_length_mm": model.body_length_mm,
        "lower_bout_width_mm": model.lower_bout_width_mm,
        "upper_bout_width_mm": model.upper_bout_width_mm,
        "waist_width_mm": model.waist_width_mm,
        "waist_y_norm": model.waist_y_norm,
        "outline_points": [[x, y] for x, y in model.outline_points],
        "side_heights_mm": list(model.side_heights_mm),
        "radii_by_zone": dict(model.radii_by_zone),
        "confidence": model.confidence,
        "missing_landmarks": list(model.missing_landmarks),
    }


async def _generate_dxf_base64(gen, model) -> str:
    """Generate DXF from model and return as base64 string."""
    loop = asyncio.get_event_loop()

    def _generate():
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            dxf_path = tmp.name

        try:
            gen.save_dxf(model, dxf_path)
            with open(dxf_path, "rb") as f:
                dxf_bytes = f.read()
            return base64.b64encode(dxf_bytes).decode("utf-8")
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)

    return await loop.run_in_executor(None, _generate)


def _model_to_response(model, gen, options: dict) -> dict:
    """Build API response from SolvedBodyModel."""
    response = {
        "status": "completed",
        "confidence": model.confidence,
        "dimensions": {
            "body_length_mm": round(model.body_length_mm, 2),
            "lower_bout_mm": round(model.lower_bout_width_mm, 2),
            "upper_bout_mm": round(model.upper_bout_width_mm, 2),
            "waist_mm": round(model.waist_width_mm, 2),
            "waist_y_norm": round(model.waist_y_norm, 3),
        },
        "errors_vs_expected": gen.validate_against_expected(model),
        "missing_landmarks": model.missing_landmarks,
        "radii_by_zone": {k: round(v, 2) for k, v in model.radii_by_zone.items()},
        "landmarks_extracted": [
            {
                "label": lm.label,
                "x": lm.x_mm,
                "y": lm.y_mm,
                "confidence": lm.confidence,
            }
            for lm in model.landmarks.values()
        ],
    }

    if options.get("return_side_heights", True):
        response["side_heights"] = [round(h, 2) for h in model.side_heights_mm]

    if options.get("return_json", True):
        response["outline_points"] = [
            [round(x, 3), round(y, 3)] for x, y in model.outline_points
        ]

    return response


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/solve-from-dxf")
@limiter.limit(IBG_RATE_LIMIT_FREE)
async def solve_from_dxf(
    request: Request,
    dxf_file: UploadFile = File(...),
    instrument_spec: str = Form(...),
    consolidate: bool = Form(True),
    options: str = Form("{}"),
    principal: Optional[Principal] = Depends(get_optional_principal),
):
    """
    Upload partial DXF, receive solved body model.

    Free tier endpoint — authentication optional.
    Rate limited to 10 requests/hour for unauthenticated users.

    Args:
        dxf_file: Partial vectorizer output DXF
        instrument_spec: Instrument type (dreadnought, cuatro_venezolano, stratocaster, jumbo)
        consolidate: If True, consolidate LINE entities to LWPOLYLINE first
        options: JSON string with return options

    Returns:
        Solved body model with dimensions, outline points, side heights, etc.
    """
    try:
        opts = json.loads(options)
    except json.JSONDecodeError:
        opts = {}

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await dxf_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        gen = InstrumentBodyGenerator(instrument_spec)

        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(
            None, lambda: gen.complete_from_dxf(tmp_path, consolidate=consolidate)
        )

        response = _model_to_response(model, gen, opts)
        response["session_id"] = _create_session(model, gen)

        if opts.get("return_dxf"):
            dxf_data = await _generate_dxf_base64(gen, model)
            response["dxf_data"] = dxf_data

        return JSONResponse(response)

    except IbgDxfExportBlockedError as e:
        raise _ibg_export_blocked_response(e) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/solve-from-landmarks")
@limiter.limit(IBG_RATE_LIMIT_PAID)
async def solve_from_landmarks(
    request: Request,
    body: SolveFromLandmarksRequest,
    principal: Principal = Depends(get_current_principal),
):
    """
    Solve body from user-provided landmarks.

    Paid tier endpoint — authentication required.
    Rate limited to 100 requests/hour.

    Args:
        body: Instrument spec + landmarks list

    Returns:
        Solved body model with dimensions, outline points, side heights, etc.
    """
    try:
        gen = InstrumentBodyGenerator(body.instrument_spec)

        landmarks = [
            LandmarkPoint(
                label=lm.label,
                x_mm=lm.x_mm,
                y_mm=lm.y_mm,
                source=lm.source,
                confidence=lm.confidence,
            )
            for lm in body.landmarks
        ]

        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(
            None, lambda: gen.complete_from_landmarks(landmarks)
        )

        opts = body.options.model_dump()
        response = _model_to_response(model, gen, opts)
        response["session_id"] = _create_session(model, gen)

        if opts.get("return_dxf"):
            dxf_data = await _generate_dxf_base64(gen, model)
            response["dxf_data"] = dxf_data

        return JSONResponse(response)

    except IbgDxfExportBlockedError as e:
        raise _ibg_export_blocked_response(e) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
@limiter.limit(IBG_RATE_LIMIT_FREE)
async def get_session(
    request: Request,
    session_id: str,
    principal: Optional[Principal] = Depends(get_optional_principal),
):
    """
    Retrieve previously solved session.

    Free tier endpoint — authentication optional.

    Args:
        session_id: Session ID from a previous solve call

    Returns:
        Stored session data including model and landmarks
    """
    session = _get_session(session_id)
    model_data = session["model"]

    return JSONResponse({
        "session_id": session_id,
        "status": "retrieved",
        "instrument_spec": session["instrument_spec"],
        "confidence": model_data["confidence"],
        "dimensions": {
            "body_length_mm": round(model_data["body_length_mm"], 2),
            "lower_bout_mm": round(model_data["lower_bout_width_mm"], 2),
            "upper_bout_mm": round(model_data["upper_bout_width_mm"], 2),
            "waist_mm": round(model_data["waist_width_mm"], 2),
            "waist_y_norm": round(model_data["waist_y_norm"], 3),
        },
        "missing_landmarks": model_data["missing_landmarks"],
        "radii_by_zone": {
            k: round(v, 2) for k, v in model_data["radii_by_zone"].items()
        },
        "side_heights": [round(h, 2) for h in model_data["side_heights_mm"]],
        "outline_points": [
            [round(x, 3), round(y, 3)] for x, y in model_data["outline_points"]
        ],
        "landmarks": session["landmarks"],
    })


@router.put("/session/{session_id}/landmarks")
@limiter.limit(IBG_RATE_LIMIT_PAID)
async def override_landmarks(
    request: Request,
    session_id: str,
    body: OverrideLandmarksRequest,
    principal: Principal = Depends(get_current_principal),
):
    """
    Override landmarks and re-solve.

    Paid tier endpoint — authentication required.
    Rate limited to 100 requests/hour.

    Args:
        session_id: Existing session ID
        body: Landmarks to override or add

    Returns:
        Re-solved body model with updated landmarks
    """
    session = _get_session(session_id)

    try:
        gen = InstrumentBodyGenerator(session["instrument_spec"])

        landmarks = [
            LandmarkPoint(
                label=lm["label"],
                x_mm=lm["x_mm"],
                y_mm=lm["y_mm"],
                source=lm.get("source", "session"),
                confidence=lm.get("confidence", 0.9),
            )
            for lm in session.get("landmarks", [])
        ]

        for override in body.override_landmarks:
            for i, lm in enumerate(landmarks):
                if lm.label == override.label:
                    landmarks[i] = LandmarkPoint(
                        label=override.label,
                        x_mm=override.x_mm,
                        y_mm=override.y_mm,
                        source="user_override",
                        confidence=override.confidence,
                    )
                    break

        for new_lm in body.add_landmarks:
            landmarks.append(
                LandmarkPoint(
                    label=new_lm.label,
                    x_mm=new_lm.x_mm,
                    y_mm=new_lm.y_mm,
                    source="user_added",
                    confidence=new_lm.confidence,
                )
            )

        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(
            None, lambda: gen.complete_from_landmarks(landmarks)
        )

        updated_session = {
            "instrument_spec": session["instrument_spec"],
            "landmarks": [
                {
                    "label": lm.label,
                    "x_mm": lm.x_mm,
                    "y_mm": lm.y_mm,
                    "source": lm.source,
                    "confidence": lm.confidence,
                }
                for lm in landmarks
            ],
            "model": _model_to_dict(model),
        }
        _update_session(session_id, updated_session)

        response = _model_to_response(model, gen, {"return_json": True})
        response["session_id"] = session_id

        return JSONResponse(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
