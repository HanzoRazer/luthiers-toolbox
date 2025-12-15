# Patch N14.0 - Jig alignment and machine envelope (skeleton)

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JigAlignment:
    """
    Alignment of the rosette jig on the CNC or saw table.

    For now this is a purely geometric container; later bundles will
    derive offsets from ring radius, machine origin, etc.
    """
    origin_x_mm: float
    origin_y_mm: float
    rotation_deg: float = 0.0

    def as_dict(self) -> dict:
        return {
            "origin_x_mm": self.origin_x_mm,
            "origin_y_mm": self.origin_y_mm,
            "rotation_deg": self.rotation_deg,
        }


@dataclass
class MachineEnvelope:
    """
    Axis-aligned machine working volume.

    Z limits are included to support multi-pass depths later.
    """
    x_min_mm: float = 0.0
    y_min_mm: float = 0.0
    z_min_mm: float = -50.0
    x_max_mm: float = 1000.0
    y_max_mm: float = 1000.0
    z_max_mm: float = 0.0

    def contains(self, x_mm: float, y_mm: float, z_mm: float = 0.0) -> bool:
        return (
            self.x_min_mm <= x_mm <= self.x_max_mm
            and self.y_min_mm <= y_mm <= self.y_max_mm
            and self.z_min_mm <= z_mm <= self.z_max_mm
        )
