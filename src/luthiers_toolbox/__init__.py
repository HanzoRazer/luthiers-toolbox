"""
Luthier's Toolbox - Parametric CAD/CAM suite for guitar makers.

This package provides integrated tools for designing, costing, and manufacturing
guitars and other stringed instruments. It combines CAD design capabilities,
CAM toolpath generation, material costing, and tonewood analytics in a unified
workflow.

Modules:
    cad: Parametric design tools for instrument components
    cam: CNC toolpath generation and G-code export
    costing: Material and labor cost estimation
    tonewood: Wood properties database and acoustic analytics
"""

__version__ = "0.1.0"
__author__ = "Luthier's Toolbox Contributors"

from . import cad
from . import cam
from . import costing
from . import tonewood

__all__ = ["cad", "cam", "costing", "tonewood", "__version__"]
