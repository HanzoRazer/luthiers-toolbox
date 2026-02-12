"""
DXF → G-code Workflow API v1

The golden path for converting DXF designs to machine-ready G-code:

1. POST /dxf/upload - Upload and parse DXF file
2. POST /dxf/validate - Validate geometry for CAM
3. POST /cam/plan - Create CAM operation plan
4. POST /cam/gcode - Generate G-code from plan
5. GET  /cam/posts - List available post-processors
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/dxf", tags=["DXF Workflow"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class DxfUploadResponse(V1Response):
    """Response from DXF upload."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed DXF data: layers, entities, bounds",
        examples=[{
            "layers": ["PROFILE", "POCKETS"],
            "entity_count": 42,
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 500, "max_y": 200},
        }],
    )


class DxfValidateRequest(BaseModel):
    """Request to validate DXF geometry."""
    dxf_base64: str = Field(..., description="Base64-encoded DXF file content")
    tolerance_mm: float = Field(0.01, description="Geometric tolerance in mm")
    check_closure: bool = Field(True, description="Verify closed contours")


class DxfValidateResponse(V1Response):
    """Validation results."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "valid": True,
            "issues": [],
            "geometry": {"closed_contours": 3, "open_paths": 0},
        }],
    )


class CamPlanRequest(BaseModel):
    """Request to create CAM operation plan."""
    dxf_base64: str = Field(..., description="Base64-encoded DXF file")
    operation: str = Field("profile", description="Operation type: profile, pocket, drill")
    tool_diameter_mm: float = Field(..., description="Tool diameter in mm")
    depth_mm: float = Field(..., description="Cut depth in mm")
    stepover_percent: float = Field(40.0, description="Stepover as percentage of tool diameter")
    feed_xy: float = Field(1000.0, description="XY feedrate mm/min")
    feed_z: float = Field(200.0, description="Z feedrate mm/min")
    safe_z: float = Field(5.0, description="Safe retract height mm")


class CamPlanResponse(V1Response):
    """CAM plan ready for G-code generation."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "plan_id": "plan_abc123",
            "operations": [{"type": "profile", "passes": 3}],
            "estimated_time_min": 12.5,
        }],
    )


class GcodeRequest(BaseModel):
    """Request to generate G-code."""
    plan_id: Optional[str] = Field(None, description="Plan ID from /cam/plan")
    dxf_base64: Optional[str] = Field(None, description="Or provide DXF directly")
    dialect: str = Field("grbl", description="Post-processor: grbl, linuxcnc, fanuc, haas")
    operation: str = Field("profile", description="Operation type")
    tool_diameter_mm: float = Field(6.0, description="Tool diameter")
    depth_mm: float = Field(3.0, description="Cut depth")
    feed_xy: float = Field(1000.0, description="XY feedrate")
    feed_z: float = Field(200.0, description="Z feedrate")


class GcodeResponse(V1Response):
    """Generated G-code."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "gcode": "G21\\nG90\\nG0 Z5.000\\n...",
            "line_count": 156,
            "estimated_time_min": 8.2,
        }],
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/upload", response_model=DxfUploadResponse)
async def upload_dxf(file: UploadFile = File(...)) -> DxfUploadResponse:
    """
    Upload and parse a DXF file.

    Returns layer names, entity counts, and bounding box.
    This is the first step in the DXF → G-code workflow.
    """
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        return DxfUploadResponse(
            ok=False,
            error="File must be a .dxf file",
            hint="Upload a DXF file exported from your CAD software",
        )

    try:
        content = await file.read()

        # Delegate to existing preflight service
        from ..dxf.preflight_service import validate_dxf_bytes

        result = validate_dxf_bytes(content)

        return DxfUploadResponse(
            ok=True,
            data={
                "filename": file.filename,
                "size_bytes": len(content),
                "layers": result.get("layers", []),
                "entity_count": result.get("entity_count", 0),
                "bounds": result.get("bounds"),
            },
        )
    except Exception as e:
        return DxfUploadResponse(
            ok=False,
            error=f"Failed to parse DXF: {str(e)}",
            hint="Ensure the file is a valid DXF (R12-R2018 supported)",
        )


@router.post("/validate", response_model=DxfValidateResponse)
def validate_dxf(req: DxfValidateRequest) -> DxfValidateResponse:
    """
    Validate DXF geometry for CAM operations.

    Checks for:
    - Closed contours (required for pocketing)
    - Duplicate vertices
    - Self-intersections
    - Unit sanity (mm vs inches)
    """
    import base64

    try:
        dxf_bytes = base64.b64decode(req.dxf_base64)
    except Exception:
        return DxfValidateResponse(
            ok=False,
            error="Invalid base64 encoding",
            hint="Encode the DXF file content as base64",
        )

    try:
        from ..dxf.preflight_service import validate_dxf_bytes

        result = validate_dxf_bytes(
            dxf_bytes,
            tolerance_mm=req.tolerance_mm,
            check_closure=req.check_closure,
        )

        issues = result.get("issues", [])
        has_errors = any(i.get("severity") == "error" for i in issues)

        return DxfValidateResponse(
            ok=not has_errors,
            data={
                "valid": not has_errors,
                "issues": issues,
                "geometry": result.get("geometry", {}),
            },
            error="Validation failed - see issues" if has_errors else None,
        )
    except Exception as e:
        return DxfValidateResponse(
            ok=False,
            error=f"Validation error: {str(e)}",
            hint="Check that the DXF file is valid",
        )


@router.post("/cam/plan", response_model=CamPlanResponse)
def create_cam_plan(req: CamPlanRequest) -> CamPlanResponse:
    """
    Create a CAM operation plan from DXF geometry.

    The plan includes:
    - Toolpath strategy (profile, pocket, drill)
    - Pass depths and stepover
    - Estimated machining time
    """
    import base64
    import hashlib

    try:
        dxf_bytes = base64.b64decode(req.dxf_base64)
    except Exception:
        return CamPlanResponse(
            ok=False,
            error="Invalid base64 encoding",
        )

    # Generate plan ID from content hash
    plan_id = f"plan_{hashlib.sha256(dxf_bytes).hexdigest()[:12]}"

    # Calculate passes based on depth
    max_doc = req.tool_diameter_mm * 0.5  # 50% of tool diameter
    passes = max(1, int(req.depth_mm / max_doc + 0.99))

    return CamPlanResponse(
        ok=True,
        data={
            "plan_id": plan_id,
            "operation": req.operation,
            "tool_diameter_mm": req.tool_diameter_mm,
            "depth_mm": req.depth_mm,
            "passes": passes,
            "depth_per_pass_mm": round(req.depth_mm / passes, 3),
            "stepover_mm": round(req.tool_diameter_mm * req.stepover_percent / 100, 3),
            "estimated_time_min": passes * 2.5,  # Rough estimate
        },
    )


@router.post("/cam/gcode", response_model=GcodeResponse)
def generate_gcode(req: GcodeRequest) -> GcodeResponse:
    """
    Generate G-code from a CAM plan or DXF file.

    Supports multiple dialects:
    - grbl: GRBL 1.1+ (Arduino/hobby CNC)
    - linuxcnc: LinuxCNC/EMC2
    - fanuc: FANUC industrial
    - haas: Haas VF/UMC
    """
    if not req.dxf_base64 and not req.plan_id:
        return GcodeResponse(
            ok=False,
            error="Provide either dxf_base64 or plan_id",
            hint="Use /cam/plan first to create a plan, or provide DXF directly",
        )

    try:
        # Delegate to existing post-processor
        from ..rmos.posts.base import get_dialect_config, Dialect

        config = get_dialect_config(req.dialect)

        # Generate simple G-code (full implementation delegates to CAM engine)
        lines = [
            f"; Generated by Luthier's ToolBox API v1",
            f"; Dialect: {config.name}",
            f"; Tool: {req.tool_diameter_mm}mm, Depth: {req.depth_mm}mm",
            "",
            "G21 ; mm mode",
            "G90 ; absolute",
            "G17 ; XY plane",
            "",
            f"G0 Z{req.feed_z / 50:.3f} ; safe retract",
            "G0 X0 Y0 ; home",
            "",
            "; TODO: Full toolpath generation requires CAM engine",
            "; This is a placeholder demonstrating the API structure",
            "",
            "M5 ; spindle off",
            "M2 ; program end",
        ]

        gcode = "\n".join(lines)

        return GcodeResponse(
            ok=True,
            data={
                "gcode": gcode,
                "dialect": req.dialect,
                "line_count": len(lines),
                "estimated_time_min": 1.0,
            },
        )
    except ValueError as e:
        return GcodeResponse(
            ok=False,
            error=str(e),
            hint="Available dialects: grbl, linuxcnc, fanuc, haas, mach3, marlin",
        )


@router.get("/cam/posts")
def list_post_processors() -> V1Response:
    """
    List available G-code post-processors (dialects).

    Each post-processor formats G-code for a specific controller.
    """
    from ..rmos.posts.types import Dialect, DIALECT_CONFIGS

    posts = []
    for dialect in Dialect:
        config = DIALECT_CONFIGS[dialect]
        posts.append({
            "id": dialect.value,
            "name": config.name,
            "use_line_numbers": config.use_line_numbers,
            "comment_style": config.comment_style,
            "coord_decimals": config.coord_decimals,
        })

    return V1Response(
        ok=True,
        data={"posts": posts},
    )
