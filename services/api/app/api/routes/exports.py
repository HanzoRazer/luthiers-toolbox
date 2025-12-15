from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

from app.api.routes.rosette_patterns import ROSETTE_PATTERNS_DB
from app.core.dxf_geometry import DxfCircle, DxfLine, load_dxf_geometries
from app.core.pdf_renderer import render_manufacturing_plan_pdf
from app.core.rosette_planner import generate_manufacturing_plan
from app.core.saw_gcode import generate_saw_slice_gcode
from app.core.saw_risk import evaluate_saw_slice_risk
from app.schemas.export_requests import (
    ManufacturingPlanExportRequest,
    SawBatchGcodeExportRequest,
)
from app.schemas.saw_slice_op import SawSliceOp, SawSliceRiskOptions
from app.schemas.saw_tool import SawToolInDB
from app.api.routes.saw_tools import SAW_TOOLS_DB

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/manufacturing-plan.json")
def export_plan_json(req: ManufacturingPlanExportRequest):
    pattern = ROSETTE_PATTERNS_DB.get(req.pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    plan = generate_manufacturing_plan(
        pattern=pattern,
        guitars=req.guitars,
        tile_length_mm=req.tile_length_mm,
        scrap_factor=req.scrap_factor,
    ).model_dump()
    plan["tile_length_mm"] = req.tile_length_mm
    plan["scrap_factor"] = req.scrap_factor

    filename = f"manufacturing_plan__{req.pattern_id}__g{req.guitars}.json"
    return JSONResponse(
        content=plan,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/manufacturing-plan.pdf")
def export_plan_pdf(req: ManufacturingPlanExportRequest):
    pattern = ROSETTE_PATTERNS_DB.get(req.pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    plan = generate_manufacturing_plan(
        pattern=pattern,
        guitars=req.guitars,
        tile_length_mm=req.tile_length_mm,
        scrap_factor=req.scrap_factor,
    ).model_dump()
    plan["tile_length_mm"] = req.tile_length_mm
    plan["scrap_factor"] = req.scrap_factor

    try:
        pdf_bytes = render_manufacturing_plan_pdf(plan)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    filename = f"manufacturing_plan__{req.pattern_id}__g{req.guitars}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _circle_ops_from_batch(batch: Dict[str, Any]) -> List[SawSliceOp]:
    base = batch["base_circle"]
    num_rings = int(batch["num_rings"])
    radial_step = float(batch["radial_step_mm"])
    radial_sign = float(batch.get("radial_sign", 1.0))

    ops: List[SawSliceOp] = []
    for idx in range(num_rings):
        radius = float(base["radius_mm"]) + radial_sign * idx * radial_step
        op = SawSliceOp(
            op_type="saw_slice",
            id=f"{batch['id']}_ring_{idx}",
            tool_id=batch["tool_id"],
            geometry_source="circle_param",
            circle={
                "center_x_mm": base["center_x_mm"],
                "center_y_mm": base["center_y_mm"],
                "radius_mm": radius,
            },
            line=None,
            dxf_path=None,
            slice_thickness_mm=float(batch["slice_thickness_mm"]),
            passes=int(batch.get("passes", 1)),
            material=batch.get("material", "hardwood"),
            workholding=batch.get("workholding", "vacuum"),
            risk_options=SawSliceRiskOptions(
                allow_aggressive=False,
                machine_gantry_span_mm=1200.0,
            ),
        )
        ops.append(op)
    return ops


def _ops_from_dxf_batch(batch: Dict[str, Any]) -> List[SawSliceOp]:
    dxf_path = batch["dxf_path"]
    layer = batch.get("layer")
    unit_scale = float(batch.get("unit_scale", 1.0))
    max_entities = batch.get("max_entities")

    geoms = load_dxf_geometries(dxf_path, layer=layer, unit_scale=unit_scale)
    if max_entities:
        geoms = geoms[: int(max_entities)]

    ops: List[SawSliceOp] = []
    for idx, geom in enumerate(geoms):
        if isinstance(geom, DxfCircle):
            circle = {
                "center_x_mm": geom.center_x_mm,
                "center_y_mm": geom.center_y_mm,
                "radius_mm": geom.radius_mm,
            }
            line = None
            source = "circle_param"
        else:
            circle = None
            line = {
                "x1_mm": geom.x1_mm,
                "y1_mm": geom.y1_mm,
                "x2_mm": geom.x2_mm,
                "y2_mm": geom.y2_mm,
            }
            source = "line_param"

        ops.append(
            SawSliceOp(
                op_type="saw_slice",
                id=f"{batch['id']}_ent_{idx}",
                tool_id=batch["tool_id"],
                geometry_source=source,
                circle=circle,
                line=line,
                dxf_path=dxf_path,
                slice_thickness_mm=float(batch.get("slice_thickness_mm", 1.0)),
                passes=int(batch.get("passes", 1)),
                material=batch.get("material", "hardwood"),
                workholding=batch.get("workholding", "vacuum"),
                risk_options=SawSliceRiskOptions(
                    allow_aggressive=False,
                    machine_gantry_span_mm=1200.0,
                ),
            )
        )

    return ops


@router.post("/saw-batch.gcode")
def export_batch_gcode(req: SawBatchGcodeExportRequest):
    batch = req.batch_op
    tool_id = batch.get("tool_id")
    tool: SawToolInDB | None = SAW_TOOLS_DB.get(tool_id)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Saw tool '{tool_id}' not found")

    geometry_source = batch.get("geometry_source")
    if geometry_source == "circle_param":
        ops = _circle_ops_from_batch(batch)
    elif geometry_source == "dxf_path":
        ops = _ops_from_dxf_batch(batch)
    else:
        raise HTTPException(status_code=400, detail="Unsupported geometry_source")

    gcode_parts: List[str] = []
    for op in ops:
        _ = evaluate_saw_slice_risk(tool, op)
        gcode_parts.append(generate_saw_slice_gcode(tool, op))

    filename = f"saw_batch__{batch.get('id', 'batch')}.gcode"
    return Response(
        content="\n".join(gcode_parts),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
