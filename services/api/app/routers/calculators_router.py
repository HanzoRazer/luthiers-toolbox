"""Wave 8: Calculators Router"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from dataclasses import dataclass, asdict

router = APIRouter(
    prefix="/calculators",
    tags=["calculators"],
)

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

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
    heat_risk: float  # 0–1, where 1 is worst
    category: str     # "COOL" / "WARM" / "HOT"
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
    risk_score: float  # 0–1
    category: str      # "LOW" / "MEDIUM" / "HIGH"
    message: str = ""

@dataclass 
class BitePerToothResult:
    """Saw blade bite per tooth (feed per tooth)."""
    bite_mm: Optional[float]
    in_range: bool
    min_recommended_mm: Optional[float] = None
    max_recommended_mm: Optional[float] = None
    message: str = ""

# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

ToolKind = Literal["router_bit", "saw_blade"]

class CutOperationPayload(BaseModel):
    """Request payload for cut operation evaluation."""
    tool_id: str = Field(..., description="Tool identifier from tool library")
    material_id: str = Field(..., description="Material identifier")
    tool_kind: ToolKind = Field(..., description="Type of cutting tool")
    
    feed_mm_min: float = Field(..., gt=0, description="Feed rate in mm/min")
    rpm: float = Field(..., gt=0, description="Spindle/blade RPM")
    depth_of_cut_mm: float = Field(..., gt=0, description="Axial depth of cut")
    width_of_cut_mm: Optional[float] = Field(None, gt=0, description="Radial width of cut")
    
    # Tool parameters (if not looked up from library)
    tool_diameter_mm: Optional[float] = Field(None, gt=0, description="Tool diameter")
    flute_count: Optional[int] = Field(None, gt=0, description="Number of flutes/teeth")
    
    # Optional context
    machine_id: Optional[str] = None
    profile_id: Optional[str] = None

class CalculatorBundleResponse(BaseModel):
    """Response with all calculator results."""
    tool_id: str
    material_id: str
    tool_kind: str
    
    chipload: Optional[Dict[str, Any]] = None
    heat: Optional[Dict[str, Any]] = None
    deflection: Optional[Dict[str, Any]] = None
    rim_speed: Optional[Dict[str, Any]] = None
    kickback: Optional[Dict[str, Any]] = None
    bite_per_tooth: Optional[Dict[str, Any]] = None
    
    warnings: List[str] = []
    hard_failures: List[str] = []
    
    overall_risk: str = "GREEN"  # "GREEN" / "YELLOW" / "RED"

# ---------------------------------------------------------------------------
# Calculator implementations
# ---------------------------------------------------------------------------

def calculate_chipload(
    feed_mm_min: float,
    rpm: float,
    flute_count: int,
    min_chipload: float = 0.05,
    max_chipload: float = 0.25,
) -> ChiploadResult:
    """
    Calculate chipload (feed per tooth) for router bits.
    
    Formula: chipload = feed_rate / (rpm * flute_count)
    """
    if rpm <= 0 or flute_count <= 0:
        return ChiploadResult(
            chipload_mm=None,
            in_range=False,
            message="Invalid RPM or flute count",
        )
    
    chipload = feed_mm_min / (rpm * flute_count)
    in_range = min_chipload <= chipload <= max_chipload
    
    if chipload < min_chipload:
        message = f"Chipload {chipload:.4f}mm is below minimum ({min_chipload}mm) - risk of rubbing/heat buildup"
    elif chipload > max_chipload:
        message = f"Chipload {chipload:.4f}mm exceeds maximum ({max_chipload}mm) - risk of tool breakage"
    else:
        message = f"Chipload {chipload:.4f}mm is within recommended range"
    
    return ChiploadResult(
        chipload_mm=chipload,
        in_range=in_range,
        min_recommended_mm=min_chipload,
        max_recommended_mm=max_chipload,
        message=message,
    )

def calculate_heat_risk(
    chipload_mm: Optional[float],
    rpm: float,
    depth_of_cut_mm: float,
    material_heat_sensitivity: float = 0.5,  # 0-1
) -> HeatResult:
    """Estimate heat risk based on cutting parameters."""
    if chipload_mm is None or chipload_mm <= 0:
        return HeatResult(
            heat_risk=0.8,
            category="HOT",
            message="Unable to calculate chipload - high heat risk assumed",
        )
    
    # Normalize factors
    chipload_factor = max(0, 1 - (chipload_mm / 0.15))  # Lower chipload = higher risk
    rpm_factor = min(1, rpm / 20000)  # Higher RPM = higher risk
    depth_factor = min(1, depth_of_cut_mm / 10)  # Deeper cut = higher risk
    
    # Combined risk
    heat_risk = (chipload_factor * 0.4 + rpm_factor * 0.3 + depth_factor * 0.2 + material_heat_sensitivity * 0.1)
    heat_risk = min(1.0, max(0.0, heat_risk))
    
    if heat_risk < 0.3:
        category = "COOL"
        message = "Low heat risk - parameters are conservative"
    elif heat_risk < 0.6:
        category = "WARM"
        message = "Moderate heat risk - monitor for burn marks"
    else:
        category = "HOT"
        message = "High heat risk - reduce RPM or increase feed rate"
    
    return HeatResult(
        heat_risk=heat_risk,
        category=category,
        message=message,
    )

def calculate_deflection(
    tool_diameter_mm: float,
    depth_of_cut_mm: float,
    width_of_cut_mm: Optional[float],
    stickout_mm: float = 25.0,  # Assumed stickout
) -> DeflectionResult:
    """Estimate tool deflection risk."""
    if tool_diameter_mm <= 0:
        return DeflectionResult(
            deflection_mm=None,
            risk="RED",
            message="Invalid tool diameter",
        )
    
    # Stickout ratio (higher = more deflection)
    stickout_ratio = stickout_mm / tool_diameter_mm
    
    # Cutting force proxy
    woc = width_of_cut_mm if width_of_cut_mm else tool_diameter_mm * 0.5
    force_proxy = depth_of_cut_mm * woc
    
    # Simplified deflection estimate (not physically accurate, just risk indicator)
    # Real deflection would need: material, tool material, actual stickout, etc.
    deflection_factor = (stickout_ratio ** 3) * force_proxy * 0.0001
    deflection_mm = deflection_factor
    
    if deflection_factor < 0.05:
        risk = "GREEN"
        message = f"Low deflection risk (estimated {deflection_mm:.4f}mm)"
    elif deflection_factor < 0.15:
        risk = "YELLOW"
        message = f"Moderate deflection risk (estimated {deflection_mm:.4f}mm) - consider reducing DOC"
    else:
        risk = "RED"
        message = f"High deflection risk (estimated {deflection_mm:.4f}mm) - reduce stickout or use larger tool"
    
    return DeflectionResult(
        deflection_mm=deflection_mm,
        risk=risk,
        message=message,
    )

def calculate_rim_speed(
    blade_diameter_mm: float,
    rpm: float,
    max_rim_speed_m_per_min: float = 80.0,
) -> RimSpeedResult:
    """
    Calculate saw blade rim (surface) speed.
    
    Formula: rim_speed = π × diameter × rpm / 1000 (for m/min)
    """
    import math
    
    if blade_diameter_mm <= 0 or rpm <= 0:
        return RimSpeedResult(
            surface_speed_m_per_min=None,
            within_limits=False,
            message="Invalid blade diameter or RPM",
        )
    
    rim_speed = math.pi * blade_diameter_mm * rpm / 1000
    within_limits = rim_speed <= max_rim_speed_m_per_min
    
    if within_limits:
        message = f"Rim speed {rim_speed:.1f} m/min is within limits"
    else:
        message = f"Rim speed {rim_speed:.1f} m/min EXCEEDS maximum ({max_rim_speed_m_per_min} m/min)"
    
    return RimSpeedResult(
        surface_speed_m_per_min=rim_speed,
        within_limits=within_limits,
        max_recommended_m_per_min=max_rim_speed_m_per_min,
        message=message,
    )

def calculate_bite_per_tooth(
    feed_mm_min: float,
    rpm: float,
    tooth_count: int,
    min_bite: float = 0.05,
    max_bite: float = 0.20,
) -> BitePerToothResult:
    """
    Calculate saw blade bite per tooth (feed per tooth).
    
    Formula: bite = feed_rate / (rpm * tooth_count)
    """
    if rpm <= 0 or tooth_count <= 0:
        return BitePerToothResult(
            bite_mm=None,
            in_range=False,
            message="Invalid RPM or tooth count",
        )
    
    bite = feed_mm_min / (rpm * tooth_count)
    in_range = min_bite <= bite <= max_bite
    
    if bite < min_bite:
        message = f"Bite {bite:.4f}mm is below minimum - risk of rubbing/burning"
    elif bite > max_bite:
        message = f"Bite {bite:.4f}mm exceeds maximum - risk of tooth damage"
    else:
        message = f"Bite {bite:.4f}mm is within recommended range"
    
    return BitePerToothResult(
        bite_mm=bite,
        in_range=in_range,
        min_recommended_mm=min_bite,
        max_recommended_mm=max_bite,
        message=message,
    )

def calculate_kickback_risk(
    depth_of_cut_mm: float,
    blade_diameter_mm: float,
    tooth_count: int,
    feed_mm_min: float,
) -> KickbackRiskResult:
    """Estimate kickback risk for saw operations."""
    # Depth ratio (deeper = more risk)
    max_depth = blade_diameter_mm * 0.4  # Rule of thumb: max 40% of blade diameter
    depth_ratio = min(1.0, depth_of_cut_mm / max_depth) if max_depth > 0 else 1.0
    
    # Feed aggressiveness
    feed_factor = min(1.0, feed_mm_min / 5000)
    
    # Tooth density factor (more teeth = less risk per tooth)
    tooth_factor = max(0, 1 - (tooth_count / 100))
    
    risk_score = depth_ratio * 0.5 + feed_factor * 0.3 + tooth_factor * 0.2
    risk_score = min(1.0, max(0.0, risk_score))
    
    if risk_score < 0.3:
        category = "LOW"
        message = "Low kickback risk"
    elif risk_score < 0.6:
        category = "MEDIUM"
        message = "Moderate kickback risk - ensure proper workholding"
    else:
        category = "HIGH"
        message = "HIGH kickback risk - reduce depth or feed rate"
    
    return KickbackRiskResult(
        risk_score=risk_score,
        category=category,
        message=message,
    )

# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------

def evaluate_cut_operation(payload: CutOperationPayload) -> CalculatorBundleResponse:
    """
    Evaluate a cut operation and return all relevant calculator results.
    """
    warnings: List[str] = []
    hard_failures: List[str] = []
    
    chipload_res = None
    heat_res = None
    deflection_res = None
    rim_speed_res = None
    kickback_res = None
    bite_res = None
    
    # Get tool parameters
    tool_diameter = payload.tool_diameter_mm or 6.0  # Default 6mm
    flute_count = payload.flute_count or 2  # Default 2 flutes
    
    if payload.tool_kind == "router_bit":
        # Router bit calculations
        chipload_res = calculate_chipload(
            feed_mm_min=payload.feed_mm_min,
            rpm=payload.rpm,
            flute_count=flute_count,
        )
        
        heat_res = calculate_heat_risk(
            chipload_mm=chipload_res.chipload_mm,
            rpm=payload.rpm,
            depth_of_cut_mm=payload.depth_of_cut_mm,
        )
        
        deflection_res = calculate_deflection(
            tool_diameter_mm=tool_diameter,
            depth_of_cut_mm=payload.depth_of_cut_mm,
            width_of_cut_mm=payload.width_of_cut_mm,
        )
        
        # Collect warnings
        if chipload_res and not chipload_res.in_range:
            warnings.append(chipload_res.message)
        if heat_res and heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if deflection_res and deflection_res.risk == "RED":
            hard_failures.append(deflection_res.message)
        elif deflection_res and deflection_res.risk == "YELLOW":
            warnings.append(deflection_res.message)
            
    elif payload.tool_kind == "saw_blade":
        # Saw blade calculations
        blade_diameter = tool_diameter  # Reuse tool_diameter field
        tooth_count = flute_count  # Reuse flute_count as tooth_count
        
        rim_speed_res = calculate_rim_speed(
            blade_diameter_mm=blade_diameter,
            rpm=payload.rpm,
        )
        
        bite_res = calculate_bite_per_tooth(
            feed_mm_min=payload.feed_mm_min,
            rpm=payload.rpm,
            tooth_count=tooth_count,
        )
        
        heat_res = calculate_heat_risk(
            chipload_mm=bite_res.bite_mm if bite_res else None,
            rpm=payload.rpm,
            depth_of_cut_mm=payload.depth_of_cut_mm,
        )
        
        kickback_res = calculate_kickback_risk(
            depth_of_cut_mm=payload.depth_of_cut_mm,
            blade_diameter_mm=blade_diameter,
            tooth_count=tooth_count,
            feed_mm_min=payload.feed_mm_min,
        )
        
        # Collect warnings
        if rim_speed_res and not rim_speed_res.within_limits:
            hard_failures.append(rim_speed_res.message)
        if bite_res and not bite_res.in_range:
            warnings.append(bite_res.message)
        if heat_res and heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if kickback_res and kickback_res.category == "HIGH":
            hard_failures.append(kickback_res.message)
        elif kickback_res and kickback_res.category == "MEDIUM":
            warnings.append(kickback_res.message)
    
    # Determine overall risk
    if hard_failures:
        overall_risk = "RED"
    elif warnings:
        overall_risk = "YELLOW"
    else:
        overall_risk = "GREEN"
    
    return CalculatorBundleResponse(
        tool_id=payload.tool_id,
        material_id=payload.material_id,
        tool_kind=payload.tool_kind,
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

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=CalculatorBundleResponse)
def evaluate_cut(payload: CutOperationPayload) -> CalculatorBundleResponse:
    """Evaluate a cut operation and return all calculator results."""
    return evaluate_cut_operation(payload)

# Alias for Calculator Spine API compatibility
@router.post("/evaluate-cut", response_model=CalculatorBundleResponse)
def evaluate_cut_alias(payload: CutOperationPayload) -> CalculatorBundleResponse:
    """
    Alias for /evaluate - provides Calculator Spine API compatibility.
    
    See /evaluate for full documentation.
    """
    return evaluate_cut_operation(payload)

@router.get("/health")
def calculator_health():
    """Health check for calculator service."""
    return {
        "status": "ok",
        "calculators": [
            "chipload",
            "heat_risk",
            "deflection",
            "rim_speed",
            "bite_per_tooth",
            "kickback_risk",
        ],
        "tool_kinds": ["router_bit", "saw_blade"],
    }
