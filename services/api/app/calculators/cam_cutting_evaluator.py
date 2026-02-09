"""CAM cutting evaluation — chipload, heat, deflection, rim-speed, kickback, bite.

Pure calculation functions with zero FastAPI dependency.
Extracted from ``calculators_consolidated_router.py`` (WP-3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional


# ============================================================================
# Result Dataclasses
# ============================================================================

@dataclass
class ChiploadResult:
    """Chipload calculation result."""
    chipload_mm: Optional[float]
    in_range: bool
    min_recommended_mm: Optional[float] = None
    max_recommended_mm: Optional[float] = None
    message: str = ""


@dataclass
class HeatResult:
    """Heat risk assessment."""
    heat_risk: float  # 0-1, where 1 is worst
    category: str  # "COOL" / "WARM" / "HOT"
    message: str = ""


@dataclass
class DeflectionResult:
    """Tool deflection assessment."""
    deflection_mm: Optional[float]
    risk: str  # "GREEN" / "YELLOW" / "RED"
    message: str = ""


@dataclass
class RimSpeedResult:
    """Saw blade rim speed result."""
    surface_speed_m_per_min: Optional[float]
    within_limits: bool
    max_recommended_m_per_min: Optional[float] = None
    message: str = ""


@dataclass
class KickbackRiskResult:
    """Saw blade kickback risk assessment."""
    risk_score: float  # 0-1
    category: str  # "LOW" / "MEDIUM" / "HIGH"
    message: str = ""


@dataclass
class BitePerToothResult:
    """Saw blade bite per tooth (feed per tooth)."""
    bite_mm: Optional[float]
    in_range: bool
    min_recommended_mm: Optional[float] = None
    max_recommended_mm: Optional[float] = None
    message: str = ""


ToolKind = Literal["router_bit", "saw_blade"]


# ============================================================================
# Pure Calculation Functions
# ============================================================================

def calculate_chipload(
    feed_mm_min: float, rpm: float, flute_count: int,
    min_chipload: float = 0.05, max_chipload: float = 0.25,
) -> ChiploadResult:
    """Calculate chipload (feed per tooth) for router bits."""
    if rpm <= 0 or flute_count <= 0:
        return ChiploadResult(chipload_mm=None, in_range=False, message="Invalid RPM or flute count")

    chipload = feed_mm_min / (rpm * flute_count)
    in_range = min_chipload <= chipload <= max_chipload

    if chipload < min_chipload:
        message = f"Chipload {chipload:.4f}mm below min ({min_chipload}mm) - rubbing risk"
    elif chipload > max_chipload:
        message = f"Chipload {chipload:.4f}mm exceeds max ({max_chipload}mm) - breakage risk"
    else:
        message = f"Chipload {chipload:.4f}mm within recommended range"

    return ChiploadResult(
        chipload_mm=chipload, in_range=in_range,
        min_recommended_mm=min_chipload, max_recommended_mm=max_chipload, message=message,
    )


def calculate_heat_risk(
    chipload_mm: Optional[float], rpm: float, depth_of_cut_mm: float,
    material_heat_sensitivity: float = 0.5,
) -> HeatResult:
    """Estimate heat risk based on cutting parameters."""
    if chipload_mm is None or chipload_mm <= 0:
        return HeatResult(heat_risk=0.8, category="HOT", message="Unable to calculate chipload - high heat risk")

    chipload_factor = max(0, 1 - (chipload_mm / 0.15))
    rpm_factor = min(1, rpm / 20000)
    depth_factor = min(1, depth_of_cut_mm / 10)
    heat_risk = chipload_factor * 0.4 + rpm_factor * 0.3 + depth_factor * 0.2 + material_heat_sensitivity * 0.1
    heat_risk = min(1.0, max(0.0, heat_risk))

    if heat_risk < 0.3:
        return HeatResult(heat_risk=heat_risk, category="COOL", message="Low heat risk")
    elif heat_risk < 0.6:
        return HeatResult(heat_risk=heat_risk, category="WARM", message="Moderate heat risk - monitor for burns")
    else:
        return HeatResult(heat_risk=heat_risk, category="HOT", message="High heat risk - reduce RPM or increase feed")


def calculate_deflection(
    tool_diameter_mm: float, depth_of_cut_mm: float,
    width_of_cut_mm: Optional[float], stickout_mm: float = 25.0,
) -> DeflectionResult:
    """Estimate tool deflection risk."""
    if tool_diameter_mm <= 0:
        return DeflectionResult(deflection_mm=None, risk="RED", message="Invalid tool diameter")

    stickout_ratio = stickout_mm / tool_diameter_mm
    woc = width_of_cut_mm if width_of_cut_mm else tool_diameter_mm * 0.5
    force_proxy = depth_of_cut_mm * woc
    deflection_mm = (stickout_ratio ** 3) * force_proxy * 0.0001

    if deflection_mm < 0.05:
        return DeflectionResult(deflection_mm=deflection_mm, risk="GREEN", message=f"Low deflection ({deflection_mm:.4f}mm)")
    elif deflection_mm < 0.15:
        return DeflectionResult(deflection_mm=deflection_mm, risk="YELLOW", message=f"Moderate deflection ({deflection_mm:.4f}mm)")
    else:
        return DeflectionResult(deflection_mm=deflection_mm, risk="RED", message=f"High deflection ({deflection_mm:.4f}mm)")


def calculate_rim_speed(blade_diameter_mm: float, rpm: float, max_rim_speed: float = 80.0) -> RimSpeedResult:
    """Calculate saw blade rim speed."""
    if blade_diameter_mm <= 0 or rpm <= 0:
        return RimSpeedResult(surface_speed_m_per_min=None, within_limits=False, message="Invalid parameters")

    rim_speed = math.pi * blade_diameter_mm * rpm / 1000
    within_limits = rim_speed <= max_rim_speed

    if within_limits:
        message = f"Rim speed {rim_speed:.1f} m/min within limits"
    else:
        message = f"Rim speed {rim_speed:.1f} m/min EXCEEDS maximum ({max_rim_speed} m/min)"

    return RimSpeedResult(
        surface_speed_m_per_min=rim_speed, within_limits=within_limits,
        max_recommended_m_per_min=max_rim_speed, message=message,
    )


def calculate_bite_per_tooth(
    feed_mm_min: float, rpm: float, tooth_count: int,
    min_bite: float = 0.05, max_bite: float = 0.20,
) -> BitePerToothResult:
    """Calculate saw blade bite per tooth."""
    if rpm <= 0 or tooth_count <= 0:
        return BitePerToothResult(bite_mm=None, in_range=False, message="Invalid parameters")

    bite = feed_mm_min / (rpm * tooth_count)
    in_range = min_bite <= bite <= max_bite

    if bite < min_bite:
        message = f"Bite {bite:.4f}mm below min - rubbing risk"
    elif bite > max_bite:
        message = f"Bite {bite:.4f}mm exceeds max - tooth damage risk"
    else:
        message = f"Bite {bite:.4f}mm within recommended range"

    return BitePerToothResult(
        bite_mm=bite, in_range=in_range,
        min_recommended_mm=min_bite, max_recommended_mm=max_bite, message=message,
    )


def calculate_kickback_risk(
    depth_of_cut_mm: float, blade_diameter_mm: float,
    tooth_count: int, feed_mm_min: float,
) -> KickbackRiskResult:
    """Estimate kickback risk for saw operations."""
    max_depth = blade_diameter_mm * 0.4
    depth_ratio = min(1.0, depth_of_cut_mm / max_depth) if max_depth > 0 else 1.0
    feed_factor = min(1.0, feed_mm_min / 5000)
    tooth_factor = max(0, 1 - (tooth_count / 100))

    risk_score = depth_ratio * 0.5 + feed_factor * 0.3 + tooth_factor * 0.2
    risk_score = min(1.0, max(0.0, risk_score))

    if risk_score < 0.3:
        return KickbackRiskResult(risk_score=risk_score, category="LOW", message="Low kickback risk")
    elif risk_score < 0.6:
        return KickbackRiskResult(risk_score=risk_score, category="MEDIUM", message="Moderate kickback - ensure workholding")
    else:
        return KickbackRiskResult(risk_score=risk_score, category="HIGH", message="HIGH kickback risk - reduce depth/feed")


def evaluate_cut_operation(
    tool_id: str,
    material_id: str,
    tool_kind: str,
    feed_mm_min: float,
    rpm: float,
    depth_of_cut_mm: float,
    width_of_cut_mm: Optional[float] = None,
    tool_diameter_mm: float = 6.0,
    flute_count: int = 2,
) -> Dict[str, Any]:
    """Evaluate a cut operation and return all calculator results as a dict.

    Returns a flat dict suitable for constructing ``CAMCalculatorBundleResponse``.
    """
    warnings: List[str] = []
    hard_failures: List[str] = []

    chipload_res = heat_res = deflection_res = None
    rim_speed_res = kickback_res = bite_res = None

    if tool_kind == "router_bit":
        chipload_res = calculate_chipload(feed_mm_min, rpm, flute_count)
        heat_res = calculate_heat_risk(chipload_res.chipload_mm, rpm, depth_of_cut_mm)
        deflection_res = calculate_deflection(tool_diameter_mm, depth_of_cut_mm, width_of_cut_mm)

        if not chipload_res.in_range:
            warnings.append(chipload_res.message)
        if heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if deflection_res.risk == "RED":
            hard_failures.append(deflection_res.message)
        elif deflection_res.risk == "YELLOW":
            warnings.append(deflection_res.message)

    elif tool_kind == "saw_blade":
        rim_speed_res = calculate_rim_speed(tool_diameter_mm, rpm)
        bite_res = calculate_bite_per_tooth(feed_mm_min, rpm, flute_count)
        heat_res = calculate_heat_risk(bite_res.bite_mm if bite_res else None, rpm, depth_of_cut_mm)
        kickback_res = calculate_kickback_risk(depth_of_cut_mm, tool_diameter_mm, flute_count, feed_mm_min)

        if not rim_speed_res.within_limits:
            hard_failures.append(rim_speed_res.message)
        if not bite_res.in_range:
            warnings.append(bite_res.message)
        if heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if kickback_res.category == "HIGH":
            hard_failures.append(kickback_res.message)
        elif kickback_res.category == "MEDIUM":
            warnings.append(kickback_res.message)

    overall_risk = "RED" if hard_failures else ("YELLOW" if warnings else "GREEN")

    return dict(
        tool_id=tool_id,
        material_id=material_id,
        tool_kind=tool_kind,
        chipload=asdict(chipload_res) if chipload_res else None,
        heat=asdict(heat_res) if heat_res else None,
        deflection=asdict(deflection_res) if deflection_res else None,
        rim_speed=asdict(rim_speed_res) if rim_speed_res else None,
        kickback=asdict(kickback_res) if kickback_res else None,
        bite_per_tooth=asdict(bite_res) if bite_res else None,
        warnings=warnings,
        hard_failures=hard_failures,
        overall_risk=overall_risk,
    )
