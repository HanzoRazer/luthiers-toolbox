"""
RMOS Post-Processors Package

G-code post-processors for different machine controllers:
- grbl: GRBL-compatible controllers (ShapeOko, X-Carve, etc.)
- fanuc: FANUC CNC controllers

Registry Declarations:
    impl="app.rmos.posts.grbl:render"
    impl="app.rmos.posts.fanuc:render"
"""

from .grbl import render as grbl_render
from .fanuc import render as fanuc_render

__all__ = ["grbl_render", "fanuc_render"]
