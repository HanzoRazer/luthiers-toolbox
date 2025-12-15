# services/api/app/api/routes/saw_ops.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes.saw_tools import SAW_TOOLS_DB
from app.core.dxf_geometry import DxfCircle, DxfLine, load_dxf_geometries
from app.core.saw_gcode import generate_saw_slice_gcode
from app.core.saw_risk import evaluate_saw_slice_risk
from app.schemas.dxf_guided_ops import (
    DxfGuidedBatchPreviewRequest,
    DxfGuidedSlicePreviewRequest,
)
from app.schemas.saw_slice_batch_op import SawSliceBatchOp
from app.schemas.saw_slice_op import SawSliceOp, SawSliceRiskOptions
from app.schemas.saw_tool import SawToolInDB

router = APIRouter(prefix="/saw-ops", tags=["saw-ops"])


# --- helpers ---------------------------------------------------------------

def _ensure_risk_options(op: SawSliceOp) -> SawSliceOp:
    """
    Make sure risk_options exists and has a default machine_gantry_span_mm
    for preview-only calls.
    """
    opts = op.risk_options or SawSliceRiskOptions(
        allow_aggressive=False,
        machine_gantry_span_mm=1200.0,
    )

    # If caller omitted gantry span, give a preview-safe default.
    if opts.machine_gantry_span_mm is None:
        opts.machine_gantry_span_mm = 1200.0

    op.risk_options = opts
    return op


def _circle_op_from_batch(batch: SawSliceBatchOp, ring_idx: int) -> SawSliceOp:
    """
    Helper: convert a single ring from a SawSliceBatchOp(circle_param)
    into a SawSliceOp, for risk + G-code preview.
    """
    radial_offset = batch.radial_sign * ring_idx * batch.radial_step_mm
    radius = batch.base_circle.radius_mm + radial_offset

    if radius <= 0:
        raise ValueError("Computed radius <= 0. Check radial_step_mm & radial_sign.")

    circle_dict = {
        "center_x_mm": batch.base_circle.center_x_mm,
        "center_y_mm": batch.base_circle.center_y_mm,
        "radius_mm": radius,
    }

    op = SawSliceOp(
        op_type="saw_slice",
        id=f"{batch.id}_ring_{ring_idx}",
        tool_id=batch.tool_id,
        geometry_source="circle_param",
        line=None,
        circle=circle_dict,
        dxf_path=None,
        slice_thickness_mm=batch.slice_thickness_mm,
        passes=batch.passes,
        material=batch.material,
        workholding=batch.workholding,
        risk_options=SawSliceRiskOptions(
            allow_aggressive=False,
            machine_gantry_span_mm=1200.0,
        ),
    )
    return op


# --- /saw-ops/slice/preview -----------------------------------------------

@router.post("/slice/preview")
def slice_preview(op: SawSliceOp):
    """
    === /saw-ops/slice/preview ===

    Preview risk + G-code for a *single* saw slice operation
    (line or circle geometry, DXF-ref, etc.).

    - Does NOT write JobLog (pure preview).
    - Expects the same SawSliceOp shape you use in pipelines.
    - If risk_options.machine_gantry_span_mm is missing, a preview-safe
      default of 1200 mm is applied.
    """
    tool: SawToolInDB | None = SAW_TOOLS_DB.get(op.tool_id)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Saw tool '{op.tool_id}' not found")

    op = _ensure_risk_options(op)

    risk = evaluate_saw_slice_risk(tool, op)
    gcode = generate_saw_slice_gcode(tool, op)

    return {
        "op_id": op.id,
        "tool_id": op.tool_id,
        "geometry_source": op.geometry_source,
        "material": op.material,
        "workholding": op.workholding,
        "risk": risk,
        "gcode": gcode,
    }


# --- /saw-ops/batch/preview -----------------------------------------------

@router.post("/batch/preview")
def batch_preview(batch: SawSliceBatchOp):
    """
    === /saw-ops/batch/preview ===

    Pure preview endpoint for SawSliceBatchOp.

    - Does NOT write JobLog.
    - Designed to match the RosetteMultiRingOpPanel.vue frontend call.
    - Currently focused on circle_param (multi-ring rosette mode).
    """
    # Validate tool exists
    tool: SawToolInDB | None = SAW_TOOLS_DB.get(batch.tool_id)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Saw tool '{batch.tool_id}' not found")

    if batch.geometry_source != "circle_param":
        raise HTTPException(
            status_code=400,
            detail="Only circle_param supported in RMOS batch preview. "
                   "Line mode can be added later if needed.",
        )

    slice_results = []
    gcode_fragments = []

    # Loop through rings and treat each as a single SawSliceOp
    for ring_idx in range(batch.num_rings):
        op = _circle_op_from_batch(batch, ring_idx)
        op = _ensure_risk_options(op)

        risk_result = evaluate_saw_slice_risk(tool, op)
        gcode = generate_saw_slice_gcode(tool, op)

        slice_results.append({
            "index": ring_idx,
            "kind": "ring",
            "offset_mm": batch.radial_sign * ring_idx * batch.radial_step_mm,
            "risk_grade": risk_result["risk_grade"],
            "rim_speed_m_min": risk_result["rim_speed_m_min"],
            "doc_grade": risk_result["doc_grade"],
            "gantry_grade": risk_result["gantry_grade"],
        })

        gcode_fragments.append(gcode)

    # Compute overall risk grade
    overall = "GREEN"
    for s in slice_results:
        if s["risk_grade"] == "RED":
            overall = "RED"
            break
        if s["risk_grade"] == "YELLOW" and overall == "GREEN":
            overall = "YELLOW"

    return {
        "op_id": batch.id,
        "tool_id": batch.tool_id,
        "mode": batch.geometry_source,
        "material": batch.material,
        "workholding": batch.workholding,
        "num_slices": len(slice_results),
        "overall_risk_grade": overall,
        "slice_risks": slice_results,
        "gcode": "\n".join(gcode_fragments),
    }


# --- DXF-guided previews --------------------------------------------------


@router.post("/slice/preview-dxf")
def slice_preview_dxf(req: DxfGuidedSlicePreviewRequest):
    """Preview a single saw slice derived from a DXF entity."""

    tool: SawToolInDB | None = SAW_TOOLS_DB.get(req.tool_id)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Saw tool '{req.tool_id}' not found")

    geoms = load_dxf_geometries(req.dxf_path, layer=req.layer, unit_scale=req.unit_scale)
    if not geoms:
        raise HTTPException(status_code=400, detail="No LINE/CIRCLE geometries found in DXF")

    idx = req.entity_index or 0
    if idx < 0 or idx >= len(geoms):
        raise HTTPException(status_code=400, detail=f"entity_index {idx} out of range (0..{len(geoms)-1})")

    geom = geoms[idx]
    if isinstance(geom, DxfCircle):
        op = SawSliceOp(
            op_type="saw_slice",
            id=req.op_id,
            tool_id=req.tool_id,
            geometry_source="circle_param",
            circle={
                "center_x_mm": geom.center_x_mm,
                "center_y_mm": geom.center_y_mm,
                "radius_mm": geom.radius_mm,
            },
            line=None,
            dxf_path=req.dxf_path,
            slice_thickness_mm=req.slice_thickness_mm,
            passes=req.passes,
            material=req.material,
            workholding=req.workholding,
            risk_options=SawSliceRiskOptions(
                allow_aggressive=False,
                machine_gantry_span_mm=1200.0,
            ),
        )
    else:
        op = SawSliceOp(
            op_type="saw_slice",
            id=req.op_id,
            tool_id=req.tool_id,
            geometry_source="line_param",
            line={
                "x1_mm": geom.x1_mm,
                "y1_mm": geom.y1_mm,
                "x2_mm": geom.x2_mm,
                "y2_mm": geom.y2_mm,
            },
            circle=None,
            dxf_path=req.dxf_path,
            slice_thickness_mm=req.slice_thickness_mm,
            passes=req.passes,
            material=req.material,
            workholding=req.workholding,
            risk_options=SawSliceRiskOptions(
                allow_aggressive=False,
                machine_gantry_span_mm=1200.0,
            ),
        )

    op = _ensure_risk_options(op)
    risk = evaluate_saw_slice_risk(tool, op)
    gcode = generate_saw_slice_gcode(tool, op)

    return {
        "op_id": op.id,
        "tool_id": op.tool_id,
        "geometry_source": op.geometry_source,
        "dxf_path": req.dxf_path,
        "entity_index": idx,
        "risk": risk,
        "gcode": gcode,
    }


@router.post("/batch/preview-dxf")
def batch_preview_dxf(req: DxfGuidedBatchPreviewRequest):
    """Preview a DXF-derived batch of saw slices."""

    tool: SawToolInDB | None = SAW_TOOLS_DB.get(req.tool_id)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Saw tool '{req.tool_id}' not found")

    geoms = load_dxf_geometries(req.dxf_path, layer=req.layer, unit_scale=req.unit_scale)
    if not geoms:
        raise HTTPException(status_code=400, detail="No LINE/CIRCLE geometries found in DXF")

    if req.max_entities:
        geoms = geoms[: req.max_entities]

    slice_results: list[dict[str, object]] = []
    gcode_fragments: list[str] = []

    for idx, geom in enumerate(geoms):
        if isinstance(geom, DxfCircle):
            op = SawSliceOp(
                op_type="saw_slice",
                id=f"{req.op_id}_ent_{idx}",
                tool_id=req.tool_id,
                geometry_source="circle_param",
                circle={
                    "center_x_mm": geom.center_x_mm,
                    "center_y_mm": geom.center_y_mm,
                    "radius_mm": geom.radius_mm,
                },
                line=None,
                dxf_path=req.dxf_path,
                slice_thickness_mm=req.slice_thickness_mm,
                passes=req.passes,
                material=req.material,
                workholding=req.workholding,
                risk_options=SawSliceRiskOptions(
                    allow_aggressive=False,
                    machine_gantry_span_mm=1200.0,
                ),
            )
        else:
            op = SawSliceOp(
                op_type="saw_slice",
                id=f"{req.op_id}_ent_{idx}",
                tool_id=req.tool_id,
                geometry_source="line_param",
                line={
                    "x1_mm": geom.x1_mm,
                    "y1_mm": geom.y1_mm,
                    "x2_mm": geom.x2_mm,
                    "y2_mm": geom.y2_mm,
                },
                circle=None,
                dxf_path=req.dxf_path,
                slice_thickness_mm=req.slice_thickness_mm,
                passes=req.passes,
                material=req.material,
                workholding=req.workholding,
                risk_options=SawSliceRiskOptions(
                    allow_aggressive=False,
                    machine_gantry_span_mm=1200.0,
                ),
            )

        op = _ensure_risk_options(op)
        risk = evaluate_saw_slice_risk(tool, op)
        gcode = generate_saw_slice_gcode(tool, op)

        slice_results.append(
            {
                "index": idx,
                "kind": geom.kind,
                "layer": getattr(geom, "layer", "0"),
                "risk_grade": risk["risk_grade"],
                "rim_speed_m_min": risk["rim_speed_m_min"],
                "doc_grade": risk["doc_grade"],
                "gantry_grade": risk["gantry_grade"],
            }
        )
        gcode_fragments.append(gcode)

    overall = "GREEN"
    for s in slice_results:
        if s["risk_grade"] == "RED":
            overall = "RED"
            break
        if s["risk_grade"] == "YELLOW" and overall == "GREEN":
            overall = "YELLOW"

    return {
        "op_id": req.op_id,
        "tool_id": req.tool_id,
        "mode": "dxf_path",
        "dxf_path": req.dxf_path,
        "num_slices": len(slice_results),
        "overall_risk_grade": overall,
        "slice_risks": slice_results,
        "gcode": "\n".join(gcode_fragments),
    }
