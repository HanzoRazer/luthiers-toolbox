from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class GridPoint:
    id: str
    x: float
    y: float


@dataclass(frozen=True)
class Grid:
    units: str
    origin: str
    points: List[GridPoint]


def load_grid(path: Path) -> Grid:
    obj = json.loads(path.read_text(encoding="utf-8"))
    units = str(obj.get("units", "mm"))
    origin = str(obj.get("origin", "unknown"))
    pts = obj.get("points", [])
    points: List[GridPoint] = []
    for p in pts:
        points.append(GridPoint(id=str(p["id"]), x=float(p["x"]), y=float(p["y"])))
    if not points:
        raise ValueError("grid.json has no points")
    return Grid(units=units, origin=origin, points=points)
