# services/api/app/cad/dxf_layers.py
"""
Centralized DXF layer definitions.

These layer names are used consistently across the CAD system to avoid
scattered string literals and ensure CAM compatibility.
"""

from __future__ import annotations

from typing import Final, Dict, List
from dataclasses import dataclass


# =============================================================================
# STANDARD LAYER NAMES
# =============================================================================

LAYER_OUTLINE: Final[str] = "OUTLINE"
LAYER_CONSTRUCTION: Final[str] = "CONSTRUCTION"
LAYER_INLAY: Final[str] = "INLAY"
LAYER_TEXT: Final[str] = "TEXT"
LAYER_DIMENSIONS: Final[str] = "DIMENSIONS"
LAYER_CENTERLINES: Final[str] = "CENTERLINES"
LAYER_TOOLPATH: Final[str] = "TOOLPATH"
LAYER_ANNOTATION: Final[str] = "ANNOTATION"

# Guitar-specific layers (for luthier workflows)
LAYER_BODY_OUTLINE: Final[str] = "BODY_OUTLINE"
LAYER_NECK_POCKET: Final[str] = "NECK_POCKET"
LAYER_PICKUP_CAVITY: Final[str] = "PICKUP_CAVITY"
LAYER_CONTROL_CAVITY: Final[str] = "CONTROL_CAVITY"
LAYER_BRIDGE: Final[str] = "BRIDGE"
LAYER_FRETS: Final[str] = "FRETS"
LAYER_INLAY_OUTLINE: Final[str] = "INLAY_OUTLINE"
LAYER_INLAY_POCKET: Final[str] = "INLAY_POCKET"
LAYER_ROSETTE: Final[str] = "ROSETTE"

# CAM operation layers
LAYER_ROUGHING: Final[str] = "CAM_ROUGHING"
LAYER_FINISHING: Final[str] = "CAM_FINISHING"
LAYER_DRILLING: Final[str] = "CAM_DRILLING"
LAYER_CONTOUR: Final[str] = "CAM_CONTOUR"


# =============================================================================
# LAYER CONFIGURATIONS
# =============================================================================

@dataclass(frozen=True)
class LayerConfig:
    """Configuration for a DXF layer."""
    name: str
    color_index: int  # AutoCAD ACI color (1-255)
    description: str
    lineweight: int = -1  # -1 = default
    linetype: str = "CONTINUOUS"


# Standard layers with their default colors
LAYER_CONFIGS: Dict[str, LayerConfig] = {
    LAYER_OUTLINE: LayerConfig(
        name=LAYER_OUTLINE,
        color_index=7,  # White/black
        description="Primary outline geometry",
    ),
    LAYER_CONSTRUCTION: LayerConfig(
        name=LAYER_CONSTRUCTION,
        color_index=8,  # Gray
        description="Construction/reference geometry",
    ),
    LAYER_INLAY: LayerConfig(
        name=LAYER_INLAY,
        color_index=5,  # Blue
        description="Inlay geometry",
    ),
    LAYER_TEXT: LayerConfig(
        name=LAYER_TEXT,
        color_index=2,  # Yellow
        description="Text annotations",
    ),
    LAYER_DIMENSIONS: LayerConfig(
        name=LAYER_DIMENSIONS,
        color_index=3,  # Green
        description="Dimension annotations",
    ),
    LAYER_CENTERLINES: LayerConfig(
        name=LAYER_CENTERLINES,
        color_index=1,  # Red
        description="Centerlines and axes",
        linetype="CENTER",
    ),
    LAYER_TOOLPATH: LayerConfig(
        name=LAYER_TOOLPATH,
        color_index=6,  # Magenta
        description="Toolpath preview geometry",
    ),
    
    # Guitar-specific
    LAYER_BODY_OUTLINE: LayerConfig(
        name=LAYER_BODY_OUTLINE,
        color_index=7,
        description="Guitar body perimeter",
    ),
    LAYER_NECK_POCKET: LayerConfig(
        name=LAYER_NECK_POCKET,
        color_index=4,  # Cyan
        description="Neck pocket cavity",
    ),
    LAYER_PICKUP_CAVITY: LayerConfig(
        name=LAYER_PICKUP_CAVITY,
        color_index=5,  # Blue
        description="Pickup routing cavities",
    ),
    LAYER_ROSETTE: LayerConfig(
        name=LAYER_ROSETTE,
        color_index=30,  # Orange
        description="Rosette pattern rings",
    ),
    
    # CAM layers
    LAYER_ROUGHING: LayerConfig(
        name=LAYER_ROUGHING,
        color_index=1,  # Red
        description="Roughing toolpath",
    ),
    LAYER_FINISHING: LayerConfig(
        name=LAYER_FINISHING,
        color_index=3,  # Green
        description="Finishing toolpath",
    ),
    LAYER_DRILLING: LayerConfig(
        name=LAYER_DRILLING,
        color_index=6,  # Magenta
        description="Drill points",
    ),
}


# Default layers to create in new documents
DEFAULT_LAYERS: Final[List[str]] = [
    LAYER_OUTLINE,
    LAYER_CONSTRUCTION,
    LAYER_INLAY,
    LAYER_TEXT,
    LAYER_DIMENSIONS,
    LAYER_CENTERLINES,
]


def get_layer_config(layer_name: str) -> LayerConfig:
    """
    Get configuration for a layer, with fallback for unknown layers.
    """
    if layer_name in LAYER_CONFIGS:
        return LAYER_CONFIGS[layer_name]
    
    # Fallback for custom/unknown layers
    return LayerConfig(
        name=layer_name,
        color_index=7,  # Default white/black
        description=f"Custom layer: {layer_name}",
    )


def get_all_layer_names() -> List[str]:
    """Return all defined layer names."""
    return list(LAYER_CONFIGS.keys())
