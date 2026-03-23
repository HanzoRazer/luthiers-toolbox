# services/api/app/routers/pipeline_context.py
"""Pipeline execution context and state management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .pipeline_schemas import DEFAULT_TOOL_DIAMETER_MM, PipelineOp


@dataclass
class PipelineContext:
    """Pipeline execution state passed between operations."""

    dxf_bytes: bytes
    dxf_filename: str
    client: Any  # httpx.AsyncClient - avoid import cycle

    # Shared parameters from request
    tool_d: float = DEFAULT_TOOL_DIAMETER_MM
    units: str = "mm"
    geometry_layer: Optional[str] = None
    auto_scale: bool = False
    cam_layer_prefix: str = "CAM_"
    machine_id: Optional[str] = None
    post_id: Optional[str] = None

    # Endpoint paths
    adaptive_plan_path: str = "/api/cam/pocket/adaptive/plan"
    sim_path: str = "/cam/simulate_gcode"
    machine_path: str = "/cam/machines"
    post_path: str = "/cam/posts"

    # Cached state
    loops: Optional[List] = None
    plan: Optional[Dict[str, Any]] = None
    plan_result: Optional[Dict[str, Any]] = None
    gcode: Optional[str] = None
    post_result: Optional[Dict[str, Any]] = None
    sim_result: Optional[Dict[str, Any]] = None
    machine_profile: Optional[Dict[str, Any]] = None
    post_profile: Optional[Dict[str, Any]] = None

    def merge_params(self, op: PipelineOp) -> Dict[str, Any]:
        """Merge operation params with shared defaults."""
        merged: Dict[str, Any] = {
            "tool_d": self.tool_d,
            "units": self.units,
            "geometry_layer": self.geometry_layer,
            "auto_scale": self.auto_scale,
            "cam_layer_prefix": self.cam_layer_prefix,
            "machine_id": self.machine_id,
            "post_id": self.post_id,
        }
        merged.update(op.params)
        return merged
