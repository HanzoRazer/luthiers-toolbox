"""
MRP-4A: SVG Translator

Governed SVG translator for Export Object visualization.

Provides styled SVG output with:
  - Layer-based coloring (blue outline, red voids)
  - Provenance metadata as XML comments
  - Proper viewBox for CAD-style viewing
"""

from app.cam.translators.svg.translator import (
    BodyOutlineSvgTranslator,
    SVG_TRANSLATOR_ID,
)

__all__ = [
    "BodyOutlineSvgTranslator",
    "SVG_TRANSLATOR_ID",
]
