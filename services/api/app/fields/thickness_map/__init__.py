"""
Thickness Map Module

Interprets thickness measurements and MOE data to produce:
  - Thickness gradient maps
  - Voicing zones (tap-tuned regions)
  - Compliance checking against targets
  - Coupling with grain/brace for holistic policy

Sources:
  - tap_tone_pi moe_result.json (stiffness data)
  - Thickness measurements
  - Target voicing profiles

Outputs:
  - Thickness map overlay for geometry
  - CAM policy constraints for thickness-critical zones
  - Voicing compliance assessment
"""

from .service import ThicknessMapService

__all__ = ["ThicknessMapService"]
