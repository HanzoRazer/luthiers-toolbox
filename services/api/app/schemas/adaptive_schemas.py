"""Adaptive Pocketing Schemas — Extracted from adaptive_router.py (Phase 9).

Pydantic models for adaptive pocket toolpath generation API.
Supports L.1, L.2, L.3, and M.1/M.4 feature sets.

See ADAPTIVE_POCKETING_MODULE_L.md for algorithm details.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


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

    Notes:
        - All fields optional (defaults to "inherit" mode)
        - Only non-None fields override post profile
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
    machine_profile_id: Optional[str] = Field(
        default=None,
        description="Machine profile ID for predictive feed modeling"
    )
    # M.4 parameters:
    adopt_overrides: bool = Field(
        default=False,
        description="Apply learned feed overrides from training"
    )
    session_override_factor: Optional[float] = Field(
        default=None,
        description="Session-only feed scale (Live Learn)"
    )


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
    """
    moves: List[Dict[str, Any]]
    stats: Dict[str, Any]
    overlays: List[Dict[str, Any]]
    job_int: Optional[Dict[str, Any]] = None


class GcodeIn(PlanIn):
    """
    Request model for G-code export with post-processor awareness.

    Extends PlanIn with post-processor selection and adaptive feed overrides.

    Attributes:
        post_id: Post processor ID ("GRBL", "Mach4", "LinuxCNC", etc.)
                 If None, defaults to "GRBL"
        adaptive_feed_override: Runtime override of post profile adaptive feed settings
        job_name: Filename stem for NC file (safe chars only, A-Z, 0-9, underscore)
                 E.g., "pocket_test" → "pocket_test_grbl.nc"

    Example:
        >>> gcode_in = GcodeIn(
        ...     loops=[Loop(pts=[(0,0), (100,0), (100,60), (0,60)])],
        ...     tool_d=6.0,
        ...     post_id="GRBL",
        ...     adaptive_feed_override=AdaptiveFeedOverride(mode="inline_f")
        ... )
    """
    post_id: Optional[str] = None
    adaptive_feed_override: Optional[AdaptiveFeedOverride] = None
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for NC file (safe chars only)"
    )


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
    """
    modes: Optional[List[str]] = Field(
        default=None,
        description="Subset of modes to export (comment, inline_f, mcode)"
    )
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for ZIP/NCs (safe chars only)"
    )


# Re-export all schemas for convenient import
__all__ = [
    "AdaptiveFeedOverride",
    "Loop",
    "PlanIn",
    "PlanOut",
    "GcodeIn",
    "BatchExportIn",
]
