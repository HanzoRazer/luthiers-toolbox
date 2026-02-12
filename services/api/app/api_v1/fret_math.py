"""
Fret Math API v1

Calculate fret positions, slot dimensions, and temperament options:

1. POST /frets/positions - Calculate fret positions from scale length
2. POST /frets/slots - Generate fret slot cutting parameters
3. GET  /frets/temperaments - List available temperament options
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/frets", tags=["Fret Math"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class FretPositionsRequest(BaseModel):
    """Request fret positions calculation."""
    scale_length_mm: float = Field(..., description="Scale length in mm (nut to saddle)")
    fret_count: int = Field(22, description="Number of frets (typically 19-24)")
    temperament: str = Field("equal_12", description="Temperament: equal_12, equal_19, pythagorean")
    nut_width_mm: float = Field(0.0, description="Nut slot width (subtracted from position)")


class FretPositionsResponse(V1Response):
    """Calculated fret positions."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "scale_length_mm": 648.0,
            "frets": [
                {"fret": 1, "distance_from_nut_mm": 36.37},
                {"fret": 2, "distance_from_nut_mm": 70.69},
            ],
            "temperament": "equal_12",
        }],
    )


class FretSlotsRequest(BaseModel):
    """Request fret slot cutting parameters."""
    scale_length_mm: float = Field(..., description="Scale length in mm")
    fret_count: int = Field(22, description="Number of frets")
    slot_width_mm: float = Field(0.6, description="Fret slot width")
    slot_depth_mm: float = Field(1.5, description="Fret slot depth")
    fretboard_radius_mm: Optional[float] = Field(None, description="Fretboard radius (None for flat)")
    temperament: str = Field("equal_12", description="Temperament model")


class FretSlotsResponse(V1Response):
    """Fret slot cutting parameters."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "slots": [
                {
                    "fret": 1,
                    "position_mm": 36.37,
                    "width_mm": 0.6,
                    "depth_mm": 1.5,
                },
            ],
            "tool_recommendation": "0.6mm slot cutter or 0.023in saw blade",
        }],
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/positions", response_model=FretPositionsResponse)
def calculate_fret_positions(req: FretPositionsRequest) -> FretPositionsResponse:
    """
    Calculate fret positions from scale length.

    Uses the 12-TET formula by default:
        position(n) = scale_length * (1 - 2^(-n/12))

    Other temperaments available for historical/experimental instruments.
    """
    if req.scale_length_mm <= 0:
        return FretPositionsResponse(
            ok=False,
            error="Scale length must be positive",
            hint="Common scale lengths: 648mm (25.5\"), 628mm (24.75\"), 864mm (34\" bass)",
        )

    if not 1 <= req.fret_count <= 36:
        return FretPositionsResponse(
            ok=False,
            error="Fret count must be between 1 and 36",
        )

    try:
        # Calculate using 12-TET formula (default)
        # Other temperaments delegate to calculators module
        if req.temperament == "equal_12":
            frets = []
            for n in range(1, req.fret_count + 1):
                position = req.scale_length_mm * (1 - 2 ** (-n / 12))
                frets.append({
                    "fret": n,
                    "distance_from_nut_mm": round(position - req.nut_width_mm, 3),
                    "distance_from_saddle_mm": round(req.scale_length_mm - position, 3),
                })
        else:
            # Delegate to alternative temperaments module
            from ..calculators.alternative_temperaments import get_ratio_set

            try:
                ratios = get_ratio_set(req.temperament, req.fret_count)
                frets = []
                for n, ratio in enumerate(ratios, 1):
                    position = req.scale_length_mm * (1 - 1 / ratio)
                    frets.append({
                        "fret": n,
                        "distance_from_nut_mm": round(position - req.nut_width_mm, 3),
                        "ratio": ratio,
                    })
            except (ValueError, KeyError):
                return FretPositionsResponse(
                    ok=False,
                    error=f"Unknown temperament: {req.temperament}",
                    hint="Available: equal_12, pythagorean, just_major, meantone",
                )

        return FretPositionsResponse(
            ok=True,
            data={
                "scale_length_mm": req.scale_length_mm,
                "fret_count": req.fret_count,
                "temperament": req.temperament,
                "frets": frets,
            },
        )
    except Exception as e:
        return FretPositionsResponse(
            ok=False,
            error=f"Calculation error: {str(e)}",
        )


@router.post("/slots", response_model=FretSlotsResponse)
def calculate_fret_slots(req: FretSlotsRequest) -> FretSlotsResponse:
    """
    Generate fret slot cutting parameters for CNC.

    Includes position, width, depth, and optional radius compensation.
    """
    if req.scale_length_mm <= 0:
        return FretSlotsResponse(
            ok=False,
            error="Scale length must be positive",
        )

    if req.slot_width_mm <= 0 or req.slot_width_mm > 2.0:
        return FretSlotsResponse(
            ok=False,
            error="Slot width must be between 0 and 2mm",
            hint="Standard fretwire needs 0.5-0.7mm slots",
        )

    try:
        slots = []
        for n in range(1, req.fret_count + 1):
            position = req.scale_length_mm * (1 - 2 ** (-n / 12))
            slot = {
                "fret": n,
                "position_mm": round(position, 3),
                "width_mm": req.slot_width_mm,
                "depth_mm": req.slot_depth_mm,
            }

            # Add radius compensation if specified
            if req.fretboard_radius_mm:
                # Calculate depth at edges for radiused board
                # Using chord calculation
                import math
                half_width = 22.0  # Assume 44mm fretboard width
                sagitta = req.fretboard_radius_mm - math.sqrt(
                    req.fretboard_radius_mm ** 2 - half_width ** 2
                )
                slot["center_depth_mm"] = round(req.slot_depth_mm + sagitta, 3)
                slot["radius_mm"] = req.fretboard_radius_mm

            slots.append(slot)

        # Tool recommendation
        if req.slot_width_mm <= 0.6:
            tool = "0.023\" (0.58mm) fret saw blade or slot cutter"
        elif req.slot_width_mm <= 0.7:
            tool = "0.025\" (0.64mm) fret saw blade"
        else:
            tool = f"{req.slot_width_mm}mm slot cutter"

        return FretSlotsResponse(
            ok=True,
            data={
                "scale_length_mm": req.scale_length_mm,
                "fret_count": req.fret_count,
                "slots": slots,
                "tool_recommendation": tool,
                "total_slot_length_mm": round(sum(s["width_mm"] for s in slots), 2),
            },
        )
    except Exception as e:
        return FretSlotsResponse(
            ok=False,
            error=f"Calculation error: {str(e)}",
        )


@router.get("/temperaments")
def list_temperaments() -> V1Response:
    """
    List available temperament options.

    Most instruments use 12-TET (equal temperament).
    Historical temperaments available for period instruments.
    """
    temperaments = [
        {
            "id": "equal_12",
            "name": "12-Tone Equal Temperament",
            "description": "Standard modern tuning - all semitones equal",
            "use_case": "99% of modern fretted instruments",
            "formula": "position = scale * (1 - 2^(-fret/12))",
        },
        {
            "id": "pythagorean",
            "name": "Pythagorean",
            "description": "Based on perfect fifths (3:2 ratio)",
            "use_case": "Medieval/Renaissance instruments, some folk instruments",
            "note": "Pure fifths but impure thirds",
        },
        {
            "id": "just_major",
            "name": "Just Intonation (Major)",
            "description": "Pure intervals based on harmonic series",
            "use_case": "Experimental, microtonal, specific key only",
            "note": "Only in-tune in one key",
        },
        {
            "id": "meantone",
            "name": "Quarter-Comma Meantone",
            "description": "Compromise between Pythagorean and Just",
            "use_case": "Renaissance/Baroque lutes, early guitars",
            "note": "Better thirds than Pythagorean",
        },
    ]

    return V1Response(
        ok=True,
        data={
            "temperaments": temperaments,
            "default": "equal_12",
            "recommendation": "Use equal_12 unless building a historical replica",
        },
    )
