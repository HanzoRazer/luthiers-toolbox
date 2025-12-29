"""
Grain Field Module

Interprets grain-related measurement data to produce:
  - Grain angle maps
  - Runout detection and zones
  - Checking (crack-prone) zones
  - Grain confidence scores

Sources:
  - tap_tone_pi tap_peaks.json (frequency patterns)
  - External grain maps (via provenance import)
  - Visual analysis inputs

Outputs:
  - Grain field overlay for geometry
  - CAM policy constraints for grain-sensitive zones
  - Advisory warnings for runout/checking
"""

from .service import GrainFieldService

__all__ = ["GrainFieldService"]
