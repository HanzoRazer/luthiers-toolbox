"""
CP-S30: Unified CAM-Core tool and preset schemas.

- tool_type polymorphism supports router bits now.
- saw_blade + drill_bit fields are included for future CP-S40+/drill work.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any


ToolType = Literal["router_bit", "saw_blade", "drill_bit"]
Units = Literal["mm", "inch"]


class ToolPreset(BaseModel):
    id: str
    name: str
    description: str = ""
    material_category: str = "all"

    # Canonical planned values (always metric)
    rpm: float = Field(..., gt=0)
    feed_mm_min: float = Field(..., gt=0)
    plunge_mm_min: Optional[float] = None
    ramp_mm_min: Optional[float] = None
    stepover_mm: Optional[float] = None
    stepdown_mm: Optional[float] = None

    # Optional chipload data (Fusion provides f_z / f_n sometimes)
    f_z_mm_tooth: Optional[float] = None
    f_n_mm_rev: Optional[float] = None

    raw: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(BaseModel):
    id: str
    name: str
    tool_type: ToolType
    vendor: Optional[str] = None
    source: Optional[str] = None
    source_guid: Optional[str] = None
    unit: Units = "mm"

    # Canonical geometry (always metric)
    diameter_mm: float = Field(..., gt=0)

    presets: List[ToolPreset] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class RouterBitTool(BaseTool):
    tool_type: Literal["router_bit"] = "router_bit"
    flute_count: int = Field(..., ge=1)
    flute_length_mm: Optional[float] = None
    overall_length_mm: Optional[float] = None
    shoulder_length_mm: Optional[float] = None
    taper_angle_deg: Optional[float] = None


class SawBladeTool(BaseTool):
    tool_type: Literal["saw_blade"] = "saw_blade"
    kerf_mm: float = Field(..., gt=0)
    tooth_count: int = Field(..., ge=1)
    max_rpm: float = Field(..., gt=0)
    rim_speed_min_m_min: Optional[float] = None
    rim_speed_max_m_min: Optional[float] = None

    # PoC preset modes per Saw Lab spec
    preset_modes: Optional[List[Dict[str, Any]]] = None


class DrillBitTool(BaseTool):
    tool_type: Literal["drill_bit"] = "drill_bit"
    tip_angle_deg: Optional[float] = None
