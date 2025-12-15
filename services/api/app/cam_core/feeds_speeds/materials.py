"""Material property placeholders for feeds & speeds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class MaterialProfile:
    name: str
    density: float
    hardness: float
    notes: str = ""


DEFAULT_MATERIALS: Dict[str, MaterialProfile] = {
    "hardwood": MaterialProfile(name="Hardwood", density=0.75, hardness=1.0),
    "softwood": MaterialProfile(name="Softwood", density=0.45, hardness=0.5),
}
