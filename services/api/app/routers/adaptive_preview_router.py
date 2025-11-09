# services/api/app/routers/adaptive_preview_router.py
"""
Patch N.14 - Adaptive Toolpath Preview
Generates SVG previews of adaptive toolpath patterns (spiral, trochoid)
"""
from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Literal, List, Tuple
import math

router = APIRouter(prefix="/cam/adaptive", tags=["cam", "adaptive-preview"])


def _svg_polyline(points: List[Tuple[float, float]], stroke: str = 'black') -> str:
    """
    Generate SVG from list of points
    
    Args:
        points: List of (x, y) coordinates
        stroke: SVG stroke color
    
    Returns:
        Complete SVG document with polyline
    """
    if not points:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    
    pad = 10.0
    w = (maxx - minx) + 2 * pad
    h = (maxy - miny) + 2 * pad
    
    # Flip Y for SVG coordinate system (top-left origin)
    pts = " ".join([f"{x-minx+pad:.2f},{h-(y-miny+pad):.2f}" for x, y in points])
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">
  <polyline fill="none" stroke="{stroke}" stroke-width="1" points="{pts}" />
</svg>'''
    return svg


class SpiralReq(BaseModel):
    """Spiral toolpath parameters"""
    width: float
    height: float
    step: float = 2.0  # Stepover distance
    turns: int = 30  # Not used in rectangular spiral, kept for compatibility
    center_x: float = 0.0
    center_y: float = 0.0


class TrochoidReq(BaseModel):
    """Trochoidal toolpath parameters"""
    width: float
    height: float
    pitch: float = 3.0  # Distance between passes
    amp: float = 0.6  # Amplitude of oscillation
    feed_dir: Literal["x", "y"] = "x"  # Primary feed direction


@router.post("/spiral.svg")
def spiral_svg(req: SpiralReq):
    """
    Generate rectangular spiral toolpath preview
    
    Creates inward-spiraling rectangular path from outside to center.
    Useful for visualizing pocket clearing strategies.
    
    Args:
        req: Spiral parameters (width, height, step, etc.)
    
    Returns:
        SVG image with purple spiral path
    """
    x0 = -req.width / 2 + req.center_x
    y0 = -req.height / 2 + req.center_y
    x1 = req.width / 2 + req.center_x
    y1 = req.height / 2 + req.center_y
    
    pts: List[Tuple[float, float]] = []
    left, right, top, bot = x0, x1, y1, y0
    
    # Generate inward spiral (rectangle shrinking from outside)
    while left <= right and bot <= top:
        # Trace perimeter: bottom-right, top-right, top-left, (next iteration starts at bot-left)
        pts.append((left, bot))
        pts.append((right, bot))
        pts.append((right, top))
        pts.append((left, top))
        
        # Step inward
        left += req.step
        bot += req.step
        right -= req.step
        top -= req.step
    
    return Response(content=_svg_polyline(pts, stroke="purple"), media_type="image/svg+xml")


@router.post("/trochoid.svg")
def trochoid_svg(req: TrochoidReq):
    """
    Generate trochoidal toolpath preview
    
    Creates sinusoidal oscillating path for slot milling.
    Reduces tool engagement and improves chip evacuation.
    
    Args:
        req: Trochoid parameters (width, height, pitch, amplitude, direction)
    
    Returns:
        SVG image with teal trochoidal path
    """
    pts: List[Tuple[float, float]] = []
    
    if req.feed_dir == "x":
        # Horizontal passes with vertical oscillation
        y = -req.height / 2
        while y <= req.height / 2:
            x = -req.width / 2
            while x <= req.width / 2:
                # Sinusoidal Y offset
                y_offset = req.amp * math.sin(2 * math.pi * x / max(1e-6, req.pitch))
                pts.append((x, y + y_offset))
                x += 0.5  # Sample resolution
            y += req.pitch
    else:
        # Vertical passes with horizontal oscillation
        x = -req.width / 2
        while x <= req.width / 2:
            y = -req.height / 2
            while y <= req.height / 2:
                # Sinusoidal X offset
                x_offset = req.amp * math.sin(2 * math.pi * y / max(1e-6, req.pitch))
                pts.append((x + x_offset, y))
                y += 0.5  # Sample resolution
            x += req.pitch
    
    return Response(content=_svg_polyline(pts, stroke="teal"), media_type="image/svg+xml")
