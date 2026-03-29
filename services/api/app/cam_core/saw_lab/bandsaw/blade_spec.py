"""Bandsaw blade library — JSON-backed specs for physics and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BandsawBladeSpec:
    """
    Bandsaw blade for tension, drift, gullet feed, and curve limits.

    ``blade_family``: ``carbon_steel`` (55–70 MPa) or ``bi_metal`` (70–90 MPa) for tension stress band.
    """

    id: str
    width_mm: float
    thickness_mm: float
    tpi: float
    blade_family: str = "carbon_steel"
    kerf_mm: float = 0.6
    min_curve_radius_mm: Optional[float] = None
    vendor: str = ""
    notes: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def cross_section_mm2(self) -> float:
        return max(0.0, self.width_mm * self.thickness_mm)


def _blade_from_dict(d: Dict[str, Any]) -> BandsawBladeSpec:
    return BandsawBladeSpec(
        id=str(d.get("id", "unknown")),
        width_mm=float(d["width_mm"]),
        thickness_mm=float(d["thickness_mm"]),
        tpi=float(d["tpi"]),
        blade_family=str(d.get("blade_family", "carbon_steel")),
        kerf_mm=float(d.get("kerf_mm", 0.6)),
        min_curve_radius_mm=(
            float(d["min_curve_radius_mm"]) if d.get("min_curve_radius_mm") is not None else None
        ),
        vendor=str(d.get("vendor", "")),
        notes=str(d.get("notes", "")),
        raw=dict(d),
    )


def load_blade_library(path: Optional[Path] = None) -> List[BandsawBladeSpec]:
    """Load blade library JSON (default: package ``data/bandsaw_blades.json``)."""
    if path is None:
        path = Path(__file__).resolve().parent / "data" / "bandsaw_blades.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    blades = data.get("blades", data) if isinstance(data, dict) else data
    if not isinstance(blades, list):
        return []
    return [_blade_from_dict(b) for b in blades]


def get_blade_by_id(blade_id: str, path: Optional[Path] = None) -> Optional[BandsawBladeSpec]:
    for b in load_blade_library(path):
        if b.id == blade_id:
            return b
    return None
