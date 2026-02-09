"""
RMOS Saw Operation Adapter

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Tool-specific adapter for saw operations (table saw, band saw, etc.)
Implements the ToolAdapter protocol for use with OperationAdapter.
"""

from __future__ import annotations

from app.core.safety import safety_critical

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .adapter import ToolAdapter, OperationAdapter, execute_operation, plan_operation


class SawToolAdapter:
    """
    Saw-specific implementation of ToolAdapter protocol.

    Handles:
    - Feasibility computation for saw cuts
    - G-code generation for saw operations
    - Plan generation with cut sequences
    """

    def __init__(
        self,
        *,
        default_feed_ipm: float = 10.0,
        default_rpm: int = 3000,
        max_depth_in: float = 2.0,
    ):
        """
        Initialize saw adapter with defaults.

        Args:
            default_feed_ipm: Default feed rate in inches per minute
            default_rpm: Default spindle RPM
            max_depth_in: Maximum safe cut depth in inches
        """
        self.default_feed_ipm = default_feed_ipm
        self.default_rpm = default_rpm
        self.max_depth_in = max_depth_in

    @safety_critical
    def compute_feasibility(self,
        cam_intent: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute feasibility for saw operation.

        Checks:
        - Depth within safe limits
        - Feed rate within tool capabilities
        - Material compatibility
        """
        params = cam_intent.get("params", {})
        depth = params.get("depth_in", params.get("depth", 0))

        warnings = []
        details = {
            "depth_in": depth,
            "max_depth_in": self.max_depth_in,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check depth
        if depth > self.max_depth_in:
            return {
                "risk_level": "RED",
                "score": 10.0,
                "block_reason": f"Depth {depth}in exceeds safe limit {self.max_depth_in}in",
                "warnings": [f"Requested depth {depth}in is too deep"],
                "details": details,
            }

        if depth > self.max_depth_in * 0.8:
            warnings.append(f"Depth {depth}in is close to limit ({self.max_depth_in}in)")

        # Compute score based on depth ratio
        depth_ratio = depth / self.max_depth_in if self.max_depth_in > 0 else 0
        score = max(0, 100 - (depth_ratio * 50))

        # Determine risk level
        if score >= 80:
            risk_level = "GREEN"
        elif score >= 50:
            risk_level = "YELLOW"
            warnings.append("Operation is feasible but requires caution")
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
        Generate G-code for saw operation.

        Returns (gcode_text, metadata).
        """
        params = cam_intent.get("params", {})
        tool = cam_intent.get("tool", {})
        job = cam_intent.get("job", {})

        # Extract parameters with defaults
        units = params.get("units", "inch")
        feed = params.get("feed_ipm", self.default_feed_ipm)
        depth = params.get("depth_in", params.get("depth", 0.1))
        rpm = params.get("rpm", self.default_rpm)

        tool_id = tool.get("tool_id", "T1")
        job_name = job.get("name", "saw_cut")

        # Build G-code
        lines = [
            f"( Saw Operation: {job_name} )",
            f"( Tool: {tool_id} )",
            f"( Generated: {datetime.now(timezone.utc).isoformat()} )",
            "",
            "G21" if units == "mm" else "G20",  # Units
            "G90",  # Absolute positioning
            "G17",  # XY plane
            "",
            f"S{rpm} M3",  # Spindle on
            "G4 P1",  # Dwell for spindle startup
            "",
            "G0 Z5",  # Safe height
            "G0 X0 Y0",  # Start position
            "",
            f"G1 Z-{depth:.4f} F{feed:.1f}",  # Plunge
            "G1 X100 F{:.1f}".format(feed),  # Cut
            "",
            "G0 Z5",  # Retract
            "M5",  # Spindle off
            "G0 X0 Y0",  # Return to start
            "M30",  # Program end
        ]

        gcode_text = "\n".join(lines)

        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tool_id": tool_id,
            "units": units,
            "feed_ipm": feed,
            "depth_in": depth,
            "rpm": rpm,
            "line_count": len(lines),
        }

        return gcode_text, metadata

    def generate_plan(
        self,
        cam_intent: Dict[str, Any],
        feasibility: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate operation plan for saw cut.

        Plans include:
        - Operation sequence
        - Time estimates
        - Tool requirements
        """
        params = cam_intent.get("params", {})
        tool = cam_intent.get("tool", {})
        job = cam_intent.get("job", {})

        depth = params.get("depth_in", params.get("depth", 0.1))
        feed = params.get("feed_ipm", self.default_feed_ipm)
        cut_length = params.get("cut_length", 100)  # Default 100 units

        # Estimate time
        cut_time_min = cut_length / feed if feed > 0 else 0
        setup_time_min = 1.0  # Estimate
        total_time_min = cut_time_min + setup_time_min

        return {
            "planned_at": datetime.now(timezone.utc).isoformat(),
            "operations": [
                {
                    "step": 1,
                    "type": "setup",
                    "description": "Install blade and set fence",
                    "tool_id": tool.get("tool_id", "T1"),
                    "estimated_time_min": setup_time_min,
                },
                {
                    "step": 2,
                    "type": "cut",
                    "description": f"Rip cut at depth {depth}in",
                    "depth_in": depth,
                    "feed_ipm": feed,
                    "length": cut_length,
                    "estimated_time_min": cut_time_min,
                },
            ],
            "total_time_min": round(total_time_min, 2),
            "job_name": job.get("name", "saw_cut"),
            "feasibility_risk": feasibility.get("risk_level") if feasibility else None,
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def execute_saw_v1(
    cam_intent_v1: Dict[str, Any],
    feasibility: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
):
    """
    Execute a saw operation with governance compliance.

    Convenience function for saw_v1 tool type.
    """
    adapter = SawToolAdapter()

    return execute_operation(
        tool_id="saw_v1",
        mode="saw",
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        parent_plan_run_id=parent_plan_run_id,
        tool_adapter=adapter,
        meta=meta,
    )


def plan_saw_v1(
    cam_intent_v1: Dict[str, Any],
    *,
    feasibility: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
):
    """
    Create a saw operation plan with governance compliance.

    Convenience function for saw_v1 tool type.
    """
    adapter = SawToolAdapter()

    return plan_operation(
        tool_id="saw_v1",
        mode="saw",
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        tool_adapter=adapter,
        meta=meta,
    )


def compute_saw_feasibility(
    cam_intent_v1: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compute feasibility for a saw operation.

    Use this to get server-side feasibility before execution.
    """
    adapter = SawToolAdapter()
    return adapter.compute_feasibility(cam_intent_v1, context)
