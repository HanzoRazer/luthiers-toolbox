"""
Saw Lab Physics Debug Schemas

Provides request/response models for the Saw Physics Debug Panel.
Aggregates all calculator outputs into a single debug response.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SawPhysicsToolSpec(BaseModel):
    """Tool specification for physics debug."""
    diameter_mm: float = Field(default=254.0, ge=50.0, le=600.0)
    kerf_mm: float = Field(default=3.0, ge=0.5, le=10.0)
    teeth_count: int = Field(default=24, ge=10, le=120)


class SawPhysicsMaterialSpec(BaseModel):
    """Material specification for physics debug."""
    hardness: str = Field(default="MEDIUM", description="SOFT, MEDIUM, HARD")
    density_kgm3: float = Field(default=700.0, ge=100.0, le=2000.0)


class SawPhysicsDebugRequest(BaseModel):
    """
    Request for saw physics debug calculation.
    """
    tool: SawPhysicsToolSpec = Field(default_factory=SawPhysicsToolSpec)
    material: SawPhysicsMaterialSpec = Field(default_factory=SawPhysicsMaterialSpec)
    
    # Operating parameters
    rpm: int = Field(default=3000, ge=500, le=20000)
    feed_mmpm: float = Field(default=1000.0, ge=100.0, le=20000.0)
    depth_mm: float = Field(default=2.0, ge=0.1, le=100.0)
    ambient_temp_c: float = Field(default=25.0, ge=-20.0, le=60.0)


# ---------------------------------------------------------------------------
# Calculator Result Models
# ---------------------------------------------------------------------------

class RimSpeedResult(BaseModel):
    """Rim speed calculation result."""
    sfm: float = Field(..., description="Surface feet per minute")
    mpm: float = Field(..., description="Meters per minute")
    warning: Optional[str] = None
    is_safe: bool = True
    max_recommended_sfm: float = 10000.0


class BiteLoadResult(BaseModel):
    """Bite load (chipload) calculation result."""
    chipload_mm: float = Field(..., description="Chip load per tooth in mm")
    chipload_inch: float = Field(..., description="Chip load per tooth in inches")
    warning: Optional[str] = None
    is_optimal: bool = True
    recommended_range_mm: tuple[float, float] = (0.05, 0.15)


class KickbackResult(BaseModel):
    """Kickback risk calculation result."""
    risk_index: float = Field(..., ge=0.0, le=100.0, description="Kickback risk index 0-100")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    warning: Optional[str] = None
    contributing_factors: List[str] = Field(default_factory=list)


class HeatIndexResult(BaseModel):
    """Heat buildup calculation result."""
    thermal_index: float = Field(..., ge=0.0, description="Relative heat index")
    estimated_temp_rise_c: float = Field(..., description="Estimated temperature rise")
    warning: Optional[str] = None
    burn_risk: str = Field(default="LOW", description="LOW, MEDIUM, HIGH")


class DeflectionResult(BaseModel):
    """Blade deflection calculation result."""
    deflection_mm: float = Field(..., ge=0.0, description="Deflection at mid-span in mm")
    warning: Optional[str] = None
    is_acceptable: bool = True
    max_acceptable_mm: float = 0.5


# ---------------------------------------------------------------------------
# Aggregated Response
# ---------------------------------------------------------------------------

class SawPhysicsDebugResponse(BaseModel):
    """
    Aggregated response from all saw physics calculators.
    """
    # Input echo (for debugging)
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Calculator results
    rim_speed: RimSpeedResult
    bite_load: BiteLoadResult
    kickback: KickbackResult
    heat_index: HeatIndexResult
    deflection: DeflectionResult
    
    # Overall assessment
    overall_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str = Field(..., description="GREEN, YELLOW, RED")
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
