"""
Saw Lab Physics Debug Router

Provides the /api/saw/physics-debug endpoint for the Saw Physics Debug Panel.
"""
from __future__ import annotations

from typing import List
import math

from fastapi import APIRouter

from .debug_schemas import (
    SawPhysicsDebugRequest,
    SawPhysicsDebugResponse,
    RimSpeedResult,
    BiteLoadResult,
    KickbackResult,
    HeatIndexResult,
    DeflectionResult,
)
from .models import SawContext, SawDesign


router = APIRouter(
    prefix="/api/saw",
    tags=["saw_lab_debug"],
)


# ---------------------------------------------------------------------------
# Calculator Implementations (simplified for debug panel)
# ---------------------------------------------------------------------------

def _calc_rim_speed(
    diameter_mm: float,
    rpm: int,
) -> RimSpeedResult:
    """Calculate rim speed in SFM and MPM."""
    circumference_mm = math.pi * diameter_mm
    mpm = (circumference_mm * rpm) / 1000.0
    sfm = mpm * 3.28084  # meters to feet
    
    warning = None
    is_safe = True
    max_sfm = 10000.0
    
    if sfm > max_sfm:
        warning = f"Rim speed {sfm:.0f} SFM exceeds maximum {max_sfm:.0f} SFM"
        is_safe = False
    elif sfm > max_sfm * 0.9:
        warning = f"Rim speed {sfm:.0f} SFM approaching maximum"
    
    return RimSpeedResult(
        sfm=round(sfm, 1),
        mpm=round(mpm, 2),
        warning=warning,
        is_safe=is_safe,
        max_recommended_sfm=max_sfm,
    )


def _calc_bite_load(
    feed_mmpm: float,
    rpm: int,
    teeth_count: int,
) -> BiteLoadResult:
    """Calculate chipload (bite) per tooth."""
    if rpm <= 0 or teeth_count <= 0:
        return BiteLoadResult(
            chipload_mm=0.0,
            chipload_inch=0.0,
            warning="Invalid RPM or teeth count",
            is_optimal=False,
        )
    
    chipload_mm = feed_mmpm / (rpm * teeth_count)
    chipload_inch = chipload_mm / 25.4
    
    # Recommended range for wood
    min_cl, max_cl = 0.05, 0.15
    
    warning = None
    is_optimal = min_cl <= chipload_mm <= max_cl
    
    if chipload_mm < min_cl:
        warning = f"Chipload {chipload_mm:.4f}mm too low (rubbing/burning risk)"
    elif chipload_mm > max_cl:
        warning = f"Chipload {chipload_mm:.4f}mm too high (tearout/kickback risk)"
    
    return BiteLoadResult(
        chipload_mm=round(chipload_mm, 4),
        chipload_inch=round(chipload_inch, 5),
        warning=warning,
        is_optimal=is_optimal,
        recommended_range_mm=(min_cl, max_cl),
    )


def _calc_kickback(
    depth_mm: float,
    kerf_mm: float,
    hardness: str,
    feed_mmpm: float,
) -> KickbackResult:
    """Calculate kickback risk index."""
    # Factors affecting kickback
    factors: List[str] = []
    
    # Depth factor (deeper = more risk)
    depth_factor = min(depth_mm / 50.0, 1.0) * 25
    if depth_mm > 30:
        factors.append("Deep cut increases kickback potential")
    
    # Kerf factor (narrow kerf = more binding risk)
    kerf_factor = max(0, (3.0 - kerf_mm) / 3.0) * 15
    if kerf_mm < 2.0:
        factors.append("Narrow kerf increases binding risk")
    
    # Hardness factor
    hardness_scores = {"SOFT": 10, "MEDIUM": 20, "HARD": 30}
    hardness_factor = hardness_scores.get(hardness, 20)
    if hardness == "HARD":
        factors.append("Hard material increases resistance")
    
    # Feed rate factor (too slow = binding)
    if feed_mmpm < 500:
        feed_factor = 15
        factors.append("Slow feed rate may cause binding")
    else:
        feed_factor = 5
    
    risk_index = min(100, depth_factor + kerf_factor + hardness_factor + feed_factor)
    
    if risk_index < 30:
        severity = "LOW"
    elif risk_index < 50:
        severity = "MEDIUM"
    elif risk_index < 75:
        severity = "HIGH"
    else:
        severity = "CRITICAL"
    
    warning = None
    if severity in ("HIGH", "CRITICAL"):
        warning = f"High kickback risk ({risk_index:.0f}/100). Review cut parameters."
    
    return KickbackResult(
        risk_index=round(risk_index, 1),
        severity=severity,
        warning=warning,
        contributing_factors=factors,
    )


def _calc_heat_index(
    sfm: float,
    chipload_mm: float,
    hardness: str,
    ambient_temp_c: float,
) -> HeatIndexResult:
    """Calculate heat buildup index."""
    # Base thermal index from rim speed
    thermal_base = (sfm / 10000.0) * 50
    
    # Chipload factor (too low = more friction heat)
    if chipload_mm < 0.05:
        chipload_factor = 30
    elif chipload_mm < 0.08:
        chipload_factor = 15
    else:
        chipload_factor = 5
    
    # Hardness factor
    hardness_factors = {"SOFT": 10, "MEDIUM": 20, "HARD": 35}
    hardness_factor = hardness_factors.get(hardness, 20)
    
    thermal_index = thermal_base + chipload_factor + hardness_factor
    
    # Estimate temperature rise (rough approximation)
    temp_rise = thermal_index * 0.8  # degrees C
    
    if thermal_index < 40:
        burn_risk = "LOW"
    elif thermal_index < 70:
        burn_risk = "MEDIUM"
    else:
        burn_risk = "HIGH"
    
    warning = None
    if burn_risk == "HIGH":
        warning = f"High burn risk. Consider reducing speed or increasing feed."
    elif burn_risk == "MEDIUM":
        warning = "Moderate heat buildup expected. Monitor for burn marks."
    
    return HeatIndexResult(
        thermal_index=round(thermal_index, 1),
        estimated_temp_rise_c=round(temp_rise, 1),
        warning=warning,
        burn_risk=burn_risk,
    )


def _calc_deflection(
    diameter_mm: float,
    kerf_mm: float,
    depth_mm: float,
) -> DeflectionResult:
    """Calculate blade deflection at mid-span."""
    # Simplified deflection model
    # Real calculation would need blade thickness, material, etc.
    
    # Thinner blades (smaller kerf) deflect more
    kerf_factor = 3.0 / max(kerf_mm, 1.0)
    
    # Deeper cuts create more lateral force
    depth_factor = depth_mm / 50.0
    
    # Larger diameter = more stable
    diameter_factor = 254.0 / max(diameter_mm, 100.0)
    
    deflection_mm = 0.1 * kerf_factor * depth_factor * diameter_factor
    
    max_acceptable = 0.5
    is_acceptable = deflection_mm <= max_acceptable
    
    warning = None
    if not is_acceptable:
        warning = f"Excessive deflection ({deflection_mm:.2f}mm). May cause wandering cut."
    elif deflection_mm > max_acceptable * 0.7:
        warning = "Deflection approaching limit. Consider stabilization."
    
    return DeflectionResult(
        deflection_mm=round(deflection_mm, 3),
        warning=warning,
        is_acceptable=is_acceptable,
        max_acceptable_mm=max_acceptable,
    )


# ---------------------------------------------------------------------------
# Debug Endpoint
# ---------------------------------------------------------------------------

@router.post("/physics-debug", response_model=SawPhysicsDebugResponse)
async def physics_debug(
    request: SawPhysicsDebugRequest,
) -> SawPhysicsDebugResponse:
    """
    Run all saw physics calculators and return aggregated results.
    
    This endpoint is for the Saw Physics Debug Panel, providing
    detailed breakdowns of each calculator's output.
    """
    # Run individual calculators
    rim_speed = _calc_rim_speed(
        diameter_mm=request.tool.diameter_mm,
        rpm=request.rpm,
    )
    
    bite_load = _calc_bite_load(
        feed_mmpm=request.feed_mmpm,
        rpm=request.rpm,
        teeth_count=request.tool.teeth_count,
    )
    
    kickback = _calc_kickback(
        depth_mm=request.depth_mm,
        kerf_mm=request.tool.kerf_mm,
        hardness=request.material.hardness,
        feed_mmpm=request.feed_mmpm,
    )
    
    heat_index = _calc_heat_index(
        sfm=rim_speed.sfm,
        chipload_mm=bite_load.chipload_mm,
        hardness=request.material.hardness,
        ambient_temp_c=request.ambient_temp_c,
    )
    
    deflection = _calc_deflection(
        diameter_mm=request.tool.diameter_mm,
        kerf_mm=request.tool.kerf_mm,
        depth_mm=request.depth_mm,
    )
    
    # Aggregate warnings
    warnings: List[str] = []
    for result in [rim_speed, bite_load, kickback, heat_index, deflection]:
        if result.warning:
            warnings.append(result.warning)
    
    # Calculate overall score (weighted average)
    scores = {
        "rim_speed": 100 if rim_speed.is_safe else 50,
        "bite_load": 100 if bite_load.is_optimal else 60,
        "kickback": 100 - kickback.risk_index,
        "heat": 100 - heat_index.thermal_index,
        "deflection": 100 if deflection.is_acceptable else 50,
    }
    
    weights = {
        "rim_speed": 0.20,
        "bite_load": 0.25,
        "kickback": 0.20,
        "heat": 0.20,
        "deflection": 0.15,
    }
    
    overall_score = sum(scores[k] * weights[k] for k in scores)
    overall_score = max(0, min(100, overall_score))
    
    # Determine risk level
    if overall_score >= 80:
        risk_level = "GREEN"
    elif overall_score >= 50:
        risk_level = "YELLOW"
    else:
        risk_level = "RED"
    
    # Generate recommendations
    recommendations: List[str] = []
    if not bite_load.is_optimal:
        if bite_load.chipload_mm < 0.05:
            recommendations.append("Increase feed rate to reduce friction heat")
        else:
            recommendations.append("Reduce feed rate to prevent tearout")
    
    if kickback.severity in ("HIGH", "CRITICAL"):
        recommendations.append("Consider shallower cuts or slower feed")
    
    if heat_index.burn_risk == "HIGH":
        recommendations.append("Reduce speed or use cooling/dust collection")
    
    return SawPhysicsDebugResponse(
        request_summary={
            "tool": request.tool.model_dump(),
            "material": request.material.model_dump(),
            "rpm": request.rpm,
            "feed_mmpm": request.feed_mmpm,
            "depth_mm": request.depth_mm,
        },
        rim_speed=rim_speed,
        bite_load=bite_load,
        kickback=kickback,
        heat_index=heat_index,
        deflection=deflection,
        overall_score=round(overall_score, 1),
        risk_level=risk_level,
        warnings=warnings,
        recommendations=recommendations,
    )


@router.get("/physics-debug/health")
async def physics_debug_health() -> dict:
    """Health check for saw physics debug endpoint."""
    return {"status": "ok", "endpoint": "saw_physics_debug"}
