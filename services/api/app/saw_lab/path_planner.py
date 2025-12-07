"""
Saw Lab 2.0 - Path Planner

Plans cutting paths for saw blade operations.

Contains:
- NEW: Saw Path Planner 2.1 (function-based, RMOS 2.0 preferred API)
  - SawPlannerConfig, SawCutOperation, SawCutPlan
  - plan_saw_cuts_for_board() - main entry point
  
- LEGACY: SawPathPlanner class - kept for backward compatibility
  - plan_cuts(), _plan_dado_cuts(), _plan_through_cuts()
"""
from __future__ import annotations

from typing import List, Dict, Any, Literal, Optional
import os
from pathlib import Path

from pydantic import BaseModel, Field

from .models import SawContext, SawDesign
from .geometry import SawGeometryEngine


# =============================================================================
# NEW: Saw Path Planner 2.1 (function-based, RMOS 2.0 preferred API)
# =============================================================================

CutType = Literal["RIP", "CROSSCUT", "TRIM", "OTHER"]


class SawPlannerConfig(BaseModel):
    """
    Planner-level knobs for trim, scrap, and ordering behavior.
    In the future this can be built from SawLabConfig or RMOS context.
    """
    leading_trim_mm: float = 0.0
    trailing_trim_mm: float = 0.0
    min_scrap_length_mm: float = 20.0

    # Cut ordering strategy for the target pieces
    ordering_strategy: Literal["AS_GIVEN", "LONGEST_FIRST"] = "AS_GIVEN"


class SawCutOperation(BaseModel):
    """
    Represents a single conceptual saw cut along the stock.
    """
    op_id: str = Field(..., description="Stable identifier for this cut in the plan.")
    sequence_index: int = Field(..., description="Order in which this cut should be executed.")
    cut_type: CutType = Field(..., description="RIP / CROSSCUT / TRIM / OTHER.")
    start_offset_mm: float = Field(
        ...,
        description="Distance from the stock reference (e.g. left end) to the start of the cut.",
    )
    cut_length_mm: float = Field(
        ...,
        description="Nominal length of the cut along the stock.",
    )
    kerf_mm: float = Field(
        ...,
        description="Kerf assumed for this cut (usually blade.kerf_mm).",
    )
    description: str = Field(
        "",
        description="Human-readable description of the operation.",
    )


class SawCutPlan(BaseModel):
    """
    Full plan for cutting one stock piece into requested lengths.
    """
    operations: List[SawCutOperation] = Field(default_factory=list)
    total_kerf_loss_mm: float = 0.0
    total_piece_length_mm: float = 0.0
    scrap_length_mm: float = 0.0
    material_utilization: float = 0.0  # 0..1
    is_feasible: bool = True
    warnings: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Saw Cut Context for 2.1 Planner
# ---------------------------------------------------------------------------

class SawBladeSpec(BaseModel):
    """Blade specification for path planning."""
    kerf_mm: float = Field(default=3.0, ge=0.5, le=10.0)
    diameter_mm: float = Field(default=254.0, ge=100.0, le=600.0)
    tooth_count: int = Field(default=24, ge=10, le=120)


class SawMaterialSpec(BaseModel):
    """Material specification for path planning."""
    material_id: Optional[str] = None
    hardness: str = "MEDIUM"  # SOFT, MEDIUM, HARD
    density_kgm3: float = 700.0


class SawCutContext(BaseModel):
    """
    Context for 2.1 path planner.
    Provides blade, material, and stock information.
    """
    blade: SawBladeSpec = Field(default_factory=SawBladeSpec)
    material: SawMaterialSpec = Field(default_factory=SawMaterialSpec)
    stock_length_mm: Optional[float] = None
    desired_piece_lengths_mm: List[float] = Field(default_factory=list)


class SawLabConfig(BaseModel):
    """
    Configuration for Saw Lab operations.
    Can host planner defaults in the future.
    """
    default_safe_z_mm: float = 15.0
    default_feed_rate_mm_per_min: float = 3000.0


# ---------------------------------------------------------------------------
# Internal helpers (2.1 implementations)
# ---------------------------------------------------------------------------

def _compute_basic_yield(
    stock_length_mm: float,
    desired_piece_lengths_mm: List[float],
    kerf_mm: float,
    planner_cfg: SawPlannerConfig,
) -> tuple[bool, float, float, float, List[str]]:
    """
    Compute a trim-aware, kerf-aware, scrap-aware yield check.

    Returns:
        (is_feasible, total_piece_length_mm, total_kerf_loss_mm, scrap_length_mm, warnings[])
    """
    warnings: List[str] = []

    if stock_length_mm <= 0.0:
        return False, 0.0, 0.0, 0.0, ["Stock length is zero or negative."]

    if not desired_piece_lengths_mm:
        # Only trims / scrap.
        total_pieces = 0.0
        total_kerf = 0.0
        required = planner_cfg.leading_trim_mm + planner_cfg.trailing_trim_mm
        scrap = stock_length_mm - required

        feasible = scrap >= planner_cfg.min_scrap_length_mm
        if not feasible:
            warnings.append(
                "Stock does not have enough length to satisfy trims and minimum scrap."
            )
        return feasible, total_pieces, total_kerf, max(scrap, 0.0), warnings

    total_pieces = sum(desired_piece_lengths_mm)
    num_cuts = max(len(desired_piece_lengths_mm) - 1, 0)
    total_kerf = num_cuts * kerf_mm

    required = (
        total_pieces
        + total_kerf
        + planner_cfg.leading_trim_mm
        + planner_cfg.trailing_trim_mm
    )

    scrap = stock_length_mm - required

    if scrap < 0:
        warnings.append(
            "Requested pieces + kerf + trims exceed available stock length."
        )
        return False, total_pieces, total_kerf, 0.0, warnings

    if scrap < planner_cfg.min_scrap_length_mm:
        warnings.append(
            f"Scrap ({scrap:.1f} mm) is smaller than the minimum usable scrap "
            f"({planner_cfg.min_scrap_length_mm:.1f} mm)."
        )
        feasible = False
    else:
        feasible = True

    return feasible, total_pieces, total_kerf, scrap, warnings


def _order_pieces(
    desired_piece_lengths_mm: List[float],
    planner_cfg: SawPlannerConfig,
) -> List[float]:
    """Apply the requested ordering strategy to the piece list."""
    pieces = list(desired_piece_lengths_mm or [])

    if planner_cfg.ordering_strategy == "LONGEST_FIRST":
        pieces.sort(reverse=True)
    # AS_GIVEN: leave as-is.

    return pieces


def _build_naive_cut_sequence(
    stock_length_mm: float,
    desired_piece_lengths_mm: List[float],
    kerf_mm: float,
    planner_cfg: SawPlannerConfig,
) -> List[SawCutOperation]:
    """
    Build a simple left-to-right cut sequence with optional leading trim.
    """
    ops: List[SawCutOperation] = []
    offset = 0.0
    seq = 0

    # Leading trim cut (optional)
    if planner_cfg.leading_trim_mm > 0:
        ops.append(
            SawCutOperation(
                op_id="TRIM_LEAD",
                sequence_index=seq,
                cut_type="TRIM",
                start_offset_mm=0.0,
                cut_length_mm=planner_cfg.leading_trim_mm,
                kerf_mm=kerf_mm,
                description=f"Leading trim cut of {planner_cfg.leading_trim_mm:.1f} mm.",
            )
        )
        seq += 1
        offset += planner_cfg.leading_trim_mm + kerf_mm

    # Order the pieces according to strategy
    ordered_pieces = _order_pieces(desired_piece_lengths_mm, planner_cfg)

    for idx, length in enumerate(ordered_pieces):
        cut_pos = offset + length

        ops.append(
            SawCutOperation(
                op_id=f"CUT_{idx+1}",
                sequence_index=seq,
                cut_type="CROSSCUT",
                start_offset_mm=offset,
                cut_length_mm=length,
                kerf_mm=kerf_mm,
                description=(
                    f"Crosscut piece {idx+1} of length {length:.1f} mm "
                    f"at ~{cut_pos:.1f} mm."
                ),
            )
        )

        offset = cut_pos + kerf_mm
        seq += 1

    return ops


# ---------------------------------------------------------------------------
# Public API: Saw Path Planner 2.1
# ---------------------------------------------------------------------------

def plan_saw_cuts_for_board(
    cut_ctx: SawCutContext,
    config: Optional[SawLabConfig] = None,
    planner_cfg: Optional[SawPlannerConfig] = None,
) -> SawCutPlan:
    """
    Saw Path Planner 2.1 – Single-board, trim + scrap + ordering.

    Inputs:
        - SawCutContext: blade, material, stock_length_mm, desired_piece_lengths_mm
        - SawLabConfig: unused for now, can host defaults later
        - SawPlannerConfig: trim, scrap, ordering knobs

    Output:
        - SawCutPlan: operations, stats, feasibility, warnings
    """
    config = config or SawLabConfig()
    planner_cfg = planner_cfg or SawPlannerConfig()
    
    kerf_mm = cut_ctx.blade.kerf_mm
    stock_length_mm = cut_ctx.stock_length_mm or 0.0
    desired_lengths = cut_ctx.desired_piece_lengths_mm or []

    plan = SawCutPlan()

    # 1) Basic yield / feasibility with trims + scrap policy
    feasible, total_pieces, total_kerf, scrap, yield_warnings = _compute_basic_yield(
        stock_length_mm=stock_length_mm,
        desired_piece_lengths_mm=desired_lengths,
        kerf_mm=kerf_mm,
        planner_cfg=planner_cfg,
    )

    plan.total_piece_length_mm = total_pieces
    plan.total_kerf_loss_mm = total_kerf
    plan.scrap_length_mm = scrap
    plan.is_feasible = feasible
    plan.warnings.extend(yield_warnings)

    if stock_length_mm > 0.0:
        plan.material_utilization = total_pieces / stock_length_mm
    else:
        plan.material_utilization = 0.0

    # 2) Build sequence if feasible
    if not feasible:
        plan.notes = (
            "Saw Path Planner 2.1: requested pieces plus trims/kerf either "
            "exceed available stock or violate minimum scrap length. "
            "No cut sequence generated."
        )
        return plan

    plan.operations = _build_naive_cut_sequence(
        stock_length_mm=stock_length_mm,
        desired_piece_lengths_mm=desired_lengths,
        kerf_mm=kerf_mm,
        planner_cfg=planner_cfg,
    )

    plan.notes = (
        "Saw Path Planner 2.1: trim-aware, scrap-aware single-board plan with "
        f"ordering strategy = {planner_cfg.ordering_strategy}."
    )

    return plan


# =============================================================================
# LEGACY: SawPathPlanner class - kept for backward compatibility
# =============================================================================


class SawPathPlanner:
    """
    Plans cutting paths for saw operations.
    
    Considers:
        - Cut order optimization
        - Safe entry/exit paths
        - Kerf compensation
        - Repeated cut patterns
    """
    
    def __init__(self):
        self._geometry = SawGeometryEngine()
    
    def plan_cuts(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> List[Dict[str, Any]]:
        """
        Plan the sequence of cuts for the operation.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            List of cut path segments
        """
        segments = []
        
        # Get cut profile
        profile = self._geometry.compute_cut_profile(design, ctx)
        
        # Safe height for rapids
        safe_z = ctx.stock_thickness_mm + 15.0
        
        # Generate cuts based on type
        if design.cut_type == "dado":
            segments = self._plan_dado_cuts(design, ctx, profile, safe_z)
        else:
            segments = self._plan_through_cuts(design, ctx, profile, safe_z)
        
        return segments
    
    def _plan_through_cuts(
        self,
        design: SawDesign,
        ctx: SawContext,
        profile: Dict[str, Any],
        safe_z: float
    ) -> List[Dict[str, Any]]:
        """Plan through cuts (rip, crosscut, miter, bevel)."""
        segments = []
        
        # Calculate positions for each cut
        for cut_idx in range(design.repeat_count):
            x_offset = cut_idx * (ctx.blade_kerf_mm + design.offset_mm)
            
            # Approach phase
            segments.append({
                "type": "rapid",
                "start": {"x": x_offset, "y": -20.0, "z": safe_z},
                "end": {"x": x_offset, "y": -20.0, "z": safe_z},
                "comment": f"Move to cut {cut_idx + 1} approach"
            })
            
            # Descend to cut depth
            cut_bottom_z = -2.0  # Below stock for through cut
            segments.append({
                "type": "plunge",
                "start": {"x": x_offset, "y": -20.0, "z": safe_z},
                "end": {"x": x_offset, "y": -20.0, "z": cut_bottom_z},
                "feed": ctx.feed_rate_mm_per_min * 0.3,  # 30% feed for plunge
                "comment": f"Plunge for cut {cut_idx + 1}"
            })
            
            # Perform cut
            cut_end_y = design.cut_length_mm + 20.0  # Overshoot for clean exit
            segments.append({
                "type": "cut",
                "start": {"x": x_offset, "y": -20.0, "z": cut_bottom_z},
                "end": {"x": x_offset, "y": cut_end_y, "z": cut_bottom_z},
                "feed": ctx.feed_rate_mm_per_min,
                "comment": f"Cut {cut_idx + 1}: {design.cut_type}"
            })
            
            # Retract
            segments.append({
                "type": "retract",
                "start": {"x": x_offset, "y": cut_end_y, "z": cut_bottom_z},
                "end": {"x": x_offset, "y": cut_end_y, "z": safe_z},
                "comment": f"Retract after cut {cut_idx + 1}"
            })
        
        return segments
    
    def _plan_dado_cuts(
        self,
        design: SawDesign,
        ctx: SawContext,
        profile: Dict[str, Any],
        safe_z: float
    ) -> List[Dict[str, Any]]:
        """Plan dado (groove) cuts with multiple passes."""
        segments = []
        
        # Calculate number of passes needed for dado width
        passes_needed = max(1, int(design.dado_width_mm / ctx.blade_kerf_mm))
        pass_step = design.dado_width_mm / passes_needed
        
        for cut_idx in range(design.repeat_count):
            base_x = cut_idx * (design.dado_width_mm + design.offset_mm)
            
            for pass_idx in range(passes_needed):
                x_offset = base_x + (pass_idx * pass_step)
                
                # Approach
                segments.append({
                    "type": "rapid",
                    "start": {"x": x_offset, "y": -20.0, "z": safe_z},
                    "end": {"x": x_offset, "y": -20.0, "z": safe_z},
                    "comment": f"Dado {cut_idx + 1}, pass {pass_idx + 1}"
                })
                
                # Plunge to dado depth
                dado_z = ctx.stock_thickness_mm - design.dado_depth_mm
                segments.append({
                    "type": "plunge",
                    "start": {"x": x_offset, "y": -20.0, "z": safe_z},
                    "end": {"x": x_offset, "y": -20.0, "z": dado_z},
                    "feed": ctx.feed_rate_mm_per_min * 0.3,
                    "comment": f"Plunge to dado depth"
                })
                
                # Cut groove
                cut_end_y = design.cut_length_mm + 20.0
                segments.append({
                    "type": "cut",
                    "start": {"x": x_offset, "y": -20.0, "z": dado_z},
                    "end": {"x": x_offset, "y": cut_end_y, "z": dado_z},
                    "feed": ctx.feed_rate_mm_per_min,
                    "comment": f"Dado pass"
                })
                
                # Retract
                segments.append({
                    "type": "retract",
                    "start": {"x": x_offset, "y": cut_end_y, "z": dado_z},
                    "end": {"x": x_offset, "y": cut_end_y, "z": safe_z},
                    "comment": f"Retract"
                })
        
        return segments
    
    def estimate_time(
        self,
        segments: List[Dict[str, Any]],
        ctx: SawContext
    ) -> float:
        """
        Estimate total time for planned cuts.
        
        Args:
            segments: Planned cut segments
            ctx: Saw context
        
        Returns:
            Estimated time in seconds
        """
        time_seconds = 0.0
        rapid_feed = 10000.0  # mm/min for rapids
        
        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            
            dx = end["x"] - start["x"]
            dy = end["y"] - start["y"]
            dz = end["z"] - start["z"]
            distance = (dx**2 + dy**2 + dz**2) ** 0.5
            
            if segment["type"] == "rapid" or segment["type"] == "retract":
                feed = rapid_feed
            else:
                feed = segment.get("feed", ctx.feed_rate_mm_per_min)
            
            if feed > 0:
                time_seconds += (distance / feed) * 60.0  # Convert to seconds
        
        # Add 15% overhead for acceleration/deceleration
        time_seconds *= 1.15
        
        return time_seconds
