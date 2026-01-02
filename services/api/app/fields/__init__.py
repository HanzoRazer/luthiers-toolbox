"""
Fields Module

Interpretation layers that couple measurement data with geometry
to produce design-relevant outputs and CAM policy constraints.

Submodules:
  - grain_field: Grain angle maps, runout detection, checking zones
  - brace_graph: Brace layout topology, scallop zones, structural analysis
  - thickness_map: Thickness gradients, voicing zones, tap-tuned deltas

These modules INTERPRET facts from tap_tone_pi to produce actionable
design and manufacturing guidance. They own the "novel coupling" that
standard mesh tools lack.
"""

from . import grain_field
from . import brace_graph
from . import thickness_map

__all__ = ["grain_field", "brace_graph", "thickness_map"]
