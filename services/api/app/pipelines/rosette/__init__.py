# services/api/app/pipelines/rosette/__init__.py
"""
Rosette Pipeline Module — legacy channel-dimension calculator.

Archived to __RECOVERED__/rosette_v1/:
  rosette_make_gcode.py, rosette_post_fill.py, rosette_to_dxf.py
"""

from .rosette_calc import compute

__all__ = [
    "compute",
]
