# services/api/app/rmos/saw_cam_guard.py
"""
Saw CAM Guard Module

Safety guards for saw operations: rim speed, bite/tooth, heat, deflection, kickback.
Returns unified RmosMessage[] for saw lab CAM operations.

Wave 8 Implementation (Combined CAM Guard Wave)
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from .messages import RmosMessage, as_warning, as_error, as_info


class SawCutOperation(BaseModel):
    """Specification for a single saw cut operation."""
    op_id: str
    blade_id: str
    material_id: str
    feed_mm_min: float
    rpm: float
    depth_mm: float
    width_mm: float
    cut_length_mm: float
    blade_diameter_mm: float = 250.0
    tooth_count: int = 60


class RiskResult(BaseModel):
    """Generic risk result from calculator."""
    value: Optional[float] = None
    message: Optional[RmosMessage] = None


def compute_rim_speed_risk(
    *,
    blade_id: str,
    rpm: float,
    blade_diameter_mm: float = 250.0,
    max_surface_speed_mpm: float = 4000.0,
) -> RiskResult:
    """
    Calculate rim speed risk.
    
    Rim speed = π * diameter * RPM / 1000 (m/min)
    Typical max for carbide-tipped blades: 4000-5000 m/min
    """
    import math
    rim_speed_mpm = math.pi * blade_diameter_mm * rpm / 1000.0
    
    if rim_speed_mpm > max_surface_speed_mpm * 1.1:
        return RiskResult(
            value=rim_speed_mpm,
            message=as_error(
                "RIM_SPEED_EXCEEDED",
                f"Rim speed ({rim_speed_mpm:.0f} m/min) exceeds safe limit ({max_surface_speed_mpm:.0f} m/min).",
                blade_id=blade_id,
                rim_speed_mpm=rim_speed_mpm,
                max_mpm=max_surface_speed_mpm,
            )
        )
    elif rim_speed_mpm > max_surface_speed_mpm * 0.9:
        return RiskResult(
            value=rim_speed_mpm,
            message=as_warning(
                "RIM_SPEED_HIGH",
                f"Rim speed ({rim_speed_mpm:.0f} m/min) approaching limit.",
                blade_id=blade_id,
                rim_speed_mpm=rim_speed_mpm,
            )
        )
    
    return RiskResult(value=rim_speed_mpm)


def compute_bite_risk(
    *,
    blade_id: str,
    feed_mm_min: float,
    material_id: str,
    rpm: float = 3000.0,
    tooth_count: int = 60,
) -> RiskResult:
    """
    Calculate bite per tooth risk.
    
    Bite = feed_rate / (RPM * tooth_count)
    Ideal range varies by material: 0.05-0.15mm for hardwood
    """
    bite_mm = feed_mm_min / (rpm * tooth_count) if rpm * tooth_count > 0 else 999
    
    # Material-specific limits (simplified)
    max_bite = 0.15 if "hard" in material_id.lower() else 0.25
    
    if bite_mm > max_bite:
        return RiskResult(
            value=bite_mm,
            message=as_warning(
                "BITE_PER_TOOTH_HIGH",
                f"Bite per tooth ({bite_mm:.4f}mm) exceeds recommended for {material_id}.",
                blade_id=blade_id,
                bite_mm=bite_mm,
                material_id=material_id,
            )
        )
    elif bite_mm < 0.01:
        return RiskResult(
            value=bite_mm,
            message=as_info(
                "BITE_PER_TOOTH_LOW",
                f"Bite per tooth ({bite_mm:.4f}mm) is very low. May cause rubbing.",
                blade_id=blade_id,
                bite_mm=bite_mm,
            )
        )
    
    return RiskResult(value=bite_mm)


def compute_saw_heat_risk(
    *,
    blade_id: str,
    material_id: str,
    cut_length_mm: float,
    heat_threshold_mm: float = 500.0,
) -> RiskResult:
    """
    Calculate heat buildup risk based on cut length.
    
    Long cuts without cooling can cause blade warping and burn marks.
    """
    if cut_length_mm > heat_threshold_mm:
        return RiskResult(
            value=cut_length_mm,
            message=as_warning(
                "SAW_HEAT_BUILDUP",
                f"Long cut ({cut_length_mm:.0f}mm) may cause heat buildup. Consider pausing.",
                blade_id=blade_id,
                cut_length_mm=cut_length_mm,
                material_id=material_id,
            )
        )
    
    return RiskResult(value=cut_length_mm)


def compute_saw_deflection_risk(
    *,
    blade_id: str,
    depth_mm: float,
    blade_diameter_mm: float = 250.0,
    max_depth_ratio: float = 0.4,
) -> RiskResult:
    """
    Calculate blade deflection risk based on cut depth vs blade diameter.
    
    Rule of thumb: max depth = 40% of blade diameter for clean cuts.
    """
    depth_ratio = depth_mm / blade_diameter_mm if blade_diameter_mm > 0 else 999
    
    if depth_ratio > max_depth_ratio:
        return RiskResult(
            value=depth_ratio,
            message=as_warning(
                "SAW_DEPTH_HIGH",
                f"Cut depth ({depth_mm:.1f}mm) is {depth_ratio:.0%} of blade diameter. May cause deflection.",
                blade_id=blade_id,
                depth_mm=depth_mm,
                depth_ratio=depth_ratio,
            )
        )
    
    return RiskResult(value=depth_ratio)


def compute_kickback_risk(
    *,
    blade_id: str,
    material_id: str,
    feed_mm_min: float,
    feed_threshold_mm_min: float = 5000.0,
) -> RiskResult:
    """
    Calculate kickback risk based on aggressive feed rates.
    
    Kickback is more likely with high feed rates on dense materials.
    """
    is_dense = any(w in material_id.lower() for w in ["hard", "ebony", "rosewood", "maple"])
    
    threshold = feed_threshold_mm_min * 0.7 if is_dense else feed_threshold_mm_min
    
    if feed_mm_min > threshold:
        return RiskResult(
            value=feed_mm_min,
            message=as_warning(
                "KICKBACK_RISK",
                f"High feed rate ({feed_mm_min:.0f}mm/min) on {material_id}. Kickback risk elevated.",
                blade_id=blade_id,
                feed_mm_min=feed_mm_min,
                material_id=material_id,
            )
        )
    
    return RiskResult(value=feed_mm_min)


def run_saw_cam_guard(
    *,
    operations: List[SawCutOperation],
) -> List[RmosMessage]:
    """
    Run all saw CAM guards and return unified message list.
    
    Args:
        operations: List of saw cut operations to validate
    
    Returns:
        List of RmosMessage with warnings/errors per operation
    """
    messages: List[RmosMessage] = []
    
    for op in operations:
        # Rim speed / surface speed
        rim = compute_rim_speed_risk(
            blade_id=op.blade_id,
            rpm=op.rpm,
            blade_diameter_mm=op.blade_diameter_mm,
        )
        if rim.message is not None:
            msg = rim.message.model_copy()
            msg.context["op_id"] = op.op_id
            messages.append(msg)
        
        # Bite per tooth
        bite = compute_bite_risk(
            blade_id=op.blade_id,
            feed_mm_min=op.feed_mm_min,
            material_id=op.material_id,
            rpm=op.rpm,
            tooth_count=op.tooth_count,
        )
        if bite.message is not None:
            msg = bite.message.model_copy()
            msg.context["op_id"] = op.op_id
            messages.append(msg)
        
        # Heat
        heat = compute_saw_heat_risk(
            blade_id=op.blade_id,
            material_id=op.material_id,
            cut_length_mm=op.cut_length_mm,
        )
        if heat.message is not None:
            msg = heat.message.model_copy()
            msg.context["op_id"] = op.op_id
            messages.append(msg)
        
        # Deflection
        defl = compute_saw_deflection_risk(
            blade_id=op.blade_id,
            depth_mm=op.depth_mm,
            blade_diameter_mm=op.blade_diameter_mm,
        )
        if defl.message is not None:
            msg = defl.message.model_copy()
            msg.context["op_id"] = op.op_id
            messages.append(msg)
        
        # Kickback
        kick = compute_kickback_risk(
            blade_id=op.blade_id,
            material_id=op.material_id,
            feed_mm_min=op.feed_mm_min,
        )
        if kick.message is not None:
            msg = kick.message.model_copy()
            msg.context["op_id"] = op.op_id
            messages.append(msg)
    
    return messages
