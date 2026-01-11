"""
Smart Guitar Schemas (SG-SBX-0.1)
=================================

Re-exports from sg-spec canonical package.
All schema definitions are now owned by sg-spec.

Install sg-spec:
    pip install git+https://github.com/HanzoRazer/sg-spec.git

Contract Version: 1.0
"""

# Re-export all schemas from sg-spec (canonical source of truth)
from sg_spec.schemas.sandbox_schemas import (
    # Version
    CONTRACT_VERSION,
    # Enums
    ModelVariant,
    Handedness,
    Connectivity,
    Feature,
    UnitSystem,
    CavityKind,
    ChannelKind,
    # Geometry models
    Vec2,
    BBox3D,
    Clearance,
    Mounting,
    ElectronicsComponent,
    # Spec subsystems
    PowerSpec,
    ThermalSpec,
    BodyDims,
    # Main spec
    SmartGuitarSpec,
    # CAM plan models
    PlanWarning,
    PlanError,
    CavityPlan,
    ChannelPlan,
    BracketPlan,
    ToolpathOp,
    SmartCamPlan,
    # Defaults
    DEFAULT_TOOLPATHS,
)

__all__ = [
    "CONTRACT_VERSION",
    "ModelVariant",
    "Handedness",
    "Connectivity",
    "Feature",
    "UnitSystem",
    "CavityKind",
    "ChannelKind",
    "Vec2",
    "BBox3D",
    "Clearance",
    "Mounting",
    "ElectronicsComponent",
    "PowerSpec",
    "ThermalSpec",
    "BodyDims",
    "SmartGuitarSpec",
    "PlanWarning",
    "PlanError",
    "CavityPlan",
    "ChannelPlan",
    "BracketPlan",
    "ToolpathOp",
    "SmartCamPlan",
    "DEFAULT_TOOLPATHS",
]
