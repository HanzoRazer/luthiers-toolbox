"""
CAM Profile Schema (MM-2)

Defines machining parameters for different material types in rosette manufacturing.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

MaterialType = Literal[
    "wood",
    "metal",
    "shell",
    "paper",
    "foil",
    "charred",
    "resin",
    "composite",
]

CutDirection = Literal["climb", "conventional", "manual", "mixed"]

LaneHint = Literal["safe", "tuned_v1", "tuned_v2", "experimental", "archived"]


class CamProfile(BaseModel):
    """
    CAM profile defining feeds, speeds, and fragility for a material type.
    """
    id: str = Field(..., description="Unique profile ID")
    name: str = Field(..., description="Human-readable profile name")
    material_type: MaterialType = Field(..., description="Material type this profile applies to")
    recommended_tool: str = Field(..., description="Tool specification (e.g., 'vbit_60deg', 'endmill_1mm_carbide')")
    spindle_rpm: int = Field(..., description="Spindle speed in RPM")
    feed_rate_mm_min: int = Field(..., description="Cutting feed rate in mm/min")
    plunge_rate_mm_min: int = Field(..., description="Plunge/drilling feed rate in mm/min")
    stepdown_mm: float = Field(..., description="Maximum depth of cut per pass in mm")
    cut_direction: CutDirection = Field(..., description="Cutting direction preference")
    coolant: str = Field(..., description="Coolant/lubrication (e.g., 'none', 'mist', 'flood')")
    fragility_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Material fragility: 0.0 (robust) to 1.0 (extremely fragile)"
    )
    priority_lane_hint: Optional[LaneHint] = Field(
        default=None, 
        description="Suggested quality lane for jobs using this profile"
    )
    notes: Optional[str] = Field(
        default=None, 
        description="Additional machining notes or warnings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wood_standard",
                "name": "Wood – standard rosette cuts",
                "material_type": "wood",
                "recommended_tool": "vbit_60deg",
                "spindle_rpm": 18000,
                "feed_rate_mm_min": 1200,
                "plunge_rate_mm_min": 400,
                "stepdown_mm": 0.6,
                "cut_direction": "climb",
                "coolant": "none",
                "fragility_score": 0.2,
                "priority_lane_hint": "tuned_v1",
                "notes": "General-purpose profile for hardwood rosette channels."
            }
        }
