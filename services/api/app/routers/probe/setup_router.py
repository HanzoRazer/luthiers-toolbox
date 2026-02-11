"""Setup sheet and probe pattern listing endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns, probe_svg
from ...schemas.probe_schemas import SetupSheetIn

router = APIRouter(tags=["probe"])


@router.post("/setup_sheet/svg")
async def generate_setup_sheet(body: SetupSheetIn) -> Response:
    """
    Generate SVG setup sheet for probing pattern.

    Returns SVG document with part outline, probe points, and dimensions.
    """
    try:
        if body.pattern in ["corner_outside", "corner_inside"]:
            svg = probe_svg.generate_corner_outside_sheet(
                part_width=body.part_width or 100.0,
                part_height=body.part_height or 60.0,
                probe_offset=body.probe_offset or 20.0
            )

        elif body.pattern in ["boss_circular", "hole_circular"]:
            svg = probe_svg.generate_boss_circular_sheet(
                boss_diameter=body.feature_diameter or 50.0
            )

        elif body.pattern == "pocket_inside":
            svg = probe_svg.generate_pocket_inside_sheet(
                pocket_width=body.part_width or 100.0,
                pocket_height=body.part_height or 60.0,
                origin_corner=body.origin_corner or "center"
            )

        elif body.pattern == "surface_z":
            svg = probe_svg.generate_surface_z_sheet()

        else:
            raise ValueError(f"Pattern '{body.pattern}' not implemented")

        filename = f"setup_{body.pattern}.svg"

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def list_probe_patterns() -> Dict[str, Any]:
    """List all available probing patterns with metadata."""
    return {
        "patterns": probe_patterns.get_probe_patterns()
    }
