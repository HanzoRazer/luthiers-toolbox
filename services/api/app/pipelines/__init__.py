# services/api/app/pipelines/__init__.py
"""
Pipeline modules migrated from legacy server.
Contains core calculation logic for lutherie operations.

Modules:
- rosette: Rosette design (calc, gcode, DXF, templates)
- bracing: Brace section calculations
- gcode_explainer: Human-readable G-code annotation
- bridge: Saddle compensation DXF generation
- dxf_cleaner: Convert entities to closed LWPOLYLINEs
- hardware: Hardware cavity DXF generation
- wiring: Pickup switch validation & treble bleed calculations
"""

from . import rosette
from . import bracing
from . import gcode_explainer
from . import bridge
from . import dxf_cleaner
from . import hardware
from . import wiring

__all__ = [
    "rosette",
    "bracing",
    "gcode_explainer",
    "bridge",
    "dxf_cleaner",
    "hardware",
    "wiring",
]
