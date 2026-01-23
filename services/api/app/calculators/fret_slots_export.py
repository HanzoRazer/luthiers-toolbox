"""
Fret Slots Export Calculator

Generates G-code for fret slot cutting with multiple post-processor support.

Phase E Implementation (December 2025)
PATCH-001: Add intonation_model for explicit 12-TET default + opt-in custom ratios (January 2026)

Supported Post-Processors:
- GRBL (default)
- Mach3/Mach4
- LinuxCNC
- PathPilot
- MASSO
- Fanuc
- Haas

Intonation Models (PATCH-001):
- equal_temperament_12 (default): Standard 12-TET fret positions
- custom_ratios: REQUIRES explicit per-fret ratios[] (ratio_set_id is rejected)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from math import sqrt
from enum import Enum

from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..schemas.cam_fret_slots import (
    PostProcessor,
    FretSlotExportRequest,
    FretSlotExportResponse,
    FretSlotData,
    ExportStatistics,
)
from .alternative_temperaments import (
    get_ratio_set,
    compute_fret_positions_from_ratios_mm,
)


# =============================================================================
# Post-Processor Templates
# =============================================================================

@dataclass
class PostTemplate:
    """Template for G-code generation."""
    name: str
    header: str
    footer: str
    line_numbers: bool = False
    line_increment: int = 10
    use_g0_g1: bool = True  # vs G00 G01
    decimal_places: int = 4
    comment_style: str = "parentheses"  # or "semicolon"
    
    def format_comment(self, text: str) -> str:
        if self.comment_style == "semicolon":
            return f"; {text}"
        return f"({text})"


POST_TEMPLATES: Dict[PostProcessor, PostTemplate] = {
    PostProcessor.GRBL: PostTemplate(
        name="GRBL",
        header="G21 G90 G17\n",
        footer="M30\n",
        line_numbers=False,
        decimal_places=4,
    ),
    PostProcessor.MACH3: PostTemplate(
        name="Mach3",
        header="G20 G90 G17 G40 G49 G80\nG21\n",
        footer="M30\n",
        line_numbers=True,
        line_increment=10,
        decimal_places=4,
    ),
    PostProcessor.MACH4: PostTemplate(
        name="Mach4",
        header="G21 G90 G17 G40 G49 G80\n",
        footer="M30\n",
        line_numbers=True,
        line_increment=10,
        decimal_places=4,
    ),
    PostProcessor.LINUXCNC: PostTemplate(
        name="LinuxCNC",
        header="G21 G90 G17 G40 G49 G80\n",
        footer="M2\n",
        line_numbers=False,
        decimal_places=4,
        comment_style="semicolon",
    ),
    PostProcessor.PATHPILOT: PostTemplate(
        name="PathPilot",
        header="G21 G90 G17 G40 G49 G80\n",
        footer="M30\n",
        line_numbers=False,
        decimal_places=4,
    ),
    PostProcessor.MASSO: PostTemplate(
        name="MASSO",
        header="G21 G90 G17\n",
        footer="M30\n",
        line_numbers=False,
        decimal_places=3,
    ),
    PostProcessor.FANUC: PostTemplate(
        name="Fanuc",
        header="O0001\nG21 G90 G17 G40 G49 G80\n",
        footer="M30\n%\n",
        line_numbers=True,
        line_increment=10,
        use_g0_g1=False,  # Uses G00 G01
        decimal_places=4,
    ),
    PostProcessor.HAAS: PostTemplate(
        name="Haas",
        header="O00001\nG20 G90 G17 G40 G49 G80\nG21\n",
        footer="M30\n%\n",
        line_numbers=True,
        line_increment=1,
        use_g0_g1=False,
        decimal_places=4,
    ),
}


# =============================================================================
# Core Export Functions
# =============================================================================

def compute_slot_geometry(
    spec: FretboardSpec,
    slot_depth_mm: float = 3.0,
    fret_positions: Optional[List[float]] = None,
) -> List[FretSlotData]:
    """
    Compute geometry for all fret slots.
    
    Args:
        spec: Fretboard specification
        slot_depth_mm: Depth of fret slots
        fret_positions: Pre-computed fret positions (optional). If None, uses 12-TET.
    
    Returns list of FretSlotData with positions and dimensions.
    """
    if fret_positions is None:
        fret_positions = compute_fret_positions_mm(spec.scale_length_mm, spec.fret_count)
    slots: List[FretSlotData] = []
    
    for i, pos in enumerate(fret_positions):
        fret_num = i + 1
        
        # Compute width at this position (linear taper)
        heel_pos = fret_positions[-1] if fret_positions else spec.scale_length_mm
        if heel_pos > 0:
            ratio = min(1.0, pos / heel_pos)
        else:
            ratio = 0.0
        width = spec.nut_width_mm + (spec.heel_width_mm - spec.nut_width_mm) * ratio
        half_width = width / 2.0
        
        slot = FretSlotData(
            fret_number=fret_num,
            position_mm=pos,
            width_mm=width,
            depth_mm=slot_depth_mm,
            bass_x=pos,
            bass_y=-half_width,
            treble_x=pos,
            treble_y=half_width,
        )
        slots.append(slot)
    
    return slots


def generate_gcode(
    slots: List[FretSlotData],
    post: PostProcessor,
    safe_z_mm: float = 5.0,
    feed_rate_mmpm: float = 1500.0,
    plunge_rate_mmpm: float = 400.0,
) -> Tuple[str, ExportStatistics]:
    """
    Generate G-code for fret slot cutting.
    
    Args:
        slots: List of FretSlotData from compute_slot_geometry()
        post: Target post-processor
        safe_z_mm: Safe retract height
        feed_rate_mmpm: Cutting feed rate
        plunge_rate_mmpm: Plunge feed rate
    
    Returns:
        Tuple of (gcode_string, statistics)
    """
    template = POST_TEMPLATES.get(post, POST_TEMPLATES[PostProcessor.GRBL])
    
    lines: List[str] = []
    line_num = template.line_increment
    
    # Helper to add line with optional line number
    def add_line(text: str):
        nonlocal line_num
        if template.line_numbers:
            lines.append(f"N{line_num} {text}")
            line_num += template.line_increment
        else:
            lines.append(text)
    
    # G0/G1 formatting
    g0 = "G0" if template.use_g0_g1 else "G00"
    g1 = "G1" if template.use_g0_g1 else "G01"
    dec = template.decimal_places
    
    # Header
    lines.append(template.format_comment(f"Fret Slot Program - {len(slots)} slots"))
    lines.append(template.format_comment(f"POST={template.name}; UNITS=mm"))
    lines.append(template.header.strip())
    add_line(f"{g0} Z{safe_z_mm:.{dec}f}")
    lines.append("")
    
    # Statistics tracking
    total_cutting_mm = 0.0
    total_plunge_mm = 0.0
    total_rapid_mm = 0.0
    
    prev_x, prev_y = 0.0, 0.0
    
    for slot in slots:
        # Comment
        lines.append(template.format_comment(
            f"Fret {slot.fret_number} - Pos: {slot.position_mm:.2f}mm"
        ))
        
        # Rapid to slot start (bass side)
        rapid_dist = sqrt((slot.bass_x - prev_x)**2 + (slot.bass_y - prev_y)**2)
        total_rapid_mm += rapid_dist + safe_z_mm  # Include Z move
        
        add_line(f"{g0} X{slot.bass_x:.{dec}f} Y{slot.bass_y:.{dec}f}")
        
        # Plunge
        add_line(f"{g1} Z{-slot.depth_mm:.{dec}f} F{plunge_rate_mmpm:.1f}")
        total_plunge_mm += slot.depth_mm
        
        # Cut across slot (bass to treble)
        slot_length = sqrt(
            (slot.treble_x - slot.bass_x)**2 + 
            (slot.treble_y - slot.bass_y)**2
        )
        total_cutting_mm += slot_length
        
        add_line(f"{g1} X{slot.treble_x:.{dec}f} Y{slot.treble_y:.{dec}f} F{feed_rate_mmpm:.1f}")
        
        # Retract
        add_line(f"{g0} Z{safe_z_mm:.{dec}f}")
        total_rapid_mm += safe_z_mm + slot.depth_mm
        
        lines.append("")
        prev_x, prev_y = slot.treble_x, slot.treble_y
    
    # Footer
    lines.append(template.footer.strip())
    
    # Calculate time estimates
    rapid_rate = 3000.0  # mm/min typical
    rapid_time_min = total_rapid_mm / rapid_rate
    cutting_time_min = total_cutting_mm / feed_rate_mmpm
    plunge_time_min = total_plunge_mm / plunge_rate_mmpm
    total_time_min = rapid_time_min + cutting_time_min + plunge_time_min
    
    stats = ExportStatistics(
        slot_count=len(slots),
        total_cutting_length_mm=round(total_cutting_mm, 2),
        total_plunge_depth_mm=round(total_plunge_mm, 2),
        estimated_time_min=round(total_time_min, 2),
        estimated_time_s=round(total_time_min * 60, 1),
        rapid_distance_mm=round(total_rapid_mm, 2),
        cutting_distance_mm=round(total_cutting_mm, 2),
        feed_rate_mmpm=feed_rate_mmpm,
        plunge_rate_mmpm=plunge_rate_mmpm,
    )
    
    return "\n".join(lines), stats


# =============================================================================
# PATCH-001: Manufacturability Validation
# =============================================================================

def validate_fret_positions_for_machining(
    fret_positions_mm: List[float],
    scale_length_mm: float,
    slot_width_mm: float,
    nut_margin_mm: float = 1.0,
    heel_margin_mm: float = 1.0,
    min_spacing_factor: float = 1.25,
) -> List[str]:
    """
    Temperament-agnostic manufacturability checks.
    
    Returns list of warning/error messages. Empty list = valid.
    
    Checks:
      - positions are within bounds (0 < pos < scale_length)
      - adjacent frets are not too close for the declared slot width
      - first fret is not too close to nut
      - last fret is not too close to bridge
    
    Args:
        fret_positions_mm: List of fret positions from nut
        scale_length_mm: Total scale length
        slot_width_mm: Width of fret slot (kerf)
        nut_margin_mm: Minimum distance from nut to first fret
        heel_margin_mm: Minimum distance from last fret to scale end
        min_spacing_factor: Multiplier for slot_width to determine min spacing
    
    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []
    
    if not fret_positions_mm:
        errors.append("No fret positions computed")
        return errors
    
    # Bounds check: 0 < fret < scale_length
    for i, p in enumerate(fret_positions_mm):
        if p <= 0.0:
            errors.append(f"Fret {i+1} position ({p:.4f}mm) is <= 0")
        if p >= scale_length_mm:
            errors.append(f"Fret {i+1} position ({p:.4f}mm) exceeds scale length ({scale_length_mm}mm)")
    
    # Minimum spacing check
    min_spacing_mm = max(0.25, slot_width_mm * min_spacing_factor)
    for i in range(1, len(fret_positions_mm)):
        spacing = fret_positions_mm[i] - fret_positions_mm[i - 1]
        if spacing < min_spacing_mm:
            errors.append(
                f"Frets {i} and {i+1} too close ({spacing:.3f}mm). "
                f"Min required: {min_spacing_mm:.3f}mm for slot_width={slot_width_mm}mm"
            )
    
    # Edge margin checks
    if fret_positions_mm[0] < nut_margin_mm:
        errors.append(f"First fret too close to nut ({fret_positions_mm[0]:.4f}mm < {nut_margin_mm}mm)")
    
    remaining = scale_length_mm - fret_positions_mm[-1]
    if remaining < heel_margin_mm:
        errors.append(f"Last fret too close to bridge ({remaining:.4f}mm < {heel_margin_mm}mm)")
    
    return errors


def export_fret_slots(
    request: FretSlotExportRequest,
) -> FretSlotExportResponse:
    """
    Main export function for fret slot G-code.
    
    PATCH-001: Now supports intonation_model selection:
      - equal_temperament_12 (default): Standard 12-TET fret positions
      - custom_ratios: Uses provided ratios[] or ratio_set_id
    
    Args:
        request: FretSlotExportRequest with all parameters
    
    Returns:
        FretSlotExportResponse with G-code and metadata
    
    Raises:
        ValueError: If custom_ratios configuration is invalid
    """
    # PATCH-001: Compute fret positions based on intonation model
    if request.intonation_model == "equal_temperament_12":
        # Default: use canonical 12-TET calculation
        fret_positions = compute_fret_positions_mm(
            scale_length_mm=request.scale_length_mm,
            fret_count=request.fret_count,
        )
    else:
        # custom_ratios: REQUIRES explicit per-fret ratios for CAM export
        # Named ratio sets (JUST_MAJOR, etc.) are scale-degree-based, not per-fret
        # CAM export requires explicit ratios to prevent musical-context misuse
        if request.ratios is not None:
            ratios = request.ratios
        elif request.ratio_set_id:
            # Reject ratio_set_id without explicit ratios - forces caller to expand
            observed_len = len(request.ratios) if request.ratios is not None else 0
            
            # Dev-mode suggestion: point to the canonical template for per-fret ratios.
            # We keep this out of production logs/messages unless explicitly in dev/test.
            hint = ""
            env = (os.getenv("APP_ENV") or os.getenv("ENV") or "").strip().lower()
            debug = (os.getenv("DEBUG") or "").strip().lower() in ("1", "true", "yes", "on")
            if env in ("dev", "development", "test") or debug:
                # Resolve relative to repo layout when running from services/api
                # (non-fatal; if path doesn't exist we still provide a stable suggestion)
                template_rel = "docs/tests/ratios_template.json"
                template_abs = str(Path(__file__).resolve().parents[3] / "docs" / "tests" / "ratios_template.json")
                hint = (
                    f" See template: '{template_rel}' "
                    f"(or absolute: '{template_abs}')."
                )
            
            raise ValueError(
                f"ratio_set_id='{request.ratio_set_id}' does not provide per-fret ratios "
                f"required for CAM export (observed length={observed_len}). "
                f"Provide explicit ratios[] with length == fret_count ({request.fret_count})."
                f"{hint}"
            )
        else:
            # Schema validation should prevent this, but guard anyway
            raise ValueError(
                "custom_ratios requires ratios[] for CAM export"
            )

        fret_positions = compute_fret_positions_from_ratios_mm(
            scale_length_mm=request.scale_length_mm,
            ratios=ratios,
        )
    
    # PATCH-001: Manufacturability validation (temperament-agnostic)
    machining_errors = validate_fret_positions_for_machining(
        fret_positions_mm=fret_positions,
        scale_length_mm=request.scale_length_mm,
        slot_width_mm=request.slot_width_mm,
    )
    if machining_errors:
        raise ValueError(
            f"Fret positions failed manufacturability checks: {'; '.join(machining_errors)}"
        )
    
    # Build FretboardSpec
    spec = FretboardSpec(
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
        scale_length_mm=request.scale_length_mm,
        fret_count=request.fret_count,
        base_radius_mm=request.base_radius_mm,
        end_radius_mm=request.end_radius_mm,
    )
    
    # Compute slot geometry using pre-computed fret positions
    slots = compute_slot_geometry(spec, request.slot_depth_mm, fret_positions=fret_positions)
    
    # Determine feed rates
    feed_rate = request.feed_rate_mmpm or 1500.0
    plunge_rate = request.plunge_rate_mmpm or 400.0
    
    # Generate G-code
    gcode, stats = generate_gcode(
        slots=slots,
        post=request.post_processor,
        safe_z_mm=request.safe_z_mm,
        feed_rate_mmpm=feed_rate,
        plunge_rate_mmpm=plunge_rate,
    )
    
    # Build response
    warnings: List[str] = []
    
    # PATCH-001: Add intonation model warning for custom ratios
    if request.intonation_model == "custom_ratios":
        warnings.append(
            f"Using custom ratios (intonation_model=custom_ratios). "
            f"Verify fret positions are correct for your application."
        )
    
    # Add warnings for edge cases
    if request.slot_depth_mm > 4.0:
        warnings.append("⚠️ Slot depth > 4mm may require multiple passes")
    if feed_rate > 2500:
        warnings.append("⚠️ High feed rate - verify for your material")
    
    return FretSlotExportResponse(
        gcode=gcode,
        dxf=None,  # TODO: Add DXF export
        post_processor=request.post_processor.value,
        slot_count=stats.slot_count,
        total_cutting_length_mm=stats.total_cutting_length_mm,
        estimated_time_min=stats.estimated_time_min,
        slots=slots,
        warnings=warnings,
    )


def export_fret_slots_multi(
    base_request: FretSlotExportRequest,
    post_processors: List[PostProcessor],
) -> Dict[str, FretSlotExportResponse]:
    """
    Export fret slots to multiple post-processors.
    
    Returns dict mapping post-processor name to response.
    """
    results: Dict[str, FretSlotExportResponse] = {}
    
    for post in post_processors:
        request = base_request.copy()
        request.post_processor = post
        
        try:
            response = export_fret_slots(request)
            results[post.value] = response
        except Exception as e:
            # Create error response
            results[post.value] = FretSlotExportResponse(
                gcode=f"(ERROR: {str(e)})",
                post_processor=post.value,
                slot_count=0,
                total_cutting_length_mm=0,
                estimated_time_min=0,
                slots=[],
                warnings=[f"Export failed: {str(e)}"],
            )
    
    return results
