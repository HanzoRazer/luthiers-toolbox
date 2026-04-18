"""
Body Solver Router — Integration layer for Body Outline Editor ↔ IBG

Endpoints:
  POST /api/body/solve-from-dxf — Upload partial DXF, receive solved model (free tier)
  POST /api/body/solve-from-landmarks — Submit user-provided landmarks (paid tier)
  GET  /api/body/session/{session_id} — Retrieve previously solved session
  PUT  /api/body/session/{session_id}/landmarks — Override landmarks and re-solve (paid tier)

Sprint: Week 1 — API endpoints only, JSON output, no DXF export
"""

from __future__ import annotations

import tempfile
import os
import uuid
from functools import wraps
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.instrument_geometry.body.ibg import InstrumentBodyGenerator
from app.instrument_geometry.body.ibg.body_contour_solver import LandmarkPoint


router = APIRouter(prefix="/api/body", tags=["Body Solver"])


# ─── Auth Stub ────────────────────────────────────────────────────────────────


def requires_paid_tier(func):
    """
    Decorator stub for paid tier authentication.

    TODO: Implement real auth check against user subscription status.
    For now, allows all requests through for development/testing.
    In production, this should check request.user.is_paid or similar.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO: Implement real auth check
        # if not request.user.is_paid:
        #     raise HTTPException(status_code=403, detail="Paid tier required")
        return await func(*args, **kwargs)
    return wrapper


# ─── Session Storage ──────────────────────────────────────────────────────────


# TODO: Migrate to Redis before multi-worker deployment.
# This in-memory dict dies on restart and breaks with multiple workers.
# Docker Compose includes Redis but this code doesn't use it yet.
_sessions: Dict[str, Dict] = {}


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
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    _sessions[session_id] = {
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
    return session_id


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
async def solve_from_dxf(
    dxf_file: UploadFile = File(...),
    instrument_spec: str = Form(...),
    consolidate: bool = Form(True),
    options: str = Form("{}"),
):
    """
    Upload partial DXF, receive solved body model.

    Free tier endpoint — no auth required.

    Args:
        dxf_file: Partial vectorizer output DXF
        instrument_spec: Instrument type (dreadnought, cuatro_venezolano, stratocaster, jumbo)
        consolidate: If True, consolidate LINE entities to LWPOLYLINE first
        options: JSON string with return options

    Returns:
        Solved body model with dimensions, outline points, side heights, etc.
    """
    import json

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
        model = gen.complete_from_dxf(tmp_path, consolidate=consolidate)

        response = _model_to_response(model, gen, opts)
        response["session_id"] = _create_session(model, gen)

        return JSONResponse(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/solve-from-landmarks")
@requires_paid_tier
async def solve_from_landmarks(request: SolveFromLandmarksRequest):
    """
    Solve body from user-provided landmarks.

    Paid tier endpoint — requires authentication.

    Args:
        request: Instrument spec + landmarks list

    Returns:
        Solved body model with dimensions, outline points, side heights, etc.
    """
    try:
        gen = InstrumentBodyGenerator(request.instrument_spec)

        landmarks = [
            LandmarkPoint(
                label=lm.label,
                x_mm=lm.x_mm,
                y_mm=lm.y_mm,
                source=lm.source,
                confidence=lm.confidence,
            )
            for lm in request.landmarks
        ]

        model = gen.complete_from_landmarks(landmarks)

        response = _model_to_response(model, gen, request.options.model_dump())
        response["session_id"] = _create_session(model, gen)

        return JSONResponse(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve previously solved session.

    Args:
        session_id: Session ID from a previous solve call

    Returns:
        Stored session data including model and landmarks
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
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
@requires_paid_tier
async def override_landmarks(session_id: str, request: OverrideLandmarksRequest):
    """
    Override landmarks and re-solve.

    Paid tier endpoint — requires authentication.

    Args:
        session_id: Existing session ID
        request: Landmarks to override or add

    Returns:
        Re-solved body model with updated landmarks
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]

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

        for override in request.override_landmarks:
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

        for new_lm in request.add_landmarks:
            landmarks.append(
                LandmarkPoint(
                    label=new_lm.label,
                    x_mm=new_lm.x_mm,
                    y_mm=new_lm.y_mm,
                    source="user_added",
                    confidence=new_lm.confidence,
                )
            )

        model = gen.complete_from_landmarks(landmarks)

        _sessions[session_id] = {
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

        response = _model_to_response(model, gen, {"return_json": True})
        response["session_id"] = session_id

        return JSONResponse(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
