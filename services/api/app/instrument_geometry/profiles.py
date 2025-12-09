"""
Compatibility shim for instrument_geometry/profiles.py

This module is kept temporarily to avoid breaking existing imports.
New code should import from `instrument_geometry.neck.neck_profiles` instead.

Wave 14 Migration: This file will be removed in a future cleanup phase.
"""

# Re-export everything from the new location
from .neck.neck_profiles import (  # noqa: F401
    InstrumentSpec,
    FretboardSpec,
    BridgeSpec,
    RadiusProfile,
)

__all__ = [
    "InstrumentSpec",
    "FretboardSpec",
    "BridgeSpec",
    "RadiusProfile",
]
