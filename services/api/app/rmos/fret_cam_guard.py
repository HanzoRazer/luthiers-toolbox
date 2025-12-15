# services/api/app/rmos/fret_cam_guard.py
"""
Fret CAM Guard Module

Combines fan-fret geometry guards with cutting physics guards
to produce unified RmosMessage[] for fret slot CAM operations.

Wave 8 Implementation (Combined CAM Guard Wave)
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any

from pydantic import BaseModel

from .messages import RmosMessage, as_warning, as_error, as_info


class FretSlotSpec(BaseModel):
    """Specification for a single fret slot."""
    fret: int
    string_index: int
    position_mm: float
    slot_width_mm: float
    slot_depth_mm: float
    bit_diameter_mm: float
    angle_rad: Optional[float] = None


class FanFretGuardInput(BaseModel):
    """Input for fan-fret geometry guard."""
    frets: List[Dict[str, Any]]
    bass_scale_mm: float
    treble_scale_mm: float
    perpendicular_fret: int


class ChiploadRiskResult(BaseModel):
    """Result from chipload risk calculation."""
    risk_level: float  # 0.0 to 1.0
    message: Optional[RmosMessage] = None


class DeflectionRiskResult(BaseModel):
    """Result from deflection risk calculation."""
    risk_level: float
    message: Optional[RmosMessage] = None


class HeatRiskResult(BaseModel):
    """Result from heat risk calculation."""
    risk_level: float
    message: Optional[RmosMessage] = None


def compute_chipload_risk_for_fret_slot(
    *,
    model_id: str,
    fret: int,
    string_index: int,
    bit_diameter_mm: float,
    slot_width_mm: float,
    feed_rate_mmpm: float = 1500.0,
    rpm: float = 24000.0,
    flute_count: int = 2,
) -> ChiploadRiskResult:
    """
    Calculate chipload risk for a fret slot cut.
    
    Chipload = feed_rate / (rpm * flute_count)
    Ideal range for hardwood: 0.05-0.15mm
    """
    chipload = feed_rate_mmpm / (rpm * flute_count)
    
    # Risk thresholds
    if chipload < 0.03:
        return ChiploadRiskResult(
            risk_level=0.7,
            message=as_warning(
                "CHIPLOAD_LOW",
                f"Chipload ({chipload:.4f}mm) is below optimal range. May cause rubbing and heat buildup.",
                fret=fret,
                string_index=string_index,
                chipload_mm=chipload,
                model_id=model_id,
            )
        )
    elif chipload > 0.20:
        return ChiploadRiskResult(
            risk_level=0.9,
            message=as_error(
                "CHIPLOAD_HIGH",
                f"Chipload ({chipload:.4f}mm) exceeds safe range. Risk of tool breakage.",
                fret=fret,
                string_index=string_index,
                chipload_mm=chipload,
                model_id=model_id,
            )
        )
    
    return ChiploadRiskResult(risk_level=0.0)


def compute_deflection_risk_for_fret_slot(
    *,
    model_id: str,
    fret: int,
    string_index: int,
    bit_diameter_mm: float,
    slot_depth_mm: float,
) -> DeflectionRiskResult:
    """
    Calculate deflection risk based on bit diameter vs slot depth.
    
    Rule of thumb: depth should not exceed 3x diameter for slotting saws.
    """
    depth_ratio = slot_depth_mm / bit_diameter_mm if bit_diameter_mm > 0 else 999
    
    if depth_ratio > 5.0:
        return DeflectionRiskResult(
            risk_level=0.95,
            message=as_error(
                "SLOT_DEPTH_EXCEEDS_TOOL",
                f"Slot depth ({slot_depth_mm}mm) is {depth_ratio:.1f}x bit diameter. High deflection risk.",
                fret=fret,
                string_index=string_index,
                depth_ratio=depth_ratio,
                model_id=model_id,
            )
        )
    elif depth_ratio > 3.0:
        return DeflectionRiskResult(
            risk_level=0.6,
            message=as_warning(
                "SLOT_DEPTH_HIGH",
                f"Slot depth ({slot_depth_mm}mm) is {depth_ratio:.1f}x bit diameter. Consider multiple passes.",
                fret=fret,
                string_index=string_index,
                depth_ratio=depth_ratio,
                model_id=model_id,
            )
        )
    
    return DeflectionRiskResult(risk_level=0.0)


def compute_heat_risk_for_fret_slot(
    *,
    model_id: str,
    fret: int,
    string_index: int,
    slot_depth_mm: float,
    material_heat_sensitivity: float = 1.0,
) -> HeatRiskResult:
    """
    Calculate heat buildup risk based on depth and material.
    
    Deeper cuts in heat-sensitive materials (ebony) need slower feeds.
    """
    heat_factor = slot_depth_mm * material_heat_sensitivity
    
    if heat_factor > 5.0:
        return HeatRiskResult(
            risk_level=0.7,
            message=as_warning(
                "HEAT_BUILDUP_RISK",
                f"Deep cut in heat-sensitive material. Consider coolant or slower feed.",
                fret=fret,
                string_index=string_index,
                heat_factor=heat_factor,
                model_id=model_id,
            )
        )
    
    return HeatRiskResult(risk_level=0.0)


def run_fret_cam_guard(
    *,
    model_id: str,
    slots: List[FretSlotSpec],
    fan_input: Optional[FanFretGuardInput] = None,
    feed_rate_mmpm: float = 1500.0,
    rpm: float = 24000.0,
    material_heat_sensitivity: float = 1.0,
) -> List[RmosMessage]:
    """
    Run all fret CAM guards and return unified message list.
    
    Args:
        model_id: Guitar model identifier
        slots: List of fret slot specifications
        fan_input: Optional fan-fret geometry input for multiscale validation
        feed_rate_mmpm: Feed rate in mm/min
        rpm: Spindle RPM
        material_heat_sensitivity: Material heat factor (1.0 = maple, 1.3 = ebony)
    
    Returns:
        List of RmosMessage with warnings/errors
    """
    messages: List[RmosMessage] = []
    
    # 1) Fan-fret geometry guard (if provided)
    if fan_input is not None:
        try:
            from ..instrument_geometry.fan_fret_guard import compute_fan_fret_geometry_guard
            
            ff_result = compute_fan_fret_geometry_guard(
                frets=fan_input.frets,
                bass_scale_mm=fan_input.bass_scale_mm,
                treble_scale_mm=fan_input.treble_scale_mm,
                perpendicular_fret=fan_input.perpendicular_fret,
            )
            
            # Convert fan-fret warnings to RmosMessages
            for w in getattr(ff_result, 'warnings', []):
                if isinstance(w, dict):
                    messages.append(
                        RmosMessage(
                            code=w.get("code", "FANFRET_WARNING"),
                            severity="warning",
                            message=w.get("message", ""),
                            context={
                                "model_id": model_id,
                                **{k: v for k, v in w.items() if k not in ("code", "message")}
                            },
                        )
                    )
            
            for e in getattr(ff_result, 'errors', []):
                if isinstance(e, dict):
                    messages.append(
                        RmosMessage(
                            code=e.get("code", "FANFRET_ERROR"),
                            severity="error",
                            message=e.get("message", ""),
                            context={
                                "model_id": model_id,
                                **{k: v for k, v in e.items() if k not in ("code", "message")}
                            },
                        )
                    )
        except ImportError:
            messages.append(
                as_info(
                    "FANFRET_GUARD_UNAVAILABLE",
                    "Fan-fret geometry guard module not available.",
                    model_id=model_id,
                )
            )
    
    # 2) Per-slot cutting physics guards
    for slot in slots:
        # Chipload check
        chip_res = compute_chipload_risk_for_fret_slot(
            model_id=model_id,
            fret=slot.fret,
            string_index=slot.string_index,
            bit_diameter_mm=slot.bit_diameter_mm,
            slot_width_mm=slot.slot_width_mm,
            feed_rate_mmpm=feed_rate_mmpm,
            rpm=rpm,
        )
        if chip_res.message is not None:
            messages.append(chip_res.message)
        
        # Deflection check
        defl_res = compute_deflection_risk_for_fret_slot(
            model_id=model_id,
            fret=slot.fret,
            string_index=slot.string_index,
            bit_diameter_mm=slot.bit_diameter_mm,
            slot_depth_mm=slot.slot_depth_mm,
        )
        if defl_res.message is not None:
            messages.append(defl_res.message)
        
        # Heat check
        heat_res = compute_heat_risk_for_fret_slot(
            model_id=model_id,
            fret=slot.fret,
            string_index=slot.string_index,
            slot_depth_mm=slot.slot_depth_mm,
            material_heat_sensitivity=material_heat_sensitivity,
        )
        if heat_res.message is not None:
            messages.append(heat_res.message)
    
    # 3) Global guard: too many messages
    if len(messages) > 100:
        messages.append(
            as_warning(
                "FRET_CAM_GUARD_MSG_FLOOD",
                "Large number of warnings/errors generated for this fret-slot preview.",
                model_id=model_id,
                count=len(messages),
            )
        )
    
    return messages
