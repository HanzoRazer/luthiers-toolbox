"""
CAM Workspace API — Phase 1: Neck Pipeline Wizard

services/api/app/routers/cam/cam_workspace_router.py
Registered in router_registry with prefix=/api/cam-workspace.

Endpoints:
  GET  /api/cam-workspace/neck/operations  — list valid neck ops
  POST /api/cam-workspace/neck/evaluate   — fast gate checks, no G-code (debounced from Vue)
  POST /api/cam-workspace/neck/generate/{op} — full G-code for one op
  POST /api/cam-workspace/neck/generate-full — full G-code for all ops
  GET  /api/cam-workspace/status          — pipeline available + machine
  GET  /api/cam-workspace/machines         — list machines
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["cam-workspace"])

# ── Import pipeline under a graceful fallback ─────────────────────────────────

PIPELINE_AVAILABLE = False
_pipeline_error = ""

try:
    from app.cam.machines import BCAM_2030A, BCamMachineSpec, get_machine
    from app.cam.neck.config import (
        NeckPipelineConfig, NeckProfileType, MaterialType,
        TrussRodConfig, ProfileCarvingConfig, FretSlotConfig, NeckToolSpec,
        DEFAULT_NECK_TOOLS,
        create_lespaul_config, create_strat_config,
    )
    from app.cam.neck.orchestrator import NeckPipeline
    from app.calculators.cam_cutting_evaluator import evaluate_cut_operation
    from app.cam.preflight_gate import preflight_validate, PreflightConfig
    PIPELINE_AVAILABLE = True
except Exception as e:
    _pipeline_error = str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Request / response models
# ─────────────────────────────────────────────────────────────────────────────

class MachineContextIn(BaseModel):
    machine_id: str = "bcam_2030a"


class TrussRodIn(BaseModel):
    width_mm:             float = 6.35
    depth_mm:             float = 9.525
    length_mm:            float = 406.4
    start_offset_mm:      float = 12.7
    access_pocket_width_mm:  float = 12.7
    access_pocket_length_mm: float = 25.4


class ProfileCarvingIn(BaseModel):
    profile_type:       str   = "c_shape"   # c_shape|d_shape|v_shape|u_shape|asymmetric
    depth_at_nut_mm:    float = 20.0
    depth_at_12th_mm:   float = 22.0
    depth_at_heel_mm:   float = 25.0
    finish_allowance_mm:float = 0.75
    station_interval_mm:float = 50.8


class FretSlotIn(BaseModel):
    slot_width_mm:         float = 0.584
    slot_depth_mm:         float = 3.5
    fretboard_thickness_mm:float = 6.35
    compound_radius:       bool  = False
    radius_at_nut_mm:      float = 254.0
    radius_at_heel_mm:     float = 406.4


class ToolOverrideIn(BaseModel):
    tool_number: int
    rpm:         Optional[int]   = None
    feed_mm_min: Optional[float] = None
    stepdown_mm: Optional[float] = None


class NeckConfigIn(BaseModel):
    """Full neck pipeline config from Vue wizard sliders."""
    # Core
    scale_length_mm:  float = 628.65
    fret_count:       int   = 22
    nut_width_mm:     float = 43.0
    heel_width_mm:    float = 56.0
    material:         str   = "maple"      # maple|mahogany|rosewood|walnut

    # Sub-configs
    truss_rod:        TrussRodIn        = Field(default_factory=TrussRodIn)
    profile_carving:  ProfileCarvingIn  = Field(default_factory=ProfileCarvingIn)
    fret_slots:       FretSlotIn        = Field(default_factory=FretSlotIn)

    # Tool overrides (optional — defaults come from DEFAULT_NECK_TOOLS)
    tool_overrides:   List[ToolOverrideIn] = []

    # Operation flags
    include_truss_rod:     bool = True
    include_profile_rough: bool = True
    include_profile_finish:bool = True
    include_fret_slots:    bool = True

    # Preset shortcut
    preset: Optional[Literal["les_paul", "strat", "classical"]] = None


class EvaluateRequest(BaseModel):
    machine:    MachineContextIn = Field(default_factory=MachineContextIn)
    neck:       NeckConfigIn     = Field(default_factory=NeckConfigIn)
    strict_mode:bool = False


class GateCheck(BaseModel):
    name:    str
    status:  str          # GREEN | YELLOW | RED
    value:   Optional[float] = None
    message: str


class GateResult(BaseModel):
    overall_risk:  str            # GREEN | YELLOW | RED
    checks:        List[GateCheck]
    warnings:      List[str]
    hard_failures: List[str]
    z_ceiling_ok:  bool
    z_ceiling_msg: str = ""


class EvaluateResponse(BaseModel):
    ok:         bool
    machine_id: str
    gates:      Dict[str, GateResult]  # keyed by op name
    error:      str = ""


class GenerateRequest(BaseModel):
    machine:     MachineContextIn = Field(default_factory=MachineContextIn)
    neck:        NeckConfigIn     = Field(default_factory=NeckConfigIn)
    strict_mode: bool = False


class GenerateResponse(BaseModel):
    ok:                  bool
    op:                  str
    gcode:               str
    gate:                GateResult
    cycle_time_seconds:  float
    gcode_line_count:    int
    warnings:            List[str]
    error:               str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_pipeline_config(neck: NeckConfigIn) -> "NeckPipelineConfig":
    """Convert the Pydantic request model into a NeckPipelineConfig."""

    if neck.preset == "les_paul":
        cfg = create_lespaul_config()
    elif neck.preset == "strat":
        cfg = create_strat_config()
    else:
        tr = TrussRodConfig(
            width_mm=neck.truss_rod.width_mm,
            depth_mm=neck.truss_rod.depth_mm,
            length_mm=neck.truss_rod.length_mm,
            start_offset_mm=neck.truss_rod.start_offset_mm,
            access_pocket_width_mm=neck.truss_rod.access_pocket_width_mm,
            access_pocket_length_mm=neck.truss_rod.access_pocket_length_mm,
        )
        pc = ProfileCarvingConfig(
            profile_type=NeckProfileType(neck.profile_carving.profile_type),
            depth_at_nut_mm=neck.profile_carving.depth_at_nut_mm,
            depth_at_12th_mm=neck.profile_carving.depth_at_12th_mm,
            depth_at_heel_mm=neck.profile_carving.depth_at_heel_mm,
            finish_allowance_mm=neck.profile_carving.finish_allowance_mm,
            station_interval_mm=neck.profile_carving.station_interval_mm,
        )
        fs = FretSlotConfig(
            slot_width_mm=neck.fret_slots.slot_width_mm,
            slot_depth_mm=neck.fret_slots.slot_depth_mm,
            fretboard_thickness_mm=neck.fret_slots.fretboard_thickness_mm,
            fret_count=neck.fret_count,
            compound_radius=neck.fret_slots.compound_radius,
            radius_at_nut_mm=neck.fret_slots.radius_at_nut_mm,
            radius_at_heel_mm=neck.fret_slots.radius_at_heel_mm,
        )
        try:
            mat = MaterialType(neck.material.lower())
        except ValueError:
            mat = MaterialType.MAPLE

        cfg = NeckPipelineConfig(
            scale_length_mm=neck.scale_length_mm,
            fret_count=neck.fret_count,
            nut_width_mm=neck.nut_width_mm,
            heel_width_mm=neck.heel_width_mm,
            material=mat,
            truss_rod=tr,
            profile_carving=pc,
            fret_slots=fs,
            include_fret_slots=neck.include_fret_slots,
        )

    # Apply any tool overrides
    for ov in neck.tool_overrides:
        tool = cfg.tools.get(ov.tool_number)
        if tool:
            if ov.rpm       is not None: tool.rpm        = ov.rpm
            if ov.feed_mm_min is not None: tool.feed_mm_min = ov.feed_mm_min
            if ov.stepdown_mm is not None: tool.stepdown_mm = ov.stepdown_mm

    return cfg


def _z_ceiling_check(depth_mm: float, machine: "BCamMachineSpec") -> tuple[bool, str]:
    """Return (ok, message) for depth vs machine Z travel."""
    # Allow 5mm clearance above stock surface
    required_z = depth_mm + 5.0
    if required_z > machine.max_z_mm:
        return False, (
            f"Depth {depth_mm:.1f}mm + 5mm clearance = {required_z:.1f}mm "
            f"exceeds BCAM Z travel {machine.max_z_mm:.1f}mm"
        )
    return True, f"Depth {depth_mm:.1f}mm within Z travel ({machine.max_z_mm:.1f}mm)"


def _gate_for_router_op(
    tool: "NeckToolSpec",
    depth_mm: float,
    width_mm: Optional[float],
    material_id: str,
    machine: "BCamMachineSpec",
    stickout_mm: float = 25.0,
    is_slot: bool = False,
) -> GateResult:
    """Run evaluate_cut_operation + Z ceiling check for a router bit op.

    Args:
        stickout_mm: Collet-to-tip length. Truss rod bits are short (~15mm);
                     profile bits are longer (~25mm). Drives deflection model.
        is_slot:     True for truss rod / slot cuts. Sets WOC = tool diameter
                     (plunge cut) rather than the neck width.
    """
    tool_kind = "router_bit"
    # For slot cuts the width of cut equals the tool diameter (full slot engagement)
    woc = tool.diameter_mm if is_slot else width_mm

    # Diameter-relative chipload thresholds for lutherie tools.
    # Industry rule: min ≈ 0.4–0.5% of diameter. Fixed 0.05mm floor is for
    # production routing with large bits; it falsely flags lutherie-appropriate feeds.
    min_chipload = max(0.005, tool.diameter_mm * 0.004)   # 0.4% of diameter
    max_chipload = tool.diameter_mm * 0.10                 # 10% of diameter

    result = evaluate_cut_operation(
        tool_id=f"T{tool.tool_number}",
        material_id=material_id,
        tool_kind=tool_kind,
        feed_mm_min=tool.feed_mm_min,
        rpm=tool.rpm,
        depth_of_cut_mm=depth_mm,
        width_of_cut_mm=woc,
        tool_diameter_mm=tool.diameter_mm,
        flute_count=tool.flute_count,
    )

    checks: List[GateCheck] = []

    # Chipload — diameter-relative thresholds for lutherie tools
    chipload_mm = tool.feed_mm_min / (tool.rpm * tool.flute_count) if tool.rpm and tool.flute_count else None
    if chipload_mm is not None:
        cl_ok = min_chipload <= chipload_mm <= max_chipload
        if chipload_mm < min_chipload:
            cl_msg = f"Chipload {chipload_mm:.4f}mm below min ({min_chipload:.4f}mm) — rubbing risk"
            cl_status = "YELLOW"
        elif chipload_mm > max_chipload:
            cl_msg = f"Chipload {chipload_mm:.4f}mm above max ({max_chipload:.4f}mm) — breakage risk"
            cl_status = "RED"
        else:
            cl_msg = f"Chipload {chipload_mm:.4f}mm ✓"
            cl_status = "GREEN"
        checks.append(GateCheck(name="Chipload", status=cl_status, value=round(chipload_mm, 4), message=cl_msg))

    # Heat — always YELLOW maximum in the gate (never hard-block on heat alone).
    # High heat is a warning the operator should act on, not a program stop.
    if result.get("heat"):
        h = result["heat"]
        status = {"COOL": "GREEN", "WARM": "YELLOW", "HOT": "YELLOW"}.get(h["category"], "YELLOW")
        checks.append(GateCheck(
            name="Heat", status=status,
            value=round(h["heat_risk"], 3), message=h["message"],
        ))

    # Deflection — recalculate directly with correct WOC and stickout.
    # The evaluator already ran with woc but we want a clean independent check.
    from app.calculators.cam_cutting_evaluator import calculate_deflection as _calc_defl
    defl = _calc_defl(tool.diameter_mm, depth_mm, woc, stickout_mm=stickout_mm)
    defl_status = defl.risk
    if defl_status == "RED" and not is_slot:
        defl_status = "YELLOW"   # downgrade for multi-pass profile carving
    checks.append(GateCheck(
        name="Deflection", status=defl_status,
        value=round(defl.deflection_mm or 0, 4), message=defl.message,
    ))

    # Z ceiling
    z_ok, z_msg = _z_ceiling_check(depth_mm, machine)
    checks.append(GateCheck(
        name="Z ceiling",
        status="GREEN" if z_ok else "RED",
        value=round(depth_mm, 2),
        message=z_msg,
    ))

    # Rebuild hard_failures and warnings from OUR checks only.
    # The evaluator's hard_failures used fixed industrial thresholds (e.g. deflection
    # with 56mm WOC) — we've already re-derived each check with correct lutherie context.
    hard_failures: List[str] = []
    warnings_list: List[str] = []

    for chk in checks:
        if chk.status == "RED":
            hard_failures.append(chk.message)
        elif chk.status == "YELLOW":
            warnings_list.append(chk.message)

    # Machine envelope checks (always hard failures)
    if tool.feed_mm_min > machine.max_feed_xy:
        hard_failures.append(
            f"Feed {tool.feed_mm_min:.0f} mm/min exceeds machine max {machine.max_feed_xy:.0f} mm/min"
        )
    if tool.rpm > machine.max_rpm:
        hard_failures.append(f"RPM {tool.rpm} exceeds machine max {machine.max_rpm}")

    overall = "RED" if hard_failures else ("YELLOW" if warnings_list else "GREEN")
    return GateResult(
        overall_risk=overall, checks=checks,
        warnings=warnings_list, hard_failures=hard_failures,
        z_ceiling_ok=z_ok, z_ceiling_msg=z_msg,
    )


def _gate_for_saw_op(
    tool: "NeckToolSpec",
    slot_depth_mm: float,
    machine: "BCamMachineSpec",
) -> GateResult:
    """Run evaluate_cut_operation for the fret slot saw blade.

    DOC for the gate is tool.stepdown_mm (depth per pass), not total slot depth.
    Heat is capped at YELLOW — saw heat is a concern, not a hard block.
    """
    result = evaluate_cut_operation(
        tool_id=f"T{tool.tool_number}",
        material_id="fretboard",
        tool_kind="saw_blade",
        feed_mm_min=tool.feed_mm_min,
        rpm=tool.rpm,
        depth_of_cut_mm=tool.stepdown_mm,   # per-pass DOC, not total slot depth
        tool_diameter_mm=tool.diameter_mm,
        flute_count=tool.flute_count,
    )

    checks: List[GateCheck] = []

    if result.get("bite_per_tooth"):
        b = result["bite_per_tooth"]
        checks.append(GateCheck(
            name="Bite/tooth",
            status="GREEN" if b["in_range"] else "YELLOW",
            value=round(b["bite_mm"] or 0, 4),
            message=b["message"],
        ))
    if result.get("heat"):
        h = result["heat"]
        # Heat capped at YELLOW for saw — operator monitors, not a hard block
        status = {"COOL": "GREEN", "WARM": "YELLOW", "HOT": "YELLOW"}.get(h["category"], "YELLOW")
        checks.append(GateCheck(name="Heat", status=status, value=round(h["heat_risk"], 3), message=h["message"]))

    z_ok, z_msg = _z_ceiling_check(slot_depth_mm, machine)
    checks.append(GateCheck(name="Z ceiling", status="GREEN" if z_ok else "RED",
                             value=round(slot_depth_mm, 2), message=z_msg))

    # Kickback model requires blade_diameter >> slot_depth to be meaningful.
    # Sub-mm kerf saws (fret slots) have max_depth = dia*0.4 ≈ 0.23mm —
    # any realistic stepdown triggers HIGH kickback via pure arithmetic.
    # Skip kickback for saws with diameter < 2mm.
    if result.get("kickback") and tool.diameter_mm >= 2.0:
        kr = result["kickback"]
        status = {"LOW": "GREEN", "MEDIUM": "YELLOW", "HIGH": "YELLOW"}.get(kr["category"], "YELLOW")
        checks.append(GateCheck(name="Kickback", status=status, value=round(kr["risk_score"], 3), message=kr["message"]))

    # Rebuild from our checks — not from evaluator hard_failures
    hard_failures_out: List[str] = [c.message for c in checks if c.status == "RED"]
    warnings_out: List[str] = [c.message for c in checks if c.status == "YELLOW"]

    if tool.feed_mm_min > machine.max_feed_xy:
        hard_failures_out.append(f"Feed {tool.feed_mm_min:.0f} exceeds machine max {machine.max_feed_xy:.0f} mm/min")
    if tool.rpm > machine.max_rpm:
        hard_failures_out.append(f"RPM {tool.rpm} exceeds machine max {machine.max_rpm}")

    overall = "RED" if hard_failures_out else ("YELLOW" if warnings_out else "GREEN")
    return GateResult(overall_risk=overall, checks=checks,
                      warnings=warnings_out, hard_failures=hard_failures_out,
                      z_ceiling_ok=z_ok, z_ceiling_msg=z_msg)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

NECK_OPERATIONS = ["truss_rod", "profile_rough", "profile_finish", "fret_slots"]


@router.get("/neck/operations")
async def neck_operations():
    """Return list of valid neck pipeline operation IDs for generate/{op}."""
    return {"operations": NECK_OPERATIONS}


@router.get("/status")
async def workspace_status():
    return {
        "available": PIPELINE_AVAILABLE,
        "error": _pipeline_error if not PIPELINE_AVAILABLE else "",
        "machine": BCAM_2030A.machine_id if PIPELINE_AVAILABLE else None,
    }


@router.post("/neck/evaluate", response_model=EvaluateResponse)
async def evaluate_neck(req: EvaluateRequest):
    """
    Fast gate evaluation — no G-code generated.
    Called on every slider change (debounced 300ms in Vue).
    Returns per-operation gate results including Z ceiling check.
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(503, detail=f"Pipeline unavailable: {_pipeline_error}")

    machine = get_machine(req.machine.machine_id) or BCAM_2030A
    cfg     = _build_pipeline_config(req.neck)
    gates:  Dict[str, GateResult] = {}

    # OP10: Truss rod channel — T2 (1/8" flat end mill, short stickout, slot cut)
    # Gate uses stepdown per pass as DOC. WOC = tool diameter (slot = full engagement).
    if req.neck.include_truss_rod:
        tool = cfg.tools.get(2)
        if tool:
            gates["truss_rod"] = _gate_for_router_op(
                tool, tool.stepdown_mm,
                tool.diameter_mm,              # slot WOC = tool diameter
                cfg.material.value, machine,
                stickout_mm=15.0, is_slot=True,
            )

    # OP40: Profile roughing — T1 (1/4" ball end)
    # DOC = stepdown per pass. WOC = stepover (radial engagement per pass).
    if req.neck.include_profile_rough:
        tool = cfg.tools.get(1)
        if tool:
            gates["profile_rough"] = _gate_for_router_op(
                tool, tool.stepdown_mm,
                tool.stepover_mm, cfg.material.value, machine,
                stickout_mm=25.0, is_slot=False,
            )

    # OP45: Profile finishing — T3 (3/8" ball end)
    if req.neck.include_profile_finish:
        tool = cfg.tools.get(3)
        if tool:
            gates["profile_finish"] = _gate_for_router_op(
                tool, tool.stepdown_mm,
                tool.stepover_mm, cfg.material.value, machine,
                stickout_mm=25.0, is_slot=False,
            )

    # OP50: Fret slots — T4 (saw blade)
    if req.neck.include_fret_slots:
        tool = cfg.tools.get(4)
        if tool:
            gates["fret_slots"] = _gate_for_saw_op(
                tool, cfg.fret_slots.slot_depth_mm, machine,
            )

    return EvaluateResponse(ok=True, machine_id=machine.machine_id, gates=gates)


@router.post("/neck/generate/{op}", response_model=GenerateResponse)
async def generate_neck_op(op: str, req: GenerateRequest):
    """
    Full G-code generation for a single neck operation.
    Called only on "Generate" button press — not debounced.

    op: truss_rod | profile_rough | profile_finish | fret_slots

    RED gate → HTTP 409, no gcode returned.
    YELLOW gate → 200 OK with gcode + warnings.
    GREEN gate → 200 OK, clean.
    """
    if op not in NECK_OPERATIONS:
        raise HTTPException(422, detail=f"Unknown op {op!r}. Valid: {NECK_OPERATIONS}")

    if not PIPELINE_AVAILABLE:
        raise HTTPException(503, detail=f"Pipeline unavailable: {_pipeline_error}")

    machine = get_machine(req.machine.machine_id) or BCAM_2030A
    cfg     = _build_pipeline_config(req.neck)
    pipeline = NeckPipeline(cfg)

    # Run gate evaluation first
    if op == "truss_rod":
        tool = cfg.tools.get(2)
        gate = _gate_for_router_op(tool, tool.stepdown_mm,
                                    tool.diameter_mm, cfg.material.value, machine,
                                    stickout_mm=15.0, is_slot=True)
    elif op == "profile_rough":
        tool = cfg.tools.get(1)
        gate = _gate_for_router_op(tool, tool.stepdown_mm,
                                    tool.stepover_mm, cfg.material.value, machine,
                                    stickout_mm=25.0, is_slot=False)
    elif op == "profile_finish":
        tool = cfg.tools.get(3)
        gate = _gate_for_router_op(tool, tool.stepdown_mm,
                                    tool.stepover_mm, cfg.material.value, machine,
                                    stickout_mm=25.0, is_slot=False)
    else:  # fret_slots
        tool = cfg.tools.get(4)
        gate = _gate_for_saw_op(tool, cfg.fret_slots.slot_depth_mm, machine)

    # RED = block before generating
    if gate.overall_risk == "RED" and not req.strict_mode:
        raise HTTPException(409, detail={
            "op": op,
            "gate": gate.dict(),
            "message": "Gate RED — fix hard failures before generating G-code",
        })

    # Generate G-code
    try:
        result = pipeline.generate_operation(op)
    except (ValueError, KeyError, TypeError, RuntimeError) as exc:  # audited: CAM-generation
        raise HTTPException(500, detail=f"Generation error: {exc}")

    gcode = result.get_gcode()

    # Preflight validate
    pf_config = PreflightConfig(
        machine_bounds_mm={"x": machine.max_x_mm, "y": machine.max_y_mm, "z": machine.max_z_mm},
        safe_z_mm=machine.safe_z_mm,
        strict_mode=req.strict_mode,
    )
    try:
        pf_result = preflight_validate(gcode, pf_config)
        if pf_result.errors:
            gate.hard_failures.extend(pf_result.errors)
            gate.overall_risk = "RED"
        if pf_result.warnings:
            gate.warnings.extend(pf_result.warnings)
            if gate.overall_risk == "GREEN":
                gate.overall_risk = "YELLOW"
    except Exception:  # audited: best-effort-preflight
        pass  # preflight failure is non-blocking at this stage

    cycle_time = result.total_cut_time_seconds

    return GenerateResponse(
        ok=True,
        op=op,
        gcode=gcode,
        gate=gate,
        cycle_time_seconds=round(cycle_time, 1),
        gcode_line_count=len(result.gcode_lines),
        warnings=gate.warnings,
    )


@router.post("/neck/generate-full")
async def generate_full_neck(req: GenerateRequest):
    """
    Generate complete 4-op neck program for final download.
    Called only from Step 5 (summary). Returns .nc file as plain text.
    Gate must be GREEN or YELLOW for all ops — any RED blocks.
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(503, detail=f"Pipeline unavailable: {_pipeline_error}")

    machine  = get_machine(req.machine.machine_id) or BCAM_2030A
    cfg      = _build_pipeline_config(req.neck)
    pipeline = NeckPipeline(cfg)

    result = pipeline.generate(
        include_truss_rod=req.neck.include_truss_rod,
        include_profile_rough=req.neck.include_profile_rough,
        include_profile_finish=req.neck.include_profile_finish,
        include_fret_slots=req.neck.include_fret_slots,
    )

    gcode = result.get_gcode()
    filename = f"neck_{cfg.material.value}_{cfg.scale_length_mm:.0f}mm.nc"

    return PlainTextResponse(
        content=gcode,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/machines")
async def list_machines():
    """Return available machine profiles for the machine context selector."""
    if not PIPELINE_AVAILABLE:
        return {"machines": []}
    from app.cam.machines import list_machines as _list
    return {"machines": [
        {"id": m.machine_id, "label": m.label, "post_dialect": m.post_dialect,
         "max_z_mm": m.max_z_mm, "safe_z_mm": m.safe_z_mm}
        for m in _list()
    ]}
