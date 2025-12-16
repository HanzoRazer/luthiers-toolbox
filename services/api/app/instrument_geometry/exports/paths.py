"""
Export path management for CAM artifacts.

Target: instrument_geometry/exports/paths.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPaths:
    root: Path

    def ensure(self) -> "ExportPaths":
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def opplan_path(self, case_id: str, op_id: str) -> Path:
        return self.root / f"{case_id}__{op_id}.opplan.json"

    def gcode_path(self, case_id: str, op_id: str, post: str = "grbl") -> Path:
        return self.root / f"{case_id}__{op_id}.{post}.nc"
