"""
Blueprint CAM Adaptive Router
=============================

DXF to adaptive pocket toolpath integration.

Endpoints:
- POST /to-adaptive: Convert DXF to adaptive pocket toolpath
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..blueprint_cam_bridge_schemas import BlueprintToAdaptiveResponse
from ...cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath

from .extraction import extract_loops_from_dxf

router = APIRouter(tags=["blueprint-cam-bridge"])


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
    Blueprint to Adaptive Pocket Bridge

    Converts Phase 2 DXF vectorization output to adaptive pocket toolpath.

    Workflow:
        1. Extract closed LWPOLYLINE loops from DXF (GEOMETRY layer)
        2. Pass to existing adaptive pocket planner (Module L.1)
        3. Generate toolpath with island avoidance
        4. Return moves + statistics

    Args:
        file: DXF file with closed LWPOLYLINE loops
        layer_name: Layer to extract from (default: GEOMETRY)
        tool_d: Tool diameter in mm
        stepover: Stepover as fraction of tool diameter (0-1.0)
        stepdown: Depth per pass in mm
        margin: Clearance from boundary in mm
        strategy: "Spiral" or "Lanes"
        smoothing: Arc tolerance for rounded joins in mm
        climb: True for climb milling, False for conventional
        feed_xy: Cutting feed rate in mm/min
        feed_z: Plunge feed rate in mm/min
        rapid: Rapid feed rate in mm/min
        safe_z: Retract height in mm
        z_rough: Cutting depth in mm (negative)
        units: "mm" or "inch"

    Returns:
        BlueprintToAdaptiveResponse with moves, stats, warnings

    Raises:
        HTTPException 422: No valid closed loops found
        HTTPException 500: Adaptive planner error
    """
    # Security patch: Validate file size and extension before reading
    from app.cam.dxf_upload_guard import read_dxf_with_validation

    dxf_bytes = await read_dxf_with_validation(file)

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
            smoothing_radius=smoothing
        )
    except HTTPException:
        raise
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
        lead_r=0.0
    )

    # Calculate statistics
    total_length = 0.0
    cutting_moves = 0
    for i in range(1, len(moves)):
        move = moves[i]
        prev = moves[i - 1]

        if move.get('code') == 'G1':
            dx = move.get('x', prev.get('x', 0)) - prev.get('x', 0)
            dy = move.get('y', prev.get('y', 0)) - prev.get('y', 0)
            dz = move.get('z', prev.get('z', 0)) - prev.get('z', 0)
            total_length += (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
            cutting_moves += 1

    # Estimate time (classic method)
    time_s = (total_length / feed_xy) * 60 * 1.1  # 10% overhead

    # Calculate volume (approximate)
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
