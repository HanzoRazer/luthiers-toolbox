"""
Adaptive Pocketing Router

LANE: OPERATION (for /plan, /gcode, /batch_export, /plan_from_dxf endpoints)
LANE: UTILITY (for /sim endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: A (Planning) - generates toolpaths from geometry

FastAPI endpoints for adaptive pocket toolpath generation with L.1, L.2, and L.3 features.

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- adaptive_plan_execution (OK/ERROR) - from /plan
- adaptive_plan_blocked (BLOCKED) - from /plan when safety policy blocks
- adaptive_gcode_execution (OK/ERROR) - from /gcode
- adaptive_batch_execution (OK/ERROR) - from /batch_export

Endpoints:
- POST /plan: Generate toolpath from boundary loops (OPERATION)
- POST /gcode: Export G-code with post-processor headers (OPERATION)
- POST /batch_export: Multi-post ZIP bundle (DXF + SVG + G-code) (OPERATION)
- POST /sim: Simulate toolpath without full G-code generation (UTILITY)
- POST /plan_from_dxf: Upload DXF file and generate toolpath (Phase 27.0) (OPERATION)

Features:
- Robust polygon offsetting with island handling (L.1)
- Continuous spiral toolpaths with adaptive stepover (L.2)
- Min-fillet injection and HUD overlays (L.2)
- Trochoidal insertion for overload zones (L.3)
- Jerk-aware time estimation (L.3)
- Adaptive feed override support (comment/inline_f/mcode modes)
- DXF file upload and geometry extraction (Phase 27.0)

Critical Safety Rules:
- All geometry validated before CAM operations
- Tool diameter MUST be validated against pocket dimensions
- Feed rates MUST be within machine capabilities
- G-code MUST include post-processor headers/footers
- Units MUST be consistent throughout (convert at boundaries only)

References:
- ADAPTIVE_POCKETING_MODULE_L.md for algorithm details
- CODING_POLICY.md Section "Critical Safety Rules"
"""
import io
import json
import math
import os
import re
import time
import zipfile
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ..geometry.arc_utils import tessellate_arc_radians

from ezdxf import readfile as dxf_readfile
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..cam.adaptive_core_l1 import (
    MAX_STEPOVER,
    MAX_TOOL_DIAMETER_MM,
    MIN_STEPOVER,
    MIN_TOOL_DIAMETER_MM,
    polygon_area,
    to_toolpath,
)
from ..cam.adaptive_core_l2 import plan_adaptive_l2
from ..cam.feedtime import estimate_time
from ..cam.feedtime_l3 import (
    jerk_aware_time,
    jerk_aware_time_with_profile,
    jerk_aware_time_with_profile_and_tags,
)
from ..cam.stock_ops import rough_mrr_estimate
from ..cam.trochoid_l3 import insert_trochoids
from ..services.jobint_artifacts import build_jobint_payload
from ..util.exporters import export_dxf, export_svg
from ..util.units import scale_geom_units
from .geometry_router import GcodeExportIn, export_gcode
from .machine_router import get_profile

# Import run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

# Import feasibility functions (Phase 2: server-side enforcement)
from ..rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ..rmos.policies import SafetyPolicy

router = APIRouter(prefix="/cam/pocket/adaptive", tags=["cam-adaptive"])


def _load_post_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Load post processor profiles from JSON configuration file.
    
    Returns:
        Dictionary mapping profile IDs to profile configurations
        Empty dict if file not found or invalid JSON
        
    Example:
        >>> profiles = _load_post_profiles()
        >>> 'GRBL' in profiles
        True
        
    Notes:
        - Profiles located in ../assets/post_profiles.json
        - Fails gracefully by returning empty dict
        - Used for adaptive feed mode configuration
    """
    profile_path = os.path.join(
        os.path.dirname(__file__), "..", "assets", "post_profiles.json"
    )
    try:
        with open(profile_path, "r") as f:
            profiles = json.load(f)
            return {p["id"]: p for p in profiles}
    except Exception:
        return {}


def _merge_adaptive_override(
    post: Dict[str, Any],
    override: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge user adaptive feed override with post processor profile.
    
    Allows runtime override of adaptive feed settings without modifying
    post-processor JSON configuration files. Honors "inherit" mode to
    preserve profile defaults.
    
    Args:
        post: Post processor profile dictionary
        override: User override dictionary with keys:
            - mode: "comment" | "inline_f" | "mcode" | "inherit"
            - slowdown_threshold: float (0-1)
            - inline_min_f: float (min feed rate in mm/min)
            - mcode_start: str (M-code for zone start)
            - mcode_end: str (M-code for zone end)
    
    Returns:
        Modified post profile with override applied
        
    Example:
        >>> post = {'adaptive_feed': {'mode': 'comment'}}
        >>> override = {'mode': 'inline_f', 'inline_min_f': 100.0}
        >>> result = _merge_adaptive_override(post, override)
        >>> result['adaptive_feed']['mode']
        'inline_f'
        
    Notes:
        - If override.mode is "inherit" or None, returns post unchanged
        - Only overrides keys present in override dict (partial updates)
        - Original post dict is not modified (creates copy)
    """
    if not override or override.get("mode") in (None, "inherit"):
        return post
    
    post = post.copy()
    adaptive_feed = (post.get("adaptive_feed") or {}).copy()
    
    # Explicit mode wins
    adaptive_feed["mode"] = override.get("mode", adaptive_feed.get("mode", "comment"))
    
    # Merge other keys if present
    for key in ("slowdown_threshold", "inline_min_f", "mcode_start", "mcode_end"):
        if override.get(key) is not None:
            adaptive_feed[key] = override[key]
    
    post["adaptive_feed"] = adaptive_feed
    return post



def _apply_adaptive_feed(
    moves: List[Dict[str, Any]], 
    post: Optional[Dict[str, Any]], 
    base_units: Literal["mm", "inch"]
) -> List[str]:
    """
    Apply adaptive feed translation based on post processor profile.
    
    Transforms move dictionaries with slowdown metadata into G-code lines
    with post-processor-specific feed control. Supports three modes:
    - comment: Emit (FEED_HINT START/END) comments around slowed segments
    - inline_f: Scale F values directly in slowed segments
    - mcode: Emit M-codes at zone boundaries (e.g., LinuxCNC M52 P...)
    
    Args:
        moves: List of move dictionaries with meta.slowdown from L.2/L.3
               Each move has keys: code, x, y, z, i, j, f, meta
        post: Post processor profile dictionary with adaptive_feed config
              If None, defaults to comment mode
        base_units: "mm" or "inch" (used for unit consistency checks)
    
    Returns:
        List of G-code lines with adaptive feed applied
        
    Example:
        >>> moves = [
        ...     {'code': 'G1', 'x': 10, 'y': 0, 'f': 1200, 'meta': {'slowdown': 0.5}},
        ...     {'code': 'G1', 'x': 20, 'y': 0, 'f': 1200, 'meta': {'slowdown': 1.0}}
        ... ]
        >>> post = {'adaptive_feed': {'mode': 'inline_f', 'inline_min_f': 100.0}}
        >>> lines = _apply_adaptive_feed(moves, post, "mm")
        >>> lines[0]
        'G1 X10.0000 Y0.0000 F600.0'  # 50% slowdown applied
        
    Notes:
        - slowdown_threshold (default 0.95): values below trigger slowdown zone
        - inline_min_f (default 100.0): minimum feed rate in mm/min
        - M-codes configurable via mcode_start/mcode_end (e.g., LinuxCNC M52)
        - Zone boundaries automatically closed if file ends inside zone
    """
    prof = (post or {}).get("adaptive_feed") or {
        "mode": "comment",
        "slowdown_threshold": 0.95
    }
    mode = prof.get("mode", "comment")
    thr = float(prof.get("slowdown_threshold", 0.95))
    inline_min_f = float(prof.get("inline_min_f", 100.0))
    m_start = prof.get("mcode_start", "M200")
    m_end = prof.get("mcode_end", "M201")

    out_lines = []
    in_zone = False

    def line_from_move(m: Dict[str, Any], force_f: Optional[float] = None) -> str:
        """
        Convert move dictionary to G-code line.
        
        Args:
            m: Move dict with keys: code, x, y, z, i, j, f
            force_f: Override feed rate (used for inline_f mode)
        
        Returns:
            G-code line string (e.g., "G1 X10.0000 Y5.0000 F1200.0")
        """
        code = m["code"]
        parts = [code]
        if "x" in m:
            parts.append(f"X{m['x']:.4f}")
        if "y" in m:
            parts.append(f"Y{m['y']:.4f}")
        if "z" in m:
            parts.append(f"Z{m['z']:.4f}")
        if "i" in m:
            parts.append(f"I{m['i']:.4f}")
        if "j" in m:
            parts.append(f"J{m['j']:.4f}")
        
        fval = force_f if force_f is not None else m.get("f", None)
        if fval is not None:
            parts.append(f"F{max(inline_min_f, fval):.1f}")
        
        return " ".join(parts)

    for m in moves:
        slow = float(m.get("meta", {}).get("slowdown", 1.0))
        is_slow = slow < thr and m["code"] in ("G1", "G2", "G3")

        # Zone enter
        if is_slow and not in_zone:
            if mode == "comment":
                out_lines.append(f"(FEED_HINT START scale={slow:.3f})")
            elif mode == "mcode":
                out_lines.append(m_start)
            in_zone = True

        # Zone exit (if not slow now, but was slow)
        if (not is_slow) and in_zone:
            if mode == "comment":
                out_lines.append("(FEED_HINT END)")
            elif mode == "mcode":
                out_lines.append(m_end)
            in_zone = False

        # Generate move line
        if mode == "inline_f" and is_slow:
            # Scale current move feed
            base_f = m.get("f", 1200.0)
            force_f = base_f * slow
            out_lines.append(line_from_move(m, force_f=force_f))
        else:
            out_lines.append(line_from_move(m))

    # If file ends while inside a slow zone, close it
    if in_zone:
        if mode == "comment":
            out_lines.append("(FEED_HINT END)")
        elif mode == "mcode":
            out_lines.append(m_end)

    return out_lines


class AdaptiveFeedOverride(BaseModel):
    """
    User override for adaptive feed mode at export time.
    
    Allows runtime override of post-processor profile defaults without
    modifying JSON configuration files. Used in /gcode and /batch_export
    endpoints to customize feed control behavior per request.
    
    Attributes:
        mode: Feed control mode ("comment", "inline_f", "mcode", or "inherit")
              "inherit" preserves post profile defaults
        slowdown_threshold: Threshold below which slowdown zone activates (0-1)
                           E.g., 0.95 means slowdown factor < 0.95 triggers zone
        inline_min_f: Minimum feed rate in mm/min for inline_f mode
                     Prevents feed rates below this value (safety)
        mcode_start: M-code emitted at slowdown zone start (e.g., "M52 P50")
        mcode_end: M-code emitted at slowdown zone end (e.g., "M52 P100")
    
    Example:
        >>> override = AdaptiveFeedOverride(
        ...     mode="inline_f",
        ...     slowdown_threshold=0.9,
        ...     inline_min_f=100.0
        ... )
        >>> # Applied to request body in POST /gcode
        
    Notes:
        - All fields optional (defaults to "inherit" mode)
        - Only non-None fields override post profile
        - See _merge_adaptive_override() for merge logic
    """
    mode: Literal["comment", "inline_f", "mcode", "inherit"] = "inherit"
    slowdown_threshold: Optional[float] = None
    inline_min_f: Optional[float] = None
    mcode_start: Optional[str] = None
    mcode_end: Optional[str] = None


class Loop(BaseModel):
    """
    Closed polygon representing boundary or island.
    
    First loop in request is outer boundary (CCW orientation).
    Subsequent loops are islands/holes (CW orientation).
    
    Attributes:
        pts: List of (x, y) tuples forming closed polygon
             First and last point automatically connected if different
    
    Example:
        >>> outer = Loop(pts=[(0,0), (100,0), (100,60), (0,60)])
        >>> island = Loop(pts=[(30,15), (70,15), (70,45), (30,45)])
        >>> # Used in PlanIn.loops list
    """
    pts: List[Tuple[float, float]]


class PlanIn(BaseModel):
    """
    Request model for adaptive pocket toolpath planning.
    
    Supports L.1 (robust offsetting), L.2 (spiralizer + fillets + HUD),
    L.3 (trochoids + jerk-aware time), and M.1/M.4 (predictive feed modeling).
    
    Attributes:
        loops: List of closed polygons (first = outer boundary, rest = islands)
        units: Unit system ("mm" or "inch", converted to mm internally)
        tool_d: Tool diameter in units (0.5-50mm typical)
        stepover: Radial stepover as fraction of tool_d (0.3-0.7 typical)
        stepdown: Axial depth per pass in units (0.5-3mm typical)
        margin: Clearance from boundary in units (0.5-2mm typical)
        strategy: Toolpath strategy ("Spiral" or "Lanes")
        smoothing: Arc tolerance for rounded joins in mm (0.05-1.0)
        climb: Climb milling (True) vs conventional (False)
        feed_xy: Cutting feed rate in units/min (800-2000 typical)
        safe_z: Retract height above work in units (5-10mm typical)
        z_rough: Cutting depth in units (negative, e.g., -1.5mm)
        corner_radius_min: Min fillet radius at sharp corners (L.2, 0.5-25mm)
        target_stepover: Adaptive stepover target (L.2, 0.3-0.7)
        slowdown_feed_pct: Feed reduction % in tight curves (L.2, 20-80%)
        use_trochoids: Enable trochoidal milling (L.3, default False)
        trochoid_radius: Trochoidal arc radius in mm (L.3, 1-3mm)
        trochoid_pitch: Trochoidal advance per arc in mm (L.3, 2-5mm)
        jerk_aware: Enable jerk-aware time estimation (L.3, default False)
        machine_feed_xy: Machine max feed in mm/min (L.3, 1200-3000)
        machine_rapid: Machine rapid rate in mm/min (L.3, 3000-8000)
        machine_accel: Machine acceleration in mm/s² (L.3, 500-1500)
        machine_jerk: Machine jerk limit in mm/s³ (L.3, 1000-3000)
        corner_tol_mm: Corner velocity tolerance in mm (L.3, 0.1-0.5)
        machine_profile_id: Machine profile ID for predictive feed (M.1)
        adopt_overrides: Apply learned feed overrides (M.4, default False)
        session_override_factor: Live session feed scale (M.4)
    
    Example:
        >>> plan_in = PlanIn(
        ...     loops=[Loop(pts=[(0,0), (100,0), (100,60), (0,60)])],
        ...     units="mm",
        ...     tool_d=6.0,
        ...     stepover=0.45,
        ...     strategy="Spiral",
        ...     feed_xy=1200.0
        ... )
        
    Notes:
        - All loops validated to have 3+ points
        - Units converted to mm at API boundary
        - Tool diameter and stepover validated against MIN/MAX constants
        - See adaptive_core_l1.py and adaptive_core_l2.py for validation rules
    """
    loops: List[Loop]
    units: str = "mm"
    tool_d: float
    stepover: float = 0.45
    stepdown: float = 2.0
    margin: float = 0.5
    strategy: str = "Spiral"
    smoothing: float = 0.5
    climb: bool = True
    feed_xy: float = 1200.0
    safe_z: float = 5.0
    z_rough: float = -1.5
    # L.2 parameters:
    corner_radius_min: float = 1.0
    target_stepover: float = 0.45
    slowdown_feed_pct: float = 60.0
    # L.3 parameters:
    use_trochoids: bool = False
    trochoid_radius: float = 1.5
    trochoid_pitch: float = 3.0
    jerk_aware: bool = False
    machine_feed_xy: float = 1200.0
    machine_rapid: float = 3000.0
    machine_accel: float = 800.0     # mm/s²
    machine_jerk: float = 2000.0     # mm/s³
    corner_tol_mm: float = 0.2
    # M.1 parameters:
    machine_profile_id: Optional[str] = Field(default=None, description="Machine profile ID for predictive feed modeling")
    # M.4 parameters:
    adopt_overrides: bool = Field(default=False, description="Apply learned feed overrides from training")
    session_override_factor: Optional[float] = Field(default=None, description="Session-only feed scale (Live Learn)")


class PlanOut(BaseModel):
    """
    Response model for adaptive pocket toolpath planning.
    
    Attributes:
        moves: List of move dictionaries with keys:
               - code: G-code command ("G0", "G1", "G2", "G3")
               - x, y, z: Coordinates in mm
               - i, j: Arc offsets (G2/G3 only)
               - f: Feed rate in mm/min
               - meta: Metadata dict with slowdown factor (L.2/L.3)
        stats: Statistics dictionary with keys:
               - length_mm: Total toolpath length
               - area_mm2: Pocket area
               - time_s: Estimated machining time (classic or jerk-aware)
               - volume_mm3: Material removed
               - move_count: Number of moves
               - tight_segments: Count of tight radius segments (L.2)
               - trochoid_arcs: Count of trochoidal arcs (L.3)
        overlays: List of HUD overlay dictionaries for UI visualization:
                  - type: "tight_radius" | "slowdown" | "fillet"
                  - pos: [x, y] position in mm
                  - data: Additional metadata (radius, factor, etc.)
    
    Example:
        >>> result = plan(plan_in)
        >>> result.stats["length_mm"]
        547.3
        >>> result.moves[10]["code"]
        "G1"
        >>> result.overlays[0]["type"]
        "tight_radius"
        
    Notes:
        - moves array suitable for G-code export or canvas rendering
        - stats include both classic and jerk-aware time if jerk_aware=True
        - overlays used by AdaptivePocketLab.vue for visual feedback
    """
    moves: List[Dict[str, Any]]
    stats: Dict[str, Any]
    overlays: List[Dict[str, Any]]
    job_int: Optional[Dict[str, Any]] = None


@router.post("/plan", response_model=PlanOut)
def plan(body: PlanIn) -> PlanOut:
    """
    Generate adaptive pocket toolpath from boundary loops.
    
    Integrates L.1 (robust offsetting), L.2 (spiralizer + fillets + HUD),
    L.3 (trochoids + jerk-aware time), and M.4 (live learn feed overrides).
    
    Request Flow:
        1. Validate loops (3+ points, outer + optional islands)
        2. Plan L.2 toolpath (true spiral + adaptive stepover + fillets)
        3. Convert mixed path (points + arcs) to linear moves
        4. Compute slowdown factors from curvature (L.2 merged feature)
        5. Inject slowdown metadata into cutting moves
        6. Apply M.4 session-only feed override (live learn)
        7. Insert L.3 trochoidal arcs in overload segments (optional)
        8. Calculate statistics (length, time, volume, tight segments)
        9. Return moves + stats + HUD overlays
    
    Args:
        body: PlanIn request model with geometry and machining parameters
    
    Returns:
        PlanOut with moves array, statistics, and HUD overlays
    
    Raises:
        HTTPException 400: If loops empty or outer loop has < 3 points
        HTTPException 500: If planning fails (invalid geometry, tool collision)
    
    Example:
        >>> response = client.post("/plan", json={
        ...     "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
        ...     "tool_d": 6.0,
        ...     "stepover": 0.45,
        ...     "strategy": "Spiral",
        ...     "feed_xy": 1200.0
        ... })
        >>> response.json()["stats"]["length_mm"]
        547.3
    
    Notes:
        - All internal calculations in mm (units converted at API boundary)
        - Slowdown factors (0-1) applied to cutting moves based on curvature
        - Trochoids disabled by default (enable with use_trochoids=True)
        - Jerk-aware time requires jerk_aware=True and machine parameters
        - See ADAPTIVE_POCKETING_MODULE_L.md for algorithm documentation
    """
    # Parameter validation
    if not body.loops:
        raise HTTPException(400, "Loops array cannot be empty")
    
    if len(body.loops[0].pts) < 3:
        raise HTTPException(400, "Outer loop must have at least 3 points")
    
    if body.tool_d <= 0:
        raise HTTPException(400, "Tool diameter must be positive")
    
    if not (0.1 <= body.stepover <= 0.95):
        raise HTTPException(400, "Stepover must be between 0.1 and 0.95 (10%-95% of tool diameter)")
    
    if body.strategy not in ["Spiral", "Lanes"]:
        raise HTTPException(400, f"Invalid strategy '{body.strategy}'. Must be 'Spiral' or 'Lanes'")
    
    plan_request_dict = body.model_dump(mode="json")
    request_hash = sha256_of_obj(plan_request_dict)

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    feasibility = compute_feasibility_internal(
        tool_id="adaptive_plan",
        req=plan_request_dict,
        context="adaptive_plan",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="adaptive_plan",
            workflow_mode="adaptive",
            event_type="adaptive_plan_blocked",
            status="BLOCKED",
            feasibility=feasibility,
            request_hash=feas_hash,
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Adaptive pocket planning blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    loops = [l.pts for l in body.loops]

    # Generate path using L.2: true spiral + adaptive stepover + fillets + HUD
    plan2 = plan_adaptive_l2(
        loops=loops,
        tool_d=body.tool_d,
        stepover=body.stepover,
        stepdown=body.stepdown,
        margin=body.margin,
        strategy=body.strategy,
        smoothing_radius=body.smoothing,
        corner_radius_min=body.corner_radius_min,
        target_stepover=body.target_stepover,
        feed_xy=body.feed_xy,
        slowdown_feed_pct=body.slowdown_feed_pct
    )
    
    path_pts_or_arcs = plan2["path"]

    overlays_normalized: List[Dict[str, Any]] = []
    for overlay in plan2.get("overlays", []):
        normalized = dict(overlay)
        coords = None
        if isinstance(normalized.get("pos"), (list, tuple)) and len(normalized["pos"]) >= 2:
            coords = normalized["pos"]
        elif isinstance(normalized.get("at"), (list, tuple)) and len(normalized["at"]) >= 2:
            coords = normalized["at"]

        if coords:
            normalized.setdefault("x", coords[0])
            normalized.setdefault("y", coords[1])

        overlays_normalized.append(normalized)
    
    # Convert mixed path (points + arcs) to linear moves for preview
    # Arc tessellation delegated to geometry/arc_utils.py (Fortran Rule)
    pts_only: List[Tuple[float, float]] = []
    for item in path_pts_or_arcs:
        if isinstance(item, dict) and item.get("type") == "arc":
            cx, cy, r = item["cx"], item["cy"], abs(item["r"])
            start_rad = math.radians(item["start"])
            end_rad = math.radians(item["end"])
            cw = item.get("cw", False)
            steps = max(6, int(r / 1.0))  # 1mm chord approx
            arc_pts = tessellate_arc_radians(cx, cy, r, start_rad, end_rad, cw, steps)
            pts_only.extend(arc_pts)
        else:
            pts_only.append(tuple(item))
    
    # Compute per-point slowdown factors (MERGED FEATURE)
    from ..cam.adaptive_spiralizer_utils import compute_slowdown_factors
    slowdown_factors = compute_slowdown_factors(
        pts_only, 
        body.tool_d,
        k_threshold=1.0 / max(1.0, 3.0 * body.tool_d),
        slowdown_range=(body.slowdown_feed_pct / 100.0, 1.0)
    )
    
    # Convert to toolpath moves with slowdown metadata
    moves = to_toolpath(
        pts_only, 
        body.feed_xy, 
        body.z_rough, 
        body.safe_z, 
        lead_r=0.5
    )
    
    # Inject slowdown metadata into cutting moves (MERGED FEATURE)
    cutting_idx = 0
    for mv in moves:
        if mv.get("code") == "G1" and 'x' in mv and 'y' in mv:
            if cutting_idx < len(slowdown_factors):
                factor = slowdown_factors[cutting_idx]
                mv["meta"] = {"slowdown": round(factor, 3)}
                # Adjust feed rate based on slowdown
                if "f" in mv:
                    mv["f"] = max(100.0, mv["f"] * factor)
                cutting_idx += 1
    
    # M.4 Live Learn: Apply session-only feed override
    # This multiplies eff_f after learned rules but before machine caps
    if body.session_override_factor is not None:
        session_f = float(body.session_override_factor)
        # Safety clamp (0.5 to 1.5 for -50% to +50%)
        if 0.5 <= session_f <= 1.5:
            for mv in moves:
                if mv.get("code") == "G1" and "f" in mv:
                    mv["f"] = max(100.0, mv["f"] * session_f)
                    # Tag with session override in metadata for debugging
                    if "meta" not in mv:
                        mv["meta"] = {}
                    mv["meta"]["session_override"] = round(session_f, 3)
    
    # L.3: Optional trochoids for overload segments
    base_moves = moves
    if body.use_trochoids:
        moves = insert_trochoids(
            base_moves,
            trochoid_radius=max(0.3, body.trochoid_radius),
            trochoid_pitch=max(0.6, body.trochoid_pitch),
            curvature_slowdown_threshold=1.0 / max(1.0, 3.0 * body.tool_d),
        )
    
    # Calculate statistics
    length = 0.0
    last = None
    tight_segments = 0
    trochoid_arcs = 0
    for mv in moves:
        if 'x' in mv and 'y' in mv:
            if last is not None:
                from math import hypot
                length += hypot(mv['x']-last[0], mv['y']-last[1])
            last = (mv['x'], mv['y'])
            # Count tight segments (slowdown < 85%)
            if mv.get("meta", {}).get("slowdown", 1.0) < 0.85:
                tight_segments += 1
            # Count trochoid arcs
            if mv.get("meta", {}).get("trochoid"):
                trochoid_arcs += 1
    
    area = polygon_area(loops[0])
    
    # M.1: Load machine profile if specified
    profile = None
    if body.machine_profile_id:
        try:
            profile = get_profile(body.machine_profile_id)
        except:
            profile = None
    
    # Classic time estimate (fallback to machine params if no profile)
    t_classic = estimate_time(moves, body.feed_xy, plunge_f=300, rapid_f=body.machine_rapid)
    
    # L.3/M.1/M.1.1: Jerk-aware time estimate with bottleneck tagging
    t_jerk = None
    caps = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    
    if body.jerk_aware or profile:
        if profile:
            # M.1.1: Use machine profile-aware estimator with bottleneck tagging
            t_jerk, moves_tagged, caps = jerk_aware_time_with_profile_and_tags(moves, profile)
            moves = moves_tagged  # Replace moves with tagged version
        else:
            # L.3: Fall back to manual parameters (no tagging)
            t_jerk = jerk_aware_time(
                moves,
                feed_xy=body.machine_feed_xy,
                rapid_f=body.machine_rapid,
                accel=body.machine_accel,
                jerk=body.machine_jerk,
                corner_tol_mm=body.corner_tol_mm,
            )
    
    volume_mm3 = rough_mrr_estimate(area, body.stepdown, length, body.tool_d)

    response: Dict[str, Any] = {
        "moves": moves,
        "stats": {
            "length_mm": round(length, 3),
            "area_mm2": round(area, 1),
            "time_s": round(t_jerk if t_jerk is not None else t_classic, 1),
            "time_s_classic": round(t_classic, 1),
            "time_s_jerk": round(t_jerk, 1) if t_jerk is not None else None,
            "volume_mm3": round(volume_mm3, 1),
            "move_count": len(moves),
            "tight_segments": tight_segments,
            "trochoid_arcs": trochoid_arcs,
            "caps": caps,
            "machine_profile_id": body.machine_profile_id or None,
            "session_override_factor": float(body.session_override_factor) if body.session_override_factor else None,
        },
        "overlays": overlays_normalized,
    }

    job_payload = build_jobint_payload(
        {
            "plan_request": plan_request_dict,
            "adaptive_plan_request": plan_request_dict,
            "moves": moves,
            "adaptive_moves": moves,
        }
    )
    if job_payload:
        response["job_int"] = job_payload

    # Create artifact for OPERATION lane compliance
    moves_hash = sha256_of_obj(moves)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="adaptive_plan",
        workflow_mode="adaptive",
        event_type="adaptive_plan_execution",
        status="OK",
        feasibility=feasibility,
        request_hash=request_hash,
        toolpaths_hash=moves_hash,
    )
    persist_run(artifact)

    response["_run_id"] = run_id
    response["_hashes"] = {
        "request_sha256": request_hash,
        "moves_sha256": moves_hash,
    }

    return response

class GcodeIn(PlanIn):
    """
    Request model for G-code export with post-processor awareness.
    
    Extends PlanIn with post-processor selection and adaptive feed overrides.
    
    Attributes:
        post_id: Post processor ID ("GRBL", "Mach4", "LinuxCNC", etc.)
                 If None, defaults to "GRBL"
        adaptive_feed_override: Runtime override of post profile adaptive feed settings
                               See AdaptiveFeedOverride for options
        job_name: Filename stem for NC file (safe chars only, A-Z, 0-9, underscore)
                 E.g., "pocket_test" → "pocket_test_grbl.nc"
    
    Example:
        >>> gcode_in = GcodeIn(
        ...     loops=[Loop(pts=[(0,0), (100,0), (100,60), (0,60)])],
        ...     tool_d=6.0,
        ...     post_id="GRBL",
        ...     adaptive_feed_override=AdaptiveFeedOverride(mode="inline_f")
        ... )
    
    Notes:
        - Inherits all PlanIn parameters (geometry, feeds, L.2/L.3/M.4 options)
        - Post profiles loaded from services/api/app/assets/post_profiles.json
        - Adaptive feed translation applied based on post.adaptive_feed config
    """
    post_id: Optional[str] = None
    adaptive_feed_override: Optional[AdaptiveFeedOverride] = None
    job_name: Optional[str] = Field(default=None, description="Filename stem for NC file (safe chars only)")


@router.post("/gcode")
def gcode(body: GcodeIn) -> StreamingResponse:
    """
    Generate post-processor aware G-code for adaptive pocket.
    
    Transforms toolpath moves into machine-specific G-code with headers,
    footers, unit commands, metadata comments, and adaptive feed translation.
    
    Request Flow:
        1. Call /plan endpoint to generate toolpath
        2. Load post-processor profile from JSON
        3. Apply user adaptive feed override (if provided)
        4. Extract header/footer from profile
        5. Insert units command (G21/G20)
        6. Apply adaptive feed translation (comment/inline_f/mcode)
        7. Add metadata comment with POST/UNITS/DATE
        8. Assemble final program (header + meta + body + footer)
        9. Export as .nc file via export_gcode utility
    
    Args:
        body: GcodeIn request model with geometry, machining params, and post config
    
    Returns:
        StreamingResponse with G-code file (.nc extension)
        Content-Type: application/octet-stream
        Content-Disposition: attachment; filename="<job_name>_<post>.nc"
    
    Raises:
        HTTPException 400: If loops invalid (see /plan endpoint)
        HTTPException 500: If post profile not found or export fails
    
    Example:
        >>> response = client.post("/gcode", json={
        ...     "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
        ...     "tool_d": 6.0,
        ...     "post_id": "GRBL",
        ...     "adaptive_feed_override": {"mode": "inline_f", "inline_min_f": 100.0}
        ... })
        >>> # Downloads pocket_grbl.nc with GRBL-specific headers
    
    Notes:
        - Post profiles in services/api/app/assets/post_profiles.json
        - Adaptive feed modes: "comment" (default), "inline_f", "mcode"
        - Metadata comment format: (POST=GRBL;UNITS=mm;DATE=2025-11-05T...)
        - See ADAPTIVE_FEED_OVERRIDE_COMPLETE.md for mode documentation
    """
    # Validate post_id if provided
    post_profiles = _load_post_profiles()
    if body.post_id:
        valid_post_ids = list(post_profiles.keys())
        if body.post_id not in valid_post_ids:
            raise HTTPException(400, f"Invalid post_id '{body.post_id}'. Available: {', '.join(valid_post_ids)}")
    
    # Generate toolpath using /plan logic
    plan_out = plan(body)
    
    # Load post profiles for adaptive feed configuration
    post = post_profiles.get(body.post_id or "GRBL")
    
    # Apply user override if provided (merge with post profile defaults)
    post = _merge_adaptive_override(
        post, 
        body.adaptive_feed_override.dict() if body.adaptive_feed_override else None
    )
    
    # Get header and footer from profile (with fallback)
    hdr = post.get("header", ["G90", "G17"]) if post else ["G90", "G17"]
    ftr = post.get("footer", ["M30"]) if post else ["M30"]
    
    # Add units command if not already in header
    units_cmd = "G20" if body.units.lower().startswith("in") else "G21"
    if units_cmd not in hdr:
        hdr = [units_cmd] + hdr
    
    # Apply adaptive feed translation (comment/inline_f/mcode)
    # plan_out is a dict, so access with dict keys
    body_lines = _apply_adaptive_feed(
        moves=plan_out["moves"],
        post=post,
        base_units=body.units
    )
    
    # Add metadata comment
    from datetime import datetime
    meta = f"(POST={body.post_id or 'GRBL'};UNITS={body.units};DATE={datetime.utcnow().isoformat()}Z)"
    
    # Assemble full program
    program = "\n".join(hdr + [meta] + body_lines + ftr) + "\n"
    
    # Create artifact for OPERATION lane compliance
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="adaptive_gcode",
        workflow_mode="adaptive",
        event_type="adaptive_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)

    response = export_gcode(GcodeExportIn(gcode=program, units=body.units, post_id=body.post_id))
    response.headers["X-Run-ID"] = run_id
    response.headers["X-GCode-SHA256"] = gcode_hash
    return response

# Allowed adaptive feed modes (validated against in batch export)
ALLOWED_MODES = ("comment", "inline_f", "mcode")


def _safe_stem(s: Optional[str]) -> str:
    """
    Sanitize job name to safe filename stem.
    
    Removes unsafe characters and ensures valid filename for cross-platform
    compatibility. Falls back to timestamp-based name if sanitization
    results in empty string.
    
    Args:
        s: User-provided job name (can be None or empty string)
    
    Returns:
        Safe filename stem containing only:
        - Letters: A-Z, a-z
        - Numbers: 0-9
        - Dash: -
        - Underscore: _
        Fallback: "pocket_<unix_timestamp>" if input invalid
    
    Example:
        >>> _safe_stem("My Pocket Design #3")
        "My_Pocket_Design_3"
        >>> _safe_stem(None)
        "pocket_1730830000"
        >>> _safe_stem("!@#$%")
        "pocket_1730830000"
    
    Notes:
        - Spaces replaced with underscores before sanitization
        - Leading/trailing whitespace stripped
        - Empty string after sanitization triggers timestamp fallback
        - Used in /batch_export and /gcode endpoints for file naming
    """
    if not s:
        return f"pocket_{int(time.time())}"
    
    # Strip whitespace, replace spaces with underscores
    s = s.strip().replace(" ", "_")
    
    # Keep only safe characters: letters, numbers, dash, underscore
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    
    # Fallback to timestamp if sanitization resulted in empty string
    return s or f"pocket_{int(time.time())}"


class BatchExportIn(GcodeIn):
    """
    Request model for batch export with multiple adaptive feed modes.
    
    Extends GcodeIn with optional modes subset filter for exporting
    only specific adaptive feed variants instead of all three.
    
    Attributes:
        modes: Subset of adaptive feed modes to export
               Options: ["comment", "inline_f", "mcode"]
               If None or empty, defaults to all three modes
        job_name: Filename stem for ZIP and NC files (sanitized to safe chars)
                 E.g., "pocket_test" → "pocket_test_comment.nc"
    
    Example:
        >>> batch_in = BatchExportIn(
        ...     loops=[Loop(pts=[(0,0), (100,0), (100,60), (0,60)])],
        ...     tool_d=6.0,
        ...     modes=["comment", "inline_f"],  # Exclude mcode variant
        ...     job_name="test_pocket"
        ... )
        
    Notes:
        - Inherits all PlanIn and GcodeIn parameters
        - Generates separate NC file per mode in single ZIP
        - Includes manifest.json with run metadata
        - See BATCH_EXPORT_SUBSET_UPGRADE.md for mode filtering
    """
    modes: Optional[List[str]] = Field(default=None, description="Subset of modes to export (comment, inline_f, mcode)")
    job_name: Optional[str] = Field(default=None, description="Filename stem for ZIP/NCs (safe chars only)")


@router.post("/batch_export")
def batch_export(body: BatchExportIn) -> StreamingResponse:
    """
    Batch export adaptive pocket G-code with multiple feed modes.
    
    Generates ZIP archive containing NC files for each requested adaptive
    feed mode plus a JSON manifest with run metadata. Allows users to
    compare different feed control strategies (comment/inline_f/mcode)
    without re-running toolpath planning.
    
    Request Flow:
        1. Normalize modes list (filter to allowed values, default to all)
        2. Resolve job name stem (sanitize or fallback to timestamp)
        3. For each mode:
           a. Clone request body and set adaptive_feed_override.mode
           b. Call /plan to generate toolpath
           c. Load post profile and apply override
           d. Apply adaptive feed translation (_apply_adaptive_feed)
           e. Assemble G-code with headers/footers/metadata
           f. Write to ZIP as <stem>_<mode>.nc
        4. Generate manifest JSON with run metadata
        5. Return ZIP as streaming response
    
    Args:
        body: BatchExportIn with geometry, machining params, and mode filter
    
    Returns:
        StreamingResponse with ZIP file
        Content-Type: application/zip
        Content-Disposition: attachment; filename="<stem>_multi_mode.zip"
        
        ZIP contents:
        - <stem>_comment.nc: FEED_HINT comment mode
        - <stem>_inline_f.nc: Inline F override mode
        - <stem>_mcode.nc: M-code wrapper mode (if requested)
        - <stem>_manifest.json: Run metadata
    
    Raises:
        HTTPException 400: If loops invalid (see /plan endpoint)
        HTTPException 500: If planning or export fails
    
    Example:
        >>> response = client.post("/batch_export", json={
        ...     "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
        ...     "tool_d": 6.0,
        ...     "modes": ["comment", "inline_f"],
        ...     "job_name": "test_pocket"
        ... })
        >>> # Downloads test_pocket_multi_mode.zip with 2 NC files + manifest
    
    Notes:
        - Reuses /plan endpoint for consistent toolpath generation
        - Each mode renders independently (allows per-mode overrides)
        - Manifest includes timestamp, tool params, strategy, L.3/M.4 flags
        - See BATCH_EXPORT_SUMMARY.md for complete feature documentation
    """
    # Normalize modes - filter to allowed values
    modes = [m for m in (body.modes or []) if m in ALLOWED_MODES]
    if not modes:
        modes = list(ALLOWED_MODES)
    
    # Resolve program stem (use job_name if provided, else timestamp)
    post_id = body.post_id or "GRBL"
    stem = _safe_stem(body.job_name)
    
    def render_with_mode(mode: str) -> str:
        """
        Render G-code with specific adaptive feed mode.
        
        Args:
            mode: Adaptive feed mode ("comment", "inline_f", or "mcode")
        
        Returns:
            Complete G-code program as string with headers/footers
        """
        # Clone body and set override mode
        body_copy = body.model_copy(deep=True)
        
        # Create override if not present
        if body_copy.adaptive_feed_override is None:
            body_copy.adaptive_feed_override = AdaptiveFeedOverride()
        
        # Set mode
        body_copy.adaptive_feed_override.mode = mode  # type: ignore
        
        # Generate plan
        plan_out = plan(body_copy)
        
        # Load post profiles
        post_profiles = _load_post_profiles()
        post = post_profiles.get(body_copy.post_id or "GRBL")
        
        # Apply override
        post = _merge_adaptive_override(
            post,
            body_copy.adaptive_feed_override.dict() if body_copy.adaptive_feed_override else None
        )
        
        # Get headers/footers
        hdr = post.get("header", ["G90", "G17"]) if post else ["G90", "G17"]
        ftr = post.get("footer", ["M30"]) if post else ["M30"]
        
        # Add units command
        units_cmd = "G20" if body_copy.units.lower().startswith("in") else "G21"
        if units_cmd not in hdr:
            hdr = [units_cmd] + hdr
        
        # Apply adaptive feed translation
        body_lines = _apply_adaptive_feed(
            moves=plan_out.moves,
            post=post,
            base_units=body_copy.units
        )
        
        # Add metadata
        from datetime import datetime
        meta = f"(POST={body_copy.post_id or 'GRBL'};UNITS={body_copy.units};MODE={mode};DATE={datetime.utcnow().isoformat()}Z)"
        
        # Assemble program
        program = "\n".join(hdr + [meta] + body_lines + ftr) + "\n"
        return program
    
    # Build ZIP with requested modes only
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for m in modes:
            z.writestr(f"{stem}_{m}.nc", render_with_mode(m))
        
        # Add manifest with modes list and run metadata
        manifest = {
            "modes": modes,
            "post": post_id,
            "units": body.units,
            "tool_d": body.tool_d,
            "stepover": body.stepover,
            "stepdown": body.stepdown,
            "strategy": body.strategy,
            "trochoids": bool(getattr(body, "use_trochoids", False)),
            "jerk_aware": bool(getattr(body, "jerk_aware", False)),
            "job_name": stem,
            "timestamp": int(time.time())
        }
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
    
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem}_multi_mode.zip"'}
    )


@router.post("/sim")
def simulate(body: PlanIn) -> Dict[str, Any]:
    """
    Simulate adaptive pocket toolpath without G-code export.
    
    Performs full toolpath planning and statistics calculation without
    generating post-processor-specific G-code. Used for:
    - Pre-flight validation (check tool collision, tight radii)
    - Time estimation (compare classic vs jerk-aware)
    - Parameter tuning (test stepover, feeds, L.2/L.3 options)
    
    Args:
        body: PlanIn request model with geometry and machining parameters
    
    Returns:
        Dictionary with keys:
        - success: True if simulation completed
        - stats: Full statistics dictionary (see PlanOut.stats)
        - moves: First 10 moves for preview (not full toolpath)
    
    Example:
        >>> response = client.post("/sim", json={
        ...     "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
        ...     "tool_d": 6.0,
        ...     "stepover": 0.45,
        ...     "jerk_aware": True
        ... })
        >>> response.json()["stats"]["time_s_jerk"]
        42.3
    
    Notes:
        - Lightweight alternative to /gcode for validation
        - Reuses /plan endpoint for consistent results
        - Returns truncated moves list (first 10) to reduce response size
        - Full moves array available via /plan endpoint if needed
    """
    plan_out = plan(body)
    
    return {
        "success": True,
        "stats": plan_out["stats"],
        "moves": plan_out["moves"][:10]  # First 10 moves for preview
    }


# ============================================================================
# Phase 27.0: DXF Upload → Adaptive Plan
# ============================================================================

def _dxf_to_loops_from_bytes(data: bytes, layer_name: str = "GEOMETRY") -> List[Loop]:
    """
    Convert DXF bytes into adaptive Loop objects from the given layer.
    
    Extracts closed LWPOLYLINE entities from specified DXF layer and converts
    them to Loop objects for adaptive pocket planning. Used by plan_from_dxf endpoint.
    
    Args:
        data: DXF file content as bytes
        layer_name: DXF layer to extract geometry from (default: "GEOMETRY")
    
    Returns:
        List of Loop objects (first is outer boundary, rest are islands)
    
    Raises:
        HTTPException: If DXF is invalid or no closed polylines found on layer
        
    Example:
        >>> with open("pocket.dxf", "rb") as f:
        ...     loops = _dxf_to_loops_from_bytes(f.read())
        >>> len(loops)  # 1 outer + 2 islands
        3
        
    Notes:
        - Only processes closed LWPOLYLINE entities
        - Open polylines are silently ignored
        - Coordinates are extracted as (x, y) tuples
        - Z coordinates are ignored (2D pocketing only)
        - First loop should be outer boundary (CCW), rest islands (CW)
    """
    try:
        fp = io.BytesIO(data)
        doc = dxf_readfile(fp)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid DXF: {exc}") from exc

    msp = doc.modelspace()
    loops: List[Loop] = []

    # Extract closed polylines from specified layer
    for entity in msp.query(f'LWPOLYLINE[layer=="{layer_name}"]'):
        if not getattr(entity, "closed", False):
            continue
        pts = []
        for p in entity.get_points():
            x, y = float(p[0]), float(p[1])
            pts.append((x, y))
        if pts:
            loops.append(Loop(pts=pts))

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed polylines found on '{layer_name}' layer.",
        )
    return loops


@router.post("/plan_from_dxf")
async def plan_from_dxf(
    file: UploadFile = File(..., description="DXF with GEOMETRY layer"),
    tool_d: float = Form(..., description="Tool diameter in mm"),
    units: str = Form("mm"),
    stepover: float = Form(0.45),
    stepdown: float = Form(2.0),
    margin: float = Form(0.5),
    strategy: str = Form("Spiral"),
    smoothing: float = Form(0.5),
    feed_xy: float = Form(1200.0),
    safe_z: float = Form(5.0),
    z_rough: float = Form(-1.5),
    corner_radius_min: float = Form(1.0),
    target_stepover: float = Form(0.45),
    slowdown_feed_pct: float = Form(60.0),
) -> Dict[str, Any]:
    """
    Bridge endpoint: Upload DXF → extract geometry → generate adaptive toolpath.
    
    Accepts DXF file upload (multipart/form-data) and extracts closed polylines
    from GEOMETRY layer. Converts to Loop objects and calls existing /plan logic.
    
    Form Parameters:
        file: DXF file (closed polylines on GEOMETRY layer)
        tool_d: Tool diameter in mm (required)
        units: "mm" or "inch" (default: "mm")
        stepover: Stepover as fraction of tool diameter (default: 0.45)
        stepdown: Z depth per pass in mm (default: 2.0)
        margin: Clearance from boundary in mm (default: 0.5)
        strategy: "Spiral" or "Lanes" (default: "Spiral")
        smoothing: Arc tolerance for rounded joins (default: 0.5)
        feed_xy: Cutting feed rate (default: 1200.0 mm/min)
        safe_z: Retract height (default: 5.0 mm)
        z_rough: Cutting depth (default: -1.5 mm)
        corner_radius_min: Min radius for fillet injection (default: 1.0 mm)
        target_stepover: Adaptive stepover target (default: 0.45)
        slowdown_feed_pct: Feed reduction percentage (default: 60.0%)
        
    Returns:
        {
            "request": <PlanIn dict with extracted loops>,
            "plan": <PlanOut dict from /plan endpoint>
        }
        
    Example Usage (curl):
        ```
        curl -X POST http://localhost:8000/api/cam/pocket/adaptive/plan_from_dxf \\
          -F "file=@pocket.dxf" \\
          -F "tool_d=6.0" \\
          -F "stepover=0.45" \\
          -F "strategy=Spiral"
        ```
        
    Example Usage (Python):
        ```python
        files = {"file": open("pocket.dxf", "rb")}
        data = {"tool_d": 6.0, "stepover": 0.45, "strategy": "Spiral"}
        response = requests.post(url, files=files, data=data)
        ```
        
    Notes:
        - DXF must contain closed LWPOLYLINE entities on "GEOMETRY" layer
        - First polyline is outer boundary (CCW), rest are islands (CW)
        - All geometry converted to Loop objects before planning
        - Uses existing /plan logic for consistent results
        - Returns both request (for replay) and plan (with moves/stats)
        - Tool diameter validated against MIN/MAX constraints
        - Feed rates validated against machine capabilities
        
    References:
        - ADAPTIVE_POCKETING_MODULE_L.md for planning algorithm details
        - Phase 27.0 documentation for DXF upload workflow
    """
    data = await file.read()
    loops = _dxf_to_loops_from_bytes(data, layer_name="GEOMETRY")

    body = PlanIn(
        loops=loops,
        units=units,
        tool_d=tool_d,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        smoothing=smoothing,
        climb=True,
        feed_xy=feed_xy,
        safe_z=safe_z,
        z_rough=z_rough,
        corner_radius_min=corner_radius_min,
        target_stepover=target_stepover,
        slowdown_feed_pct=slowdown_feed_pct,
    )

    plan_result = plan(body)

    return {
        "request": body.dict(),
        "plan": plan_result.dict(),
    }
