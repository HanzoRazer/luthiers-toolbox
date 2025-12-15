"""
RMOS Presets System

Provides material and tool presets for RMOS context building.

Presets allow:
- Quick selection of common materials (maple, walnut, MDF, etc.)
- Quick selection of common tools (3.175mm endmill, 6mm endmill, etc.)
- Building RmosContext from preset IDs instead of manual parameters
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Preset Models
# ---------------------------------------------------------------------------

class MaterialPreset(BaseModel):
    """
    Material preset for RMOS context.
    """
    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Display name")
    description: Optional[str] = None
    
    # Material properties
    hardness: str = Field(default="MEDIUM", description="SOFT, MEDIUM, HARD")
    density_kgm3: float = Field(default=700.0, ge=100.0, le=2000.0)
    burn_tendency: float = Field(default=0.5, ge=0.0, le=1.0)
    tearout_tendency: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Recommended feeds/speeds
    recommended_feed_mm_min: Optional[float] = None
    recommended_rpm: Optional[int] = None


class ToolPreset(BaseModel):
    """
    Tool preset for RMOS context.
    """
    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Display name")
    description: Optional[str] = None
    
    # Tool properties
    diameter_mm: float = Field(..., gt=0.0, le=300.0)  # Increased to 300mm for saw blades
    flute_count: int = Field(default=2, ge=1, le=8)
    tool_type: str = Field(default="endmill", description="endmill, ballnose, vbit, saw, etc.")
    
    # Optional saw-specific properties
    kerf_mm: Optional[float] = None
    tooth_count: Optional[int] = None


class PresetCollection(BaseModel):
    """Collection of material and tool presets."""
    materials: List[MaterialPreset] = Field(default_factory=list)
    tools: List[ToolPreset] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in Presets
# ---------------------------------------------------------------------------

BUILTIN_MATERIAL_PRESETS: List[MaterialPreset] = [
    MaterialPreset(
        id="maple_hard",
        name="Hard Maple",
        description="Dense hardwood, common for guitar necks",
        hardness="HARD",
        density_kgm3=720.0,
        burn_tendency=0.6,
        tearout_tendency=0.3,
        recommended_feed_mm_min=1500,
        recommended_rpm=18000,
    ),
    MaterialPreset(
        id="walnut",
        name="Black Walnut",
        description="Medium hardwood, common for guitar bodies",
        hardness="MEDIUM",
        density_kgm3=640.0,
        burn_tendency=0.4,
        tearout_tendency=0.4,
        recommended_feed_mm_min=1800,
        recommended_rpm=18000,
    ),
    MaterialPreset(
        id="mahogany",
        name="Mahogany",
        description="Classic tonewood for guitar bodies",
        hardness="MEDIUM",
        density_kgm3=560.0,
        burn_tendency=0.3,
        tearout_tendency=0.5,
        recommended_feed_mm_min=2000,
        recommended_rpm=16000,
    ),
    MaterialPreset(
        id="rosewood",
        name="Indian Rosewood",
        description="Dense hardwood for fretboards and bridges",
        hardness="HARD",
        density_kgm3=850.0,
        burn_tendency=0.2,
        tearout_tendency=0.3,
        recommended_feed_mm_min=1200,
        recommended_rpm=20000,
    ),
    MaterialPreset(
        id="ebony",
        name="Ebony",
        description="Very dense hardwood for fretboards",
        hardness="HARD",
        density_kgm3=1050.0,
        burn_tendency=0.1,
        tearout_tendency=0.2,
        recommended_feed_mm_min=1000,
        recommended_rpm=22000,
    ),
    MaterialPreset(
        id="mdf",
        name="MDF",
        description="Medium-density fiberboard for templates",
        hardness="SOFT",
        density_kgm3=750.0,
        burn_tendency=0.7,
        tearout_tendency=0.1,
        recommended_feed_mm_min=3000,
        recommended_rpm=12000,
    ),
    MaterialPreset(
        id="plywood_baltic",
        name="Baltic Birch Plywood",
        description="High-quality plywood for jigs and fixtures",
        hardness="MEDIUM",
        density_kgm3=680.0,
        burn_tendency=0.4,
        tearout_tendency=0.6,
        recommended_feed_mm_min=2500,
        recommended_rpm=14000,
    ),
    MaterialPreset(
        id="acrylic",
        name="Acrylic (Cast)",
        description="Clear plastic for templates and guards",
        hardness="MEDIUM",
        density_kgm3=1180.0,
        burn_tendency=0.8,
        tearout_tendency=0.1,
        recommended_feed_mm_min=1500,
        recommended_rpm=10000,
    ),
]


BUILTIN_TOOL_PRESETS: List[ToolPreset] = [
    ToolPreset(
        id="em_3.175",
        name="1/8\" Endmill",
        description="3.175mm (1/8\") 2-flute endmill",
        diameter_mm=3.175,
        flute_count=2,
        tool_type="endmill",
    ),
    ToolPreset(
        id="em_6.0",
        name="6mm Endmill",
        description="6mm 2-flute endmill",
        diameter_mm=6.0,
        flute_count=2,
        tool_type="endmill",
    ),
    ToolPreset(
        id="em_6.35",
        name="1/4\" Endmill",
        description="6.35mm (1/4\") 2-flute endmill",
        diameter_mm=6.35,
        flute_count=2,
        tool_type="endmill",
    ),
    ToolPreset(
        id="em_12.7",
        name="1/2\" Endmill",
        description="12.7mm (1/2\") 2-flute endmill",
        diameter_mm=12.7,
        flute_count=2,
        tool_type="endmill",
    ),
    ToolPreset(
        id="ball_3.175",
        name="1/8\" Ball Nose",
        description="3.175mm (1/8\") ball nose for 3D carving",
        diameter_mm=3.175,
        flute_count=2,
        tool_type="ballnose",
    ),
    ToolPreset(
        id="ball_6.0",
        name="6mm Ball Nose",
        description="6mm ball nose for 3D carving",
        diameter_mm=6.0,
        flute_count=2,
        tool_type="ballnose",
    ),
    ToolPreset(
        id="vbit_60",
        name="60° V-Bit",
        description="60-degree V-bit for engraving",
        diameter_mm=6.35,
        flute_count=1,
        tool_type="vbit",
    ),
    ToolPreset(
        id="vbit_90",
        name="90° V-Bit",
        description="90-degree V-bit for chamfers",
        diameter_mm=12.7,
        flute_count=2,
        tool_type="vbit",
    ),
    # Saw blades
    ToolPreset(
        id="saw_10_24",
        name="10\" 24T Saw",
        description="10-inch 24-tooth saw blade",
        diameter_mm=254.0,
        tool_type="saw",
        kerf_mm=3.0,
        tooth_count=24,
    ),
    ToolPreset(
        id="saw_10_60",
        name="10\" 60T Saw",
        description="10-inch 60-tooth fine-cut saw blade",
        diameter_mm=254.0,
        tool_type="saw",
        kerf_mm=2.5,
        tooth_count=60,
    ),
]


# ---------------------------------------------------------------------------
# Preset Registry
# ---------------------------------------------------------------------------

class PresetRegistry:
    """
    Registry for material and tool presets.
    
    Provides lookup by ID and listing of all presets.
    Can be extended with custom presets at runtime.
    """
    
    def __init__(self):
        self._materials: Dict[str, MaterialPreset] = {}
        self._tools: Dict[str, ToolPreset] = {}
        
        # Load built-in presets
        for preset in BUILTIN_MATERIAL_PRESETS:
            self._materials[preset.id] = preset
        for preset in BUILTIN_TOOL_PRESETS:
            self._tools[preset.id] = preset
    
    def get_material(self, preset_id: str) -> Optional[MaterialPreset]:
        """Get a material preset by ID."""
        return self._materials.get(preset_id)
    
    def get_tool(self, preset_id: str) -> Optional[ToolPreset]:
        """Get a tool preset by ID."""
        return self._tools.get(preset_id)
    
    def list_materials(self) -> List[MaterialPreset]:
        """List all material presets."""
        return list(self._materials.values())
    
    def list_tools(self) -> List[ToolPreset]:
        """List all tool presets."""
        return list(self._tools.values())
    
    def add_material(self, preset: MaterialPreset) -> None:
        """Add or update a material preset."""
        self._materials[preset.id] = preset
    
    def add_tool(self, preset: ToolPreset) -> None:
        """Add or update a tool preset."""
        self._tools[preset.id] = preset
    
    def remove_material(self, preset_id: str) -> bool:
        """Remove a material preset. Returns True if removed."""
        if preset_id in self._materials:
            del self._materials[preset_id]
            return True
        return False
    
    def remove_tool(self, preset_id: str) -> bool:
        """Remove a tool preset. Returns True if removed."""
        if preset_id in self._tools:
            del self._tools[preset_id]
            return True
        return False
    
    def get_collection(self) -> PresetCollection:
        """Get all presets as a collection."""
        return PresetCollection(
            materials=self.list_materials(),
            tools=self.list_tools(),
        )


# Global registry instance
_registry: Optional[PresetRegistry] = None


def get_preset_registry() -> PresetRegistry:
    """Get the global preset registry, creating if needed."""
    global _registry
    if _registry is None:
        _registry = PresetRegistry()
    return _registry
