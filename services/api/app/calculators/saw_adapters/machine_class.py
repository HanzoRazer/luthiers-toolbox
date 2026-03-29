"""
Machine class for saw/CAM routing — rim speed and curve-cutting capability.

Use with saw_lab and calculator adapters.
"""

from __future__ import annotations

from enum import Enum


class MachineClass(str, Enum):
    """Primary woodworking saw categories."""

    TABLE_SAW = "table_saw"
    CIRCULAR_SAW = "circular_saw"
    BANDSAW = "bandsaw"
    SCROLL_SAW = "scroll_saw"
    JIGSAW = "jigsaw"

    @property
    def uses_rim_speed(self) -> bool:
        """True when surface speed at the cutting circle is meaningful for feeds/heat."""
        return self in (
            MachineClass.TABLE_SAW,
            MachineClass.CIRCULAR_SAW,
            MachineClass.BANDSAW,
            MachineClass.SCROLL_SAW,
            MachineClass.JIGSAW,
        )

    @property
    def supports_curves(self) -> bool:
        """True for machines commonly used for curved cuts (not straight-only)."""
        return self in (
            MachineClass.BANDSAW,
            MachineClass.SCROLL_SAW,
            MachineClass.JIGSAW,
        )


__all__ = ["MachineClass"]
