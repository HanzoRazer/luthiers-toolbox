"""
RMOS Engines Module

Provides:
- FeasibilityEngine protocol and EngineInfo metadata
- get_feasibility_engine() for engine lookup
- list_feasibility_engines() for discovery
- REGISTRY singleton for toolchain/post-processor metadata
"""
from .base import FeasibilityEngine, EngineInfo
from .registry import (
    get_feasibility_engine,
    list_feasibility_engines,
    REGISTRY,
    EngineDescriptor,
    EngineRegistry,
)

__all__ = [
    "FeasibilityEngine",
    "EngineInfo",
    "get_feasibility_engine",
    "list_feasibility_engines",
    "REGISTRY",
    "EngineDescriptor",
    "EngineRegistry",
]
