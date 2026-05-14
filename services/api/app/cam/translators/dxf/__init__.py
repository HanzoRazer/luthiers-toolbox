"""
DXF Translators

MRP-3A: Governed DXF translators for Export Object serialization.

Dual-format support (from CLAUDE.md):
  - R12 (free tier): LINE entities for maximum CAM compatibility
  - R2000 (paid tier): LWPOLYLINE entities for modern CAM workflows

All translators wrap the existing governed dxf_writer.py infrastructure.
"""

from app.cam.translators.dxf.body_outline_translator import (
    BodyOutlineDxfTranslator,
    DXF_R12_TRANSLATOR_ID,
    DXF_R2000_TRANSLATOR_ID,
)

__all__ = [
    "BodyOutlineDxfTranslator",
    "DXF_R12_TRANSLATOR_ID",
    "DXF_R2000_TRANSLATOR_ID",
]
