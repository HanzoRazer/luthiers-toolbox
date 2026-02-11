"""Les Paul G-code generation package.

Split from lespaul_gcode_gen.py (593 lines) into mixin-based modules:
- primitives.py: Core G-code emission primitives
- perimeter.py: Body perimeter contour operation
- pockets.py: Pocket clearing operations
- drilling.py: Drilling and boring operations
- generator.py: Main class composing all mixins
"""

from .generator import LesPaulGCodeGenerator
from .primitives import GCodePrimitivesMixin
from .perimeter import PerimeterOperationMixin
from .pockets import PocketOperationsMixin
from .drilling import DrillingOperationsMixin

__all__ = [
    "LesPaulGCodeGenerator",
    "GCodePrimitivesMixin",
    "PerimeterOperationMixin",
    "PocketOperationsMixin",
    "DrillingOperationsMixin",
]
