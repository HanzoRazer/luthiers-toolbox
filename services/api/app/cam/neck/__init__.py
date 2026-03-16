# app/cam/neck/__init__.py

"""
Neck CNC Pipeline Module (LP-GAP-03)

Modular neck machining operations with full-scale station awareness.
Extends profile carving beyond 12" to cover complete neck length including heel.

Operations:
- Truss rod channel routing
- Full-scale profile carving (rough + finish)
- Fret slot integration
- Neck binding channel routing

Usage:
    from app.cam.neck import NeckPipeline, NeckPipelineConfig

    config = NeckPipelineConfig(
        scale_length_mm=628.65,  # Les Paul 24.75"
        profile_type="c_shape",
        fret_count=22,
    )

    pipeline = NeckPipeline(config)
    result = pipeline.generate()
"""

from .config import (
    NeckPipelineConfig,
    TrussRodConfig,
    ProfileCarvingConfig,
    FretSlotConfig,
    NeckToolSpec,
    DEFAULT_NECK_TOOLS,
)

from .truss_rod_channel import (
    TrussRodChannelGenerator,
    TrussRodResult,
)

from .profile_carving import (
    ProfileCarvingGenerator,
    ProfileCarvingResult,
    ProfileStation,
)

from .fret_slots import (
    FretSlotGenerator,
    FretSlotResult,
    FretSlotPosition,
)

from .orchestrator import (
    NeckPipeline,
    NeckPipelineResult,
)

__all__ = [
    # Config
    "NeckPipelineConfig",
    "TrussRodConfig",
    "ProfileCarvingConfig",
    "FretSlotConfig",
    "NeckToolSpec",
    "DEFAULT_NECK_TOOLS",
    # Truss Rod
    "TrussRodChannelGenerator",
    "TrussRodResult",
    # Profile Carving
    "ProfileCarvingGenerator",
    "ProfileCarvingResult",
    "ProfileStation",
    # Fret Slots
    "FretSlotGenerator",
    "FretSlotResult",
    "FretSlotPosition",
    # Orchestrator
    "NeckPipeline",
    "NeckPipelineResult",
]
