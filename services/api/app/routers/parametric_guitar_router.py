"""
Parametric Guitar Design Router
Generate guitar body outlines from dimensional inputs (dimension-driven CAD)
"""

import io
import math
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/guitar/design", tags=["parametric", "guitar"])


# ============================================================================
# Pydantic Models
# ============================================================================

class GuitarDimensions(BaseModel):
    """Guitar body dimensions (all in mm)"""
    bodyLength: float = Field(..., ge=300, le=700, description="Body length (mm)")
    bodyWidthUpper: float = Field(..., ge=200, le=500, description="Upper bout width (mm)")
    bodyWidthLower: float = Field(..., ge=250, le=600, description="Lower bout width (mm)")
    waistWidth: float = Field(..., ge=150, le=400, description="Waist width (mm)")
    bodyDepth: Optional[float] = Field(None, ge=40, le=150, description="Body depth (mm)")
    scaleLength: float = Field(..., ge=500, le=900, description="Scale length (mm)")
    nutWidth: Optional[float] = Field(None, ge=35, le=60, description="Nut width (mm)")
    bridgeSpacing: Optional[float] = Field(None, ge=45, le=70, description="Bridge spacing (mm)")
    fretCount: Optional[int] = Field(None, ge=12, le=27, description="Fret count")
    neckAngle: Optional[float] = Field(None, ge=0, le=10, description="Neck angle (degrees)")


class GuitarDesignRequest(BaseModel):
    """Request to generate parametric guitar body outline"""
    dimensions: GuitarDimensions
    guitarType: Literal["Acoustic", "Electric", "Classical", "Bass"] = "Acoustic"
    units: Literal["mm", "inch"] = "mm"
    format: Literal["dxf", "svg", "json"] = "dxf"
    resolution: Optional[int] = Field(48, ge=16, le=128, description="Points per curve segment")


class BodyOutlineResponse(BaseModel):
    """Generated body outline data"""
    success: bool
    guitarType: str
    dimensions: dict
    outline: List[Tuple[float, float]]
    boundingBox: dict
    metadata: dict
    message: str


# ============================================================================
# Parametric Body Generation
# ============================================================================

def generate_body_outline(
    dimensions: GuitarDimensions,
    guitar_type: str,
    resolution: int = 48
) -> List[Tuple[float, float]]:
    """
    Generate parametric body outline from dimensions.
    
    Uses ellipse approximations and bezier curves for organic guitar shapes.
    Algorithm:
    1. Create upper bout ellipse (centered at 0, dimensions.bodyWidthUpper/2 radius)
    2. Create waist narrowing (bezier curve transition)
    3. Create lower bout ellipse (larger, offset downward)
    4. Blend curves for smooth continuous outline
    
    Args:
        dimensions: GuitarDimensions with all measurements
        guitar_type: "Acoustic", "Electric", "Classical", "Bass"
        resolution: Points per curve segment (higher = smoother)
    
    Returns:
        List of (x, y) tuples forming closed polyline
    """
    length = dimensions.bodyLength
    upper_width = dimensions.bodyWidthUpper
    lower_width = dimensions.bodyWidthLower
    waist = dimensions.waistWidth
    
    # Calculate key Y positions along body
    upper_center_y = length * 0.25  # Upper bout center at 25% from top
    waist_y = length * 0.50  # Waist at 50% (midpoint)
    lower_center_y = length * 0.75  # Lower bout center at 75% from top
    
    # Radii for ellipses
    upper_radius_x = upper_width / 2.0
    upper_radius_y = length * 0.20  # Upper bout height
    
    lower_radius_x = lower_width / 2.0
    lower_radius_y = length * 0.25  # Lower bout height (slightly larger)
    
    waist_half = waist / 2.0
    
    outline = []
    
    # === RIGHT SIDE (positive X) ===
    
    # 1. Upper bout (right side, top to waist)
    for i in range(resolution // 4):
        t = i / (resolution // 4 - 1)  # 0.0 to 1.0
        angle = math.pi / 2 - t * math.pi / 2  # 90° to 0° (top to side)
        x = upper_radius_x * math.cos(angle)
        y = upper_center_y + upper_radius_y * math.sin(angle)
        outline.append((x, y))
    
    # 2. Waist transition (right side, bezier curve)
    waist_start_y = upper_center_y - upper_radius_y * 0.5
    waist_end_y = waist_y + (lower_center_y - waist_y) * 0.3
    
    for i in range(resolution // 8):
        t = i / (resolution // 8 - 1)
        # Cubic bezier: P0 = (upper_radius_x, waist_start_y), P3 = (waist_half, waist_end_y)
        # Control points pull curve inward
        p0_x, p0_y = upper_radius_x, waist_start_y
        p1_x, p1_y = upper_radius_x * 0.9, waist_y - 20
        p2_x, p2_y = waist_half * 1.1, waist_y + 20
        p3_x, p3_y = waist_half, waist_end_y
        
        # Cubic bezier formula
        x = (1-t)**3 * p0_x + 3*(1-t)**2*t * p1_x + 3*(1-t)*t**2 * p2_x + t**3 * p3_x
        y = (1-t)**3 * p0_y + 3*(1-t)**2*t * p1_y + 3*(1-t)*t**2 * p2_y + t**3 * p3_y
        outline.append((x, y))
    
    # 3. Lower bout (right side, waist to bottom)
    for i in range(resolution // 4):
        t = i / (resolution // 4 - 1)
        angle = t * math.pi  # 0° to 180° (side to bottom)
        x = lower_radius_x * math.cos(angle)
        y = lower_center_y + lower_radius_y * math.sin(angle)
        if y < waist_end_y:  # Only add points below waist transition
            continue
        outline.append((x, y))
    
    # === LEFT SIDE (negative X, mirror right side) ===
    
    # 4. Lower bout (left side, bottom to waist)
    for i in range(resolution // 4):
        t = i / (resolution // 4 - 1)
        angle = math.pi + t * math.pi  # 180° to 360° (bottom to side)
        x = lower_radius_x * math.cos(angle)
        y = lower_center_y + lower_radius_y * math.sin(angle)
        if y < waist_end_y:
            continue
        outline.append((x, y))
    
    # 5. Waist transition (left side, bezier curve)
    for i in range(resolution // 8):
        t = i / (resolution // 8 - 1)
        p0_x, p0_y = -waist_half, waist_end_y
        p1_x, p1_y = -waist_half * 1.1, waist_y + 20
        p2_x, p2_y = -upper_radius_x * 0.9, waist_y - 20
        p3_x, p3_y = -upper_radius_x, waist_start_y
        
        x = (1-t)**3 * p0_x + 3*(1-t)**2*t * p1_x + 3*(1-t)*t**2 * p2_x + t**3 * p3_x
        y = (1-t)**3 * p0_y + 3*(1-t)**2*t * p1_y + 3*(1-t)*t**2 * p2_y + t**3 * p3_y
        outline.append((x, y))
    
    # 6. Upper bout (left side, waist to top)
    for i in range(resolution // 4):
        t = i / (resolution // 4 - 1)
        angle = math.pi + t * math.pi / 2  # 180° to 270° (side to top)
        x = upper_radius_x * math.cos(angle)
        y = upper_center_y + upper_radius_y * math.sin(angle)
        outline.append((x, y))
    
    # Close the loop
    if outline[0] != outline[-1]:
        outline.append(outline[0])
    
    return outline


def outline_to_dxf_r12(outline: List[Tuple[float, float]], metadata: dict) -> str:
    """
    Convert outline to DXF R12 format (AC1009).
    
    Args:
        outline: List of (x, y) points
        metadata: Dict with guitarType, dimensions, timestamp
    
    Returns:
        DXF R12 file content as string
    """
    dxf_lines = []
    
    # Header
    dxf_lines.append("0\nSECTION\n2\nHEADER")
    dxf_lines.append("9\n$ACADVER\n1\nAC1009")  # R12
    dxf_lines.append("9\n$INSUNITS\n70\n4")  # mm
    dxf_lines.append("0\nENDSEC")
    
    # Entities section
    dxf_lines.append("0\nSECTION\n2\nENTITIES")
    
    # Add metadata as comment
    dxf_lines.append("999")
    dxf_lines.append(f"Generated by Luthier's Tool Box - {metadata.get('guitarType', 'Guitar')} Body")
    dxf_lines.append("999")
    dxf_lines.append(f"Date: {metadata.get('timestamp', 'N/A')}")
    
    # LWPOLYLINE (closed polyline)
    dxf_lines.append("0\nLWPOLYLINE")
    dxf_lines.append("8\nBODY_OUTLINE")  # Layer name
    dxf_lines.append("90")
    dxf_lines.append(str(len(outline)))  # Vertex count
    dxf_lines.append("70\n1")  # Closed flag
    
    for x, y in outline:
        dxf_lines.append("10")
        dxf_lines.append(f"{x:.4f}")
        dxf_lines.append("20")
        dxf_lines.append(f"{y:.4f}")
    
    dxf_lines.append("0\nENDSEC")
    dxf_lines.append("0\nEOF")
    
    return "\n".join(dxf_lines)


def outline_to_svg(outline: List[Tuple[float, float]], metadata: dict) -> str:
    """
    Convert outline to SVG format.
    
    Args:
        outline: List of (x, y) points
        metadata: Dict with dimensions, guitarType
    
    Returns:
        SVG file content as string
    """
    # Calculate bounding box
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    # Add padding
    padding = 20
    view_width = width + 2 * padding
    view_height = height + 2 * padding
    
    # SVG path data (shift to positive coordinates)
    path_data = []
    for i, (x, y) in enumerate(outline):
        shifted_x = x - min_x + padding
        shifted_y = y - min_y + padding
        cmd = "M" if i == 0 else "L"
        path_data.append(f"{cmd}{shifted_x:.2f},{shifted_y:.2f}")
    path_data.append("Z")  # Close path
    
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{view_width:.2f}mm" height="{view_height:.2f}mm"
     viewBox="0 0 {view_width:.2f} {view_height:.2f}">
  <title>{metadata.get('guitarType', 'Guitar')} Body Outline</title>
  <desc>Generated by Luthier's Tool Box - Parametric Design</desc>
  
  <path d="{' '.join(path_data)}" 
        fill="none" stroke="black" stroke-width="0.5"/>
</svg>"""
    
    return svg


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/parametric", response_model=BodyOutlineResponse)
async def generate_parametric_body(request: GuitarDesignRequest) -> BodyOutlineResponse:
    """
    Generate guitar body outline from dimensional inputs.
    
    Workflow:
    1. Validate dimensions (sanity checks for lutherie ranges)
    2. Generate parametric outline using ellipse/bezier algorithm
    3. Return outline data + optional file export
    
    Args:
        request: GuitarDesignRequest with dimensions and export format
    
    Returns:
        BodyOutlineResponse with outline points and metadata
    
    Example:
        POST /guitar/design/parametric
        {
          "dimensions": {
            "bodyLength": 505,
            "bodyWidthUpper": 286,
            "bodyWidthLower": 394,
            "waistWidth": 240,
            "scaleLength": 648
          },
          "guitarType": "Acoustic",
          "format": "json"
        }
    """
    try:
        # Generate outline
        outline = generate_body_outline(
            request.dimensions,
            request.guitarType,
            request.resolution
        )
        
        # Calculate bounding box
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        bbox = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys)
        }
        
        # Metadata
        from datetime import datetime
        metadata = {
            "guitarType": request.guitarType,
            "units": request.units,
            "timestamp": datetime.utcnow().isoformat(),
            "generator": "Luthier's Tool Box Parametric Engine v1.0",
            "resolution": request.resolution
        }
        
        return BodyOutlineResponse(
            success=True,
            guitarType=request.guitarType,
            dimensions=request.dimensions.dict(),
            outline=outline,
            boundingBox=bbox,
            metadata=metadata,
            message=f"Generated {len(outline)} point outline for {request.guitarType} body"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/parametric/export")
async def export_parametric_body(request: GuitarDesignRequest) -> Response:
    """
    Generate and export guitar body outline as DXF or SVG file.
    
    Args:
        request: GuitarDesignRequest with dimensions and format
    
    Returns:
        File download (DXF R12 or SVG)
    
    Example:
        POST /guitar/design/parametric/export
        {
          "dimensions": {...},
          "guitarType": "Acoustic",
          "format": "dxf"
        }
    """
    try:
        # Generate outline
        outline = generate_body_outline(
            request.dimensions,
            request.guitarType,
            request.resolution
        )
        
        # Metadata
        from datetime import datetime
        metadata = {
            "guitarType": request.guitarType,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Export based on format
        if request.format == "dxf":
            content = outline_to_dxf_r12(outline, metadata)
            media_type = "application/dxf"
            filename = f"{request.guitarType}_body_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.dxf"
        elif request.format == "svg":
            content = outline_to_svg(outline, metadata)
            media_type = "image/svg+xml"
            filename = f"{request.guitarType}_body_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.svg"
        else:  # json
            import json
            content = json.dumps({
                "outline": outline,
                "dimensions": request.dimensions.dict(),
                "metadata": metadata
            }, indent=2)
            media_type = "application/json"
            filename = f"{request.guitarType}_body_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/parametric/to-cam")
async def generate_and_plan_cam(request: GuitarDesignRequest) -> Dict[str, Any]:
    """
    Generate guitar body outline and immediately plan adaptive pocket toolpath.
    
    Complete workflow:
    1. Generate parametric body outline from dimensions
    2. Convert outline to loop format
    3. Pass to adaptive pocketing engine (Module L)
    4. Return toolpath moves + stats
    
    This endpoint bridges dimension entry → CAM without intermediate DXF export.
    
    Args:
        request: GuitarDesignRequest with dimensions (must include tool_d, stepover)
    
    Returns:
        Adaptive pocket plan with moves and statistics
    
    Example:
        POST /guitar/design/parametric/to-cam
        {
          "dimensions": {
            "bodyLength": 475,
            "bodyWidthUpper": 330,
            "bodyWidthLower": 330,
            "waistWidth": 280,
            "scaleLength": 628
          },
          "guitarType": "Electric",
          "tool_d": 6.0,
          "stepover": 0.45,
          "strategy": "Spiral"
        }
    """
    try:
        # Import adaptive planner
        from ..cam.adaptive_core_l1 import polygon_area, to_toolpath
        from ..cam.adaptive_core_l2 import plan_adaptive_l2
        from ..cam.feedtime import estimate_time
        
        # Generate outline
        outline = generate_body_outline(
            request.dimensions,
            request.guitarType,
            request.resolution
        )
        
        # Convert to loop format (single outer loop, no islands)
        loop = {"pts": outline}
        
        # Default CAM parameters (can be extended to request model)
        tool_d = 6.0  # 6mm end mill
        stepover = 0.45  # 45% of tool diameter
        stepdown = 2.0  # 2mm per pass
        margin = 0.8  # 0.8mm clearance from boundary
        strategy = "Spiral"  # Continuous spiral toolpath
        smoothing = 0.3  # Arc tolerance
        feed_xy = 1200  # mm/min cutting feed
        safe_z = 5.0  # Safe retract height
        z_rough = -2.0  # Cutting depth (negative)
        
        # Plan adaptive pocket
        path_pts = plan_adaptive_l2(
            loops=[loop],
            tool_d=tool_d,
            stepover=stepover,
            stepdown=stepdown,
            margin=margin,
            strategy=strategy,
            smoothing=smoothing
        )
        
        # Convert to toolpath moves
        moves = to_toolpath(
            path_pts=path_pts,
            safe_z=safe_z,
            z_rough=z_rough,
            feed_xy=feed_xy,
            climb=True
        )
        
        # Calculate statistics
        length_mm = sum(
            ((m.get('x', 0) - moves[i-1].get('x', 0))**2 + 
             (m.get('y', 0) - moves[i-1].get('y', 0))**2 + 
             (m.get('z', 0) - moves[i-1].get('z', 0))**2)**0.5
            for i, m in enumerate(moves) if i > 0
        )
        
        area_mm2 = polygon_area(outline) if len(outline) > 2 else 0
        time_s = estimate_time(moves, feed_xy, 3000, feed_xy)  # cutting, rapid, plunge
        volume_mm3 = area_mm2 * abs(z_rough)
        
        stats = {
            "length_mm": round(length_mm, 2),
            "area_mm2": round(area_mm2, 2),
            "time_s": round(time_s, 2),
            "time_min": round(time_s / 60, 2),
            "volume_mm3": round(volume_mm3, 2),
            "move_count": len(moves)
        }
        
        return {
            "success": True,
            "guitarType": request.guitarType,
            "dimensions": request.dimensions.dict(),
            "cam_params": {
                "tool_d": tool_d,
                "stepover": stepover,
                "strategy": strategy,
                "feed_xy": feed_xy
            },
            "moves": moves[:20],  # First 20 moves for preview
            "stats": stats,
            "message": f"Generated {len(moves)} CAM moves for {request.guitarType} body"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CAM planning failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Parametric Guitar Design",
        "version": "1.0",
        "features": ["body_outline_generation", "dxf_export", "svg_export", "cam_integration"]
    }
