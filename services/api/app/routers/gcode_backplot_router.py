"""
G-code Backplot Router (Patch N.15)

Provides endpoints for G-code visualization and time estimation.

Endpoints:
- POST /cam/gcode/plot.svg - Generate SVG polyline from G-code
- POST /cam/gcode/estimate - Calculate distances and cycle time

Features:
- XY path visualization
- Travel vs cutting distance separation
- Time breakdown (rapid vs feed)
- Arc-aware distance calculation

Author: Patch N.15
Integrated: November 2025
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

from ..util.gcode_parser import simulate, svg_from_points

router = APIRouter(prefix="/api/cam/gcode", tags=["cam", "gcode"])


class PlotReq(BaseModel):
    """Request model for G-code backplot and estimation."""
    gcode: str
    units: str = "mm"
    rapid_mm_min: float = 3000.0
    default_feed_mm_min: float = 500.0
    stroke: str = "black"


@router.post("/plot.svg")
def plot(req: PlotReq) -> Response:
    """
    Generate SVG backplot from G-code.
    
    Parses G-code and creates a 2D XY visualization of the toolpath.
    
    Args:
        req: PlotReq with gcode, units, feed rates, and stroke color
    
    Returns:
        SVG image as application/svg+xml
    
    Example:
        POST /api/cam/gcode/plot.svg
        {
          "gcode": "G0 X10 Y10\\nG1 X20 F600\\nG1 Y20",
          "units": "mm",
          "stroke": "blue"
        }
    """
    sim = simulate(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units
    )
    svg = svg_from_points(sim["points_xy"], stroke=req.stroke)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/estimate")
def estimate(req: PlotReq) -> Dict[str, Any]:
    """
    Estimate G-code cycle time and distances.
    
    Calculates:
    - Travel distance (rapid moves)
    - Cutting distance (feed moves)
    - Time breakdown (rapid vs feed)
    - Total cycle time
    
    Args:
        req: PlotReq with gcode, units, and feed rates
    
    Returns:
        Dict with:
        - travel_mm: Rapid traverse distance
        - cut_mm: Cutting distance
        - t_rapid_min: Rapid time in minutes
        - t_feed_min: Feed time in minutes
        - t_total_min: Total cycle time
        - points_xy: XY path points (for reference)
    
    Example:
        POST /api/cam/gcode/estimate
        {
          "gcode": "G0 X10\\nG1 X20 F600",
          "rapid_mm_min": 3000,
          "default_feed_mm_min": 500
        }
        
        Response:
        {
          "travel_mm": 10.0,
          "cut_mm": 10.0,
          "t_rapid_min": 0.003333,
          "t_feed_min": 0.01666,
          "t_total_min": 0.02,
          "points_xy": [[0,0], [10,0], [20,0]]
        }
    """
    sim = simulate(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units
    )
    return sim
