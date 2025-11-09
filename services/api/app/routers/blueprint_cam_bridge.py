"""
Blueprint → CAM Bridge Router
=============================

Connects Phase 2 Blueprint vectorization output (DXF) to existing CAM systems:
- Adaptive Pocket Engine (Module L.3)
- N17 Polygon Offset System
- DXF Preflight validation

This router leverages existing CAM infrastructure with zero duplication:
- Extract LWPOLYLINE loops from DXF
- Convert to List[Loop] format
- Pass to existing adaptive/offset planners
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Dict, Any
import ezdxf
from io import BytesIO

# Import existing CAM systems
from ..cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath
from ..util.units import scale_geom_units
from ..cam.contour_reconstructor import reconstruct_contours_from_dxf
from ..cam.dxf_preflight import DXFPreflight, generate_html_report, PreflightReport

router = APIRouter(prefix="/cam/blueprint", tags=["blueprint-cam-bridge"])


# ============================================================================
# Models
# ============================================================================

class Loop(BaseModel):
    """Polygon loop (closed path) - matches adaptive_router.py"""
    pts: List[Tuple[float, float]]


class BlueprintToAdaptiveRequest(BaseModel):
    """Request for Blueprint → Adaptive pocket toolpath generation"""
    # DXF parsing
    layer_name: str = Field(default="GEOMETRY", description="DXF layer to extract contours from")
    
    # Adaptive pocket parameters (required)
    tool_d: float = Field(..., description="Tool diameter in mm", gt=0)
    stepover: float = Field(default=0.45, description="Stepover as fraction of tool diameter", gt=0, le=1.0)
    stepdown: float = Field(default=2.0, description="Depth per pass in mm", gt=0)
    margin: float = Field(default=0.5, description="Margin from boundary in mm", ge=0)
    strategy: str = Field(default="Spiral", description="Toolpath strategy: Spiral or Lanes")
    smoothing: float = Field(default=0.3, description="Arc tolerance for rounded joins (mm)", ge=0.05, le=1.0)
    
    # Machining parameters
    climb: bool = Field(default=True, description="Climb milling (true) or conventional (false)")
    feed_xy: float = Field(default=1200, description="Cutting feed rate in mm/min", gt=0)
    feed_z: float = Field(default=600, description="Plunge feed rate in mm/min", gt=0)
    rapid: float = Field(default=3000, description="Rapid traverse rate in mm/min", gt=0)
    safe_z: float = Field(default=5, description="Safe Z height in mm", gt=0)
    z_rough: float = Field(default=-1.5, description="Cutting depth in mm", lt=0)
    
    # Optional: Units (always mm internally)
    units: str = Field(default="mm", description="Output units (mm or inch)")


class BlueprintToAdaptiveResponse(BaseModel):
    """Response with adaptive pocket toolpath"""
    loops_extracted: int = Field(..., description="Number of closed loops extracted from DXF")
    loops: List[Loop] = Field(..., description="Extracted loops (first=outer, rest=islands)")
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves (G0/G1/G2/G3)")
    stats: Dict[str, Any] = Field(..., description="Toolpath statistics (length, time, volume)")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal issues during processing")


# ============================================================================
# DXF Extraction Utilities
# ============================================================================

def extract_loops_from_dxf(dxf_bytes: bytes, layer_name: str = "GEOMETRY") -> Tuple[List[Loop], List[str]]:
    """
    Extract closed LWPOLYLINE loops from DXF file.
    
    Args:
        dxf_bytes: DXF file content
        layer_name: Layer to extract from (default: GEOMETRY)
    
    Returns:
        (loops, warnings) where loops is List[Loop] and warnings is List[str]
    """
    warnings = []
    loops = []
    
    try:
        # Write bytes to temp file and read with ezdxf (avoids text/binary issues)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
            tmp.write(dxf_bytes)
            tmp_path = tmp.name
        
        try:
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
        finally:
            import os
            os.unlink(tmp_path)
        
        # Query for LWPOLYLINE entities on specified layer
        # Note: ezdxf query syntax is sensitive - filter manually for layer
        all_entities = list(msp)
        all_lwpolylines = [e for e in all_entities if e.dxftype() == 'LWPOLYLINE']
        entities = [e for e in all_lwpolylines if e.dxf.layer == layer_name]
        
        # Debug: Log what we found
        if not all_entities:
            warnings.append(f"DXF modelspace is empty")
        elif not all_lwpolylines:
            entity_types = list(set([e.dxftype() for e in all_entities]))
            warnings.append(f"No LWPOLYLINE entities found. Entity types: {entity_types}")
        
        if not entities:
            if all_lwpolylines:
                layers_found = list(set([e.dxf.layer for e in all_lwpolylines]))
                warnings.append(f"No LWPOLYLINE on layer '{layer_name}'. Found layers: {layers_found}")
            else:
                warnings.append(f"No LWPOLYLINE entities found on layer '{layer_name}'")
            # Try fallback to all LWPOLYLINE entities
            entities = list(msp.query('LWPOLYLINE'))
            if entities:
                warnings.append(f"Found {len(entities)} LWPOLYLINE entities on other layers, using those instead")
        
        # Extract points from each closed LWPOLYLINE
        for entity in entities:
            if not entity.closed:
                warnings.append(f"Skipping open LWPOLYLINE (not closed)")
                continue
            
            try:
                # Get points (x, y) - ignore bulge for now
                points = [(p[0], p[1]) for p in entity.get_points()]
                
                if len(points) < 3:
                    warnings.append(f"Skipping LWPOLYLINE with only {len(points)} points (need at least 3)")
                    continue
                
                # Remove duplicate last point if it equals first (some CAD systems add it)
                if len(points) > 1 and points[0] == points[-1]:
                    points = points[:-1]
                
                loops.append(Loop(pts=points))
            
            except Exception as e:
                warnings.append(f"Error extracting LWPOLYLINE points: {str(e)}")
        
        if not loops:
            warnings.append("No valid closed loops extracted from DXF")
    
    except ezdxf.DXFError as e:
        warnings.append(f"DXF parsing error: {str(e)}")
    except Exception as e:
        warnings.append(f"Unexpected error reading DXF: {str(e)}")
    
    return loops, warnings


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/reconstruct-contours")
async def reconstruct_contours(
    file: UploadFile = File(..., description="DXF file with primitive geometry (LINE + SPLINE)"),
    layer_name: str = "Contours",
    tolerance: float = 0.1,
    min_loop_points: int = 3
):
    """
    **Phase 3.1: Contour Reconstruction**
    
    Chains primitive DXF geometry (LINE + SPLINE) into closed LWPOLYLINE loops.
    
    **Problem:**
    CAD drawings often use disconnected LINE and SPLINE primitives instead of
    closed paths. This endpoint reconstructs closed contours by:
    1. Building connectivity graph from endpoints
    2. Finding cycles using depth-first search
    3. Sampling splines to polyline segments
    4. Classifying loops (outer boundary vs islands)
    
    **Use Case:**
    Gibson L-00 blueprint has 48 LINEs + 33 SPLINEs on "Contours" layer.
    This endpoint converts them to closed loops for CAM processing.
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/cam/blueprint/reconstruct-contours \\
      -F "file=@Gibson_L-00.dxf" \\
      -F "layer_name=Contours" \\
      -F "tolerance=0.1"
    ```
    
    **Returns:**
    - loops: List of closed contours (first = outer, rest = islands)
    - stats: Geometry analysis (lines, splines, cycles found)
    - warnings: Non-fatal issues during reconstruction
    """
    # Validate file type
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="Only DXF files are supported")
    
    # Read DXF file
    try:
        dxf_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    # Reconstruct contours
    try:
        result = reconstruct_contours_from_dxf(
            dxf_bytes=dxf_bytes,
            layer_name=layer_name,
            tolerance=tolerance,
            min_loop_points=min_loop_points
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contour reconstruction failed: {str(e)}"
        )
    
    if not result.loops:
        raise HTTPException(
            status_code=422,
            detail=f"No closed contours found. Warnings: {'; '.join(result.warnings)}"
        )
    
    return {
        "success": True,
        "loops": [loop.dict() for loop in result.loops],
        "outer_loop_idx": result.outer_loop_idx,
        "stats": result.stats,
        "warnings": result.warnings,
        "message": f"Reconstructed {len(result.loops)} closed contours from {result.stats.get('lines_found', 0)} lines and {result.stats.get('splines_found', 0)} splines"
    }


@router.post("/preflight")
async def dxf_preflight(
    file: UploadFile = File(..., description="DXF file to validate"),
    format: str = "json"  # "json" or "html"
):
    """
    **Phase 3.2: DXF Preflight Validation**
    
    Validates DXF files before CAM processing to catch issues early.
    Based on nc_lint.py pattern from legacy pipeline.
    
    **Checks:**
    - ✅ Layer validation (required layers present)
    - ✅ Closed path validation (all LWPOLYLINE closed)
    - ✅ Entity type validation (CAM-compatible entities)
    - ✅ Dimension validation (reasonable sizes for guitar lutherie)
    - ✅ Geometry sanity (no zero-length segments, degenerate paths)
    
    **Severity Levels:**
    - ERROR: Must fix (blocks CAM processing)
    - WARNING: Should fix (may cause issues)
    - INFO: Nice to know (optimization suggestions)
    
    **Example:**
    ```bash
    # JSON output
    curl -X POST http://localhost:8000/api/cam/blueprint/preflight \\
      -F "file=@Gibson_L-00.dxf" \\
      -F "format=json"
    
    # HTML report (like nc_lint.py)
    curl -X POST http://localhost:8000/api/cam/blueprint/preflight \\
      -F "file=@Gibson_L-00.dxf" \\
      -F "format=html" \\
      > preflight_report.html
    ```
    
    **Returns:**
    - JSON: PreflightReport with issues array
    - HTML: Visual report with color-coded issues
    """
    # Validate file type
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="Only DXF files are supported")
    
    # Read DXF file
    try:
        dxf_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    # Run preflight checks
    try:
        preflight = DXFPreflight(dxf_bytes, filename=file.filename)
        report = preflight.run_all_checks()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preflight validation failed: {str(e)}"
        )
    
    # Return in requested format
    if format.lower() == "html":
        html = generate_html_report(report)
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html, status_code=200)
    else:
        # JSON format
        return {
            "filename": report.filename,
            "dxf_version": report.dxf_version,
            "passed": report.passed,
            "total_entities": report.total_entities,
            "layers": report.layers,
            "issues": [
                {
                    "severity": issue.severity,
                    "message": issue.message,
                    "category": issue.category,
                    "layer": issue.layer,
                    "entity_handle": issue.entity_handle,
                    "entity_type": issue.entity_type,
                    "suggestion": issue.suggestion
                }
                for issue in report.issues
            ],
            "stats": report.stats,
            "summary": {
                "errors": report.error_count(),
                "warnings": report.warning_count(),
                "info": report.info_count()
            },
            "timestamp": report.timestamp
        }


@router.post("/to-adaptive", response_model=BlueprintToAdaptiveResponse)
async def blueprint_to_adaptive(
    file: UploadFile = File(..., description="DXF file from Phase 2 vectorization"),
    layer_name: str = "GEOMETRY",
    tool_d: float = 6.0,
    stepover: float = 0.45,
    stepdown: float = 2.0,
    margin: float = 0.5,
    strategy: str = "Spiral",
    smoothing: float = 0.3,
    climb: bool = True,
    feed_xy: float = 1200,
    feed_z: float = 600,
    rapid: float = 3000,
    safe_z: float = 5.0,
    z_rough: float = -1.5,
    units: str = "mm"
):
    """
    Blueprint → Adaptive Pocket Bridge
    ===================================
    
    Converts Phase 2 DXF vectorization output to adaptive pocket toolpath.
    
    **Workflow:**
    1. Extract closed LWPOLYLINE loops from DXF (GEOMETRY layer)
    2. Pass to existing adaptive pocket planner (Module L.1)
    3. Generate toolpath with island avoidance
    4. Return moves + statistics
    
    **Integration Points:**
    - Uses `plan_adaptive_l1()` from adaptive_core_l1.py (robust pyclipper offsetting)
    - First loop = outer boundary, rest = islands (keepout zones)
    - Zero conversion needed - DXF points map directly to Loop.pts format
    
    **Example Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/cam/blueprint/to-adaptive \\
      -F "file=@guitar_body.dxf" \\
      -F "tool_d=6.0" \\
      -F "stepover=0.45" \\
      -F "strategy=Spiral"
    ```
    """
    # Validate file type
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="Only DXF files are supported")
    
    # Read DXF file
    try:
        dxf_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    # Extract loops from DXF
    loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name)
    
    if not loops:
        raise HTTPException(
            status_code=422,
            detail=f"No valid closed loops found in DXF. Warnings: {'; '.join(warnings)}"
        )
    
    # Convert Loop models to list of point lists for adaptive planner
    loops_data = [loop.pts for loop in loops]
    
    # Call existing adaptive planner (Module L.1)
    try:
        path_pts = plan_adaptive_l1(
            loops=loops_data,
            tool_d=tool_d,
            stepover=stepover,
            stepdown=stepdown,
            margin=margin,
            strategy=strategy,
            smoothing_radius=smoothing  # Note: parameter name is smoothing_radius in L.1
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Adaptive planner error: {str(e)}"
        )
    
    # Convert to toolpath moves
    moves = to_toolpath(
        path_pts=path_pts,
        z_rough=z_rough,
        safe_z=safe_z,
        feed_xy=feed_xy,
        lead_r=0.0  # No lead-in for now
    )
    
    # Calculate statistics
    total_length = 0.0
    cutting_moves = 0
    for i in range(1, len(moves)):
        move = moves[i]
        prev = moves[i-1]
        
        if move.get('code') == 'G1':
            dx = move.get('x', prev.get('x', 0)) - prev.get('x', 0)
            dy = move.get('y', prev.get('y', 0)) - prev.get('y', 0)
            dz = move.get('z', prev.get('z', 0)) - prev.get('z', 0)
            total_length += (dx**2 + dy**2 + dz**2)**0.5
            cutting_moves += 1
    
    # Estimate time (classic method)
    time_s = (total_length / feed_xy) * 60 * 1.1  # 10% overhead
    
    # Calculate volume (approximate)
    # TODO: Use actual boundary area calculation
    volume_mm3 = total_length * tool_d * abs(z_rough)
    
    stats = {
        "length_mm": round(total_length, 2),
        "time_s": round(time_s, 1),
        "time_min": round(time_s / 60, 2),
        "move_count": len(moves),
        "cutting_moves": cutting_moves,
        "volume_mm3": round(volume_mm3, 0)
    }
    
    return BlueprintToAdaptiveResponse(
        loops_extracted=len(loops),
        loops=loops,
        moves=moves,
        stats=stats,
        warnings=warnings
    )


@router.get("/health")
def health_check():
    """Health check for blueprint CAM bridge"""
    return {
        "status": "ok",
        "bridge": "blueprint-to-cam",
        "phase": "3.2",
        "endpoints": [
            "/reconstruct-contours",
            "/preflight", 
            "/to-adaptive"
        ],
        "features": {
            "contour_reconstruction": "Phase 3.1 - LINE/SPLINE chaining",
            "dxf_preflight": "Phase 3.2 - Validation system",
            "adaptive_l1": "Available - Robust pyclipper offsetting",
            "n17_offset": "Planned",
        }
    }
