"""
Brace Graph Module

Interprets brace layout as a structural graph to produce:
  - Topology validation (connected, no orphans)
  - Scallop zones (where braces taper)
  - Intersection analysis
  - Structural load paths

Sources:
  - Bracing layout JSON (from bracing pipeline)
  - Geometry mesh (for spatial mapping)

Outputs:
  - Brace graph overlay for geometry
  - CAM policy constraints for brace zones
  - No-cut zones at brace intersections
"""

from .service import BraceGraphService

__all__ = ["BraceGraphService"]
