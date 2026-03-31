"""
Archtop bridge spec (simplified Benedetto-style).

Complements archtop_floating_bridge.py with a compact ArchtopBridgeSpec dataclass
and direct compute_foot_arch / compute_post_holes utilities.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


def arch_radius_from_sagitta(span_mm: float, height_mm: float) -> float:
    """R = (w²/4 + h²) / (2h). Returns inf if height <= 0."""
    if height_mm <= 0:
        return float("inf")
    return (span_mm**2 / 4.0 + height_mm**2) / (2.0 * height_mm)


@dataclass
class ArchtopBridgeSpec:
    style: str = "benedetto"
    # Arch radius — measured wins over nominal
    body_arch_radius_mm: Optional[float] = 3048.0  # 120" nominal
    arch_span_mm: Optional[float] = None  # measured footprint width
    arch_height_mm: Optional[float] = None  # measured sagitta
    # Bridge dimensions
    base_length_mm: float = 155.0
    foot_width_mm: float = 4.5
    saddle_radius_mm: float = 381.0  # 15"
    post_spacing_mm: float = 74.6
    post_diameter_mm: float = 4.0  # M4
    string_spacing_ee_mm: float = 52.0
    material: str = "ebony"

    def resolved_arch_radius(self) -> float:
        if self.arch_span_mm and self.arch_height_mm:
            return arch_radius_from_sagitta(self.arch_span_mm, self.arch_height_mm)
        if self.body_arch_radius_mm:
            return self.body_arch_radius_mm
        raise ValueError(
            "Provide body_arch_radius_mm OR both arch_span_mm + arch_height_mm"
        )


def compute_foot_arch(spec: ArchtopBridgeSpec) -> dict:
    R = spec.resolved_arch_radius()
    span = spec.base_length_mm
    h = R - math.sqrt(max(0, R**2 - (span / 2) ** 2))
    return {
        "arch_radius_mm": round(R, 2),
        "foot_sagitta_mm": round(h, 3),
        "foot_contact_arc_mm": round(span, 1),
        "source": "measured" if spec.arch_span_mm else "nominal",
    }


def compute_post_holes(spec: ArchtopBridgeSpec) -> List[dict]:
    offset = spec.post_spacing_mm / 2
    return [
        {"x_mm": -offset, "y_mm": 0, "diameter_mm": spec.post_diameter_mm},
        {"x_mm": +offset, "y_mm": 0, "diameter_mm": spec.post_diameter_mm},
    ]
