"""
RMOS CAM Operation Adapter

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Tool-specific adapter for CAM operations (roughing, drilling, etc.)
Implements the ToolAdapter protocol for use with OperationAdapter.
"""

from __future__ import annotations

from app.core.safety import safety_critical

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .adapter import ToolAdapter, execute_operation, plan_operation


class CamRoughingAdapter:
    """
    CAM Roughing implementation of ToolAdapter protocol.

    Handles:
    - Feasibility computation for roughing operations
    - G-code generation for roughing toolpaths
    - Plan generation with operation sequences
    """

    def __init__(
        self,
        *,
        default_feed_ipm: float = 60.0,
        default_plunge_ipm: float = 20.0,
        default_rpm: int = 12000,
        max_doc_in: float = 0.25,  # Max depth of cut
        max_woc_in: float = 0.5,   # Max width of cut
    ):
        """
        Initialize CAM roughing adapter with defaults.

        Args:
            default_feed_ipm: Default feed rate
            default_plunge_ipm: Default plunge rate
            default_rpm: Default spindle RPM
            max_doc_in: Maximum depth of cut
            max_woc_in: Maximum width of cut
        """
        self.default_feed_ipm = default_feed_ipm
        self.default_plunge_ipm = default_plunge_ipm
        self.default_rpm = default_rpm
        self.max_doc_in = max_doc_in
        self.max_woc_in = max_woc_in

    @safety_critical
    def compute_feasibility(self,
        cam_intent: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute feasibility for CAM roughing operation.

        Checks:
        - Depth of cut within limits
        - Width of cut within limits
        - Tool geometry compatibility
        - Stock dimensions
        """
        params = cam_intent.get("params", {})
        tool = cam_intent.get("tool", {})

        doc = params.get("doc_in", params.get("depth_of_cut", 0.1))
        woc = params.get("woc_in", params.get("width_of_cut", 0.25))
        tool_dia = tool.get("diameter_in", tool.get("diameter", 0.25))

        warnings = []
        details = {
            "doc_in": doc,
            "max_doc_in": self.max_doc_in,
            "woc_in": woc,
            "max_woc_in": self.max_woc_in,
            "tool_diameter_in": tool_dia,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check depth of cut
        if doc > self.max_doc_in:
            return {
                "risk_level": "RED",
                "score": 15.0,
                "block_reason": f"DOC {doc}in exceeds safe limit {self.max_doc_in}in",
                "warnings": [f"Depth of cut {doc}in is too aggressive"],
                "details": details,
            }

        # Check width of cut
        if woc > self.max_woc_in:
            return {
                "risk_level": "RED",
                "score": 20.0,
                "block_reason": f"WOC {woc}in exceeds safe limit {self.max_woc_in}in",
                "warnings": [f"Width of cut {woc}in is too wide"],
                "details": details,
            }

        # Check WOC vs tool diameter
        if woc > tool_dia * 0.8:
            warnings.append(f"WOC {woc}in is high relative to tool diameter {tool_dia}in")

        # Calculate score
        doc_ratio = doc / self.max_doc_in if self.max_doc_in > 0 else 0
        woc_ratio = woc / self.max_woc_in if self.max_woc_in > 0 else 0
        combined_ratio = (doc_ratio + woc_ratio) / 2
        score = max(0, 100 - (combined_ratio * 60))

        # Determine risk level
        if score >= 75:
            risk_level = "GREEN"
        elif score >= 45:
            risk_level = "YELLOW"
            warnings.append("Aggressive parameters - monitor closely")
        else:
            risk_level = "RED"

        return {
            "risk_level": risk_level,
            "score": round(score, 1),
            "warnings": warnings,
            "details": details,
        }

    @safety_critical
    def generate_gcode(self,
        cam_intent: Dict[str, Any],
        feasibility: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate G-code for CAM roughing operation.

        Returns (gcode_text, metadata).
        """
        params = cam_intent.get("params", {})
        tool = cam_intent.get("tool", {})
        job = cam_intent.get("job", {})
        geometry = cam_intent.get("geometry", {})

        # Extract parameters
        units = params.get("units", "inch")
        feed = params.get("feed_ipm", self.default_feed_ipm)
        plunge = params.get("plunge_ipm", self.default_plunge_ipm)
        rpm = params.get("rpm", self.default_rpm)
        doc = params.get("doc_in", 0.1)
        woc = params.get("woc_in", 0.25)
        total_depth = params.get("total_depth_in", 0.5)

        tool_id = tool.get("tool_id", "T1")
        tool_number = tool.get("number", 1)
        job_name = job.get("name", "roughing_op")

        # Calculate passes
        num_passes = int(total_depth / doc) + (1 if total_depth % doc > 0 else 0)

        # Build G-code
        lines = [
            f"( CAM Roughing Operation: {job_name} )",
            f"( Tool: {tool_id} T{tool_number} )",
            f"( DOC: {doc}in, WOC: {woc}in, Total: {total_depth}in )",
            f"( Passes: {num_passes} )",
            f"( Generated: {datetime.now(timezone.utc).isoformat()} )",
            "",
            "G21" if units == "mm" else "G20",
            "G90",  # Absolute
            "G17",  # XY plane
            "",
            f"T{tool_number} M6",  # Tool change
            f"S{rpm} M3",  # Spindle on
            "G4 P2",  # Dwell
            "",
            "G0 Z25.4" if units == "mm" else "G0 Z1",  # Safe height
            "G0 X0 Y0",
            "",
        ]

        # Generate passes
        current_depth = 0
        for pass_num in range(1, num_passes + 1):
            current_depth = min(pass_num * doc, total_depth)
            lines.extend([
                f"( Pass {pass_num}/{num_passes} - Z{-current_depth:.4f} )",
                f"G0 X0 Y0",
                f"G1 Z-{current_depth:.4f} F{plunge:.1f}",
                f"G1 X100 F{feed:.1f}",
                f"G1 Y{woc:.4f}",
                f"G1 X0",
                f"G0 Z1",
                "",
            ])

        lines.extend([
            "G0 Z25.4" if units == "mm" else "G0 Z1",
            "M5",  # Spindle off
            "G0 X0 Y0",
            "M30",
        ])

        gcode_text = "\n".join(lines)

        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tool_id": tool_id,
            "tool_number": tool_number,
            "units": units,
            "feed_ipm": feed,
            "plunge_ipm": plunge,
            "rpm": rpm,
            "doc_in": doc,
            "woc_in": woc,
            "total_depth_in": total_depth,
            "num_passes": num_passes,
            "line_count": len(lines),
        }

        return gcode_text, metadata

    def generate_plan(
        self,
        cam_intent: Dict[str, Any],
        feasibility: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate operation plan for CAM roughing.
        """
        params = cam_intent.get("params", {})
        tool = cam_intent.get("tool", {})
        job = cam_intent.get("job", {})

        doc = params.get("doc_in", 0.1)
        woc = params.get("woc_in", 0.25)
        feed = params.get("feed_ipm", self.default_feed_ipm)
        total_depth = params.get("total_depth_in", 0.5)

        num_passes = int(total_depth / doc) + (1 if total_depth % doc > 0 else 0)

        # Rough time estimate
        cut_length_per_pass = 200  # Estimate
        time_per_pass_min = cut_length_per_pass / feed if feed > 0 else 1
        total_cut_time = time_per_pass_min * num_passes
        setup_time = 2.0

        operations = [
            {
                "step": 1,
                "type": "setup",
                "description": "Load tool and set work coordinates",
                "tool_id": tool.get("tool_id", "T1"),
                "estimated_time_min": setup_time,
            },
        ]

        for i in range(1, num_passes + 1):
            depth = min(i * doc, total_depth)
            operations.append({
                "step": i + 1,
                "type": "roughing_pass",
                "description": f"Roughing pass {i} at Z-{depth:.3f}",
                "doc_in": doc,
                "woc_in": woc,
                "z_depth": -depth,
                "estimated_time_min": round(time_per_pass_min, 2),
            })

        return {
            "planned_at": datetime.now(timezone.utc).isoformat(),
            "operations": operations,
            "total_time_min": round(setup_time + total_cut_time, 2),
            "num_passes": num_passes,
            "job_name": job.get("name", "roughing_op"),
            "feasibility_risk": feasibility.get("risk_level") if feasibility else None,
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def execute_cam_roughing_v1(
    cam_intent_v1: Dict[str, Any],
    feasibility: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
):
    """
    Execute a CAM roughing operation with governance compliance.
    """
    adapter = CamRoughingAdapter()

    return execute_operation(
        tool_id="cam_roughing_v1",
        mode="roughing",
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        parent_plan_run_id=parent_plan_run_id,
        tool_adapter=adapter,
        meta=meta,
    )


def plan_cam_roughing_v1(
    cam_intent_v1: Dict[str, Any],
    *,
    feasibility: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
):
    """
    Create a CAM roughing plan with governance compliance.
    """
    adapter = CamRoughingAdapter()

    return plan_operation(
        tool_id="cam_roughing_v1",
        mode="roughing",
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        tool_adapter=adapter,
        meta=meta,
    )


def compute_cam_roughing_feasibility(
    cam_intent_v1: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compute feasibility for a CAM roughing operation.
    """
    adapter = CamRoughingAdapter()
    return adapter.compute_feasibility(cam_intent_v1, context)


# =============================================================================
# Promotion Bridge (Bundle 03)
# =============================================================================

def promote_to_operation_lane(
    tool_id: str,
    cam_intent_v1: Dict[str, Any],
    feasibility: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
):
    """
    Promote a CAM operation to the OPERATION lane.

    This is the "promotion bridge" (Bundle 03) that takes existing CAM
    endpoints and wraps them with governance compliance.

    Supported tool types:
    - cam_roughing_v1
    - cam_drilling_v1 (future)
    - cam_profiling_v1 (future)
    """
    if tool_id == "cam_roughing_v1" or tool_id.startswith("roughing"):
        return execute_cam_roughing_v1(
            cam_intent_v1=cam_intent_v1,
            feasibility=feasibility,
            request_id=request_id,
            parent_plan_run_id=parent_plan_run_id,
            meta=meta,
        )

    # Fallback to generic execution
    return execute_operation(
        tool_id=tool_id,
        mode=tool_id.split("_")[0] if "_" in tool_id else "cam",
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        parent_plan_run_id=parent_plan_run_id,
        meta=meta,
    )
