# Patch N14.0 + Bundle #13 (Part B) - CNC safety validator with advanced constraints

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import List, Optional

from .cnc_jig_geometry import MachineEnvelope
from .cnc_toolpath import ToolpathPlan, ToolpathSegment
from .cnc_kerf_physics import KerfPhysicsResult


@dataclass
class CNCSafetyDecision:
    decision: str  # "allow" | "block" | "override-required"
    risk_level: str  # "low" | "medium" | "high"
    requires_override: bool
    reasons: List[str] = field(default_factory=list)


def _segment_length_mm(seg: ToolpathSegment) -> float:
    """Calculate Euclidean distance for a single segment."""
    dx = seg.x_end_mm - seg.x_start_mm
    dy = seg.y_end_mm - seg.y_start_mm
    return sqrt(dx * dx + dy * dy)


def evaluate_cnc_safety(
    toolpaths: ToolpathPlan,
    envelope: MachineEnvelope,
    kerf_result: Optional[KerfPhysicsResult] = None,
    safe_feed_max_mm_per_min: Optional[float] = None,
    max_drift_deg: Optional[float] = None,
) -> CNCSafetyDecision:
    """
    Evaluate safety for a given toolpath plan with advanced constraints.

    Bundle #13 (Part B) - Enhanced safety logic:
      - Envelope checks (existing N14.0 behavior)
      - Feed rate validation against material limits
      - Kerf drift validation against angular thresholds

    Inputs:
      - toolpaths:    the planned motion segments
      - envelope:     machine workspace bounds
      - kerf_result:  kerf physics result (optional) from compute_kerf_physics
      - safe_feed_max_mm_per_min:
                      feed above this is considered elevated risk
      - max_drift_deg:
                      maximum allowed cumulative angular drift before
                      override/blocks

    Behavior:
      - If any segment start/end is outside the envelope: BLOCK, HIGH risk.
      - If feed exceeds safe_feed_max: override-required, MEDIUM risk.
      - If kerf drift exceeds max_drift_deg: override-required or escalate,
        depending on severity.

    Example:
        safety = evaluate_cnc_safety(
            toolpaths=plan,
            envelope=envelope,
            kerf_result=kerf,
            safe_feed_max_mm_per_min=1500.0,
            max_drift_deg=2.0,
        )
    """
    reasons: list[str] = []
    inside_all = True
    max_feed = 0.0
    max_len = 0.0

    # 1) Envelope checks
    for seg in toolpaths.segments:
        if not envelope.contains(seg.x_start_mm, seg.y_start_mm, seg.z_start_mm):
            inside_all = False
            reasons.append(
                f"Start point out of envelope: "
                f"({seg.x_start_mm:.2f}, {seg.y_start_mm:.2f}, {seg.z_start_mm:.2f})"
            )
        if not envelope.contains(seg.x_end_mm, seg.y_end_mm, seg.z_end_mm):
            inside_all = False
            reasons.append(
                f"End point out of envelope: "
                f"({seg.x_end_mm:.2f}, {seg.y_end_mm:.2f}, {seg.z_end_mm:.2f})"
            )

        feed = seg.feed_mm_per_min
        if feed > max_feed:
            max_feed = feed

        length = _segment_length_mm(seg)
        if length > max_len:
            max_len = length

    # Base decision from envelope
    if not inside_all:
        return CNCSafetyDecision(
            decision="block",
            risk_level="high",
            requires_override=True,
            reasons=reasons,
        )

    decision = "allow"
    risk_level = "low"
    requires_override = False

    # 2) Feed-based constraint
    if safe_feed_max_mm_per_min is not None and max_feed > safe_feed_max_mm_per_min:
        reasons.append(
            f"Max feed {max_feed:.0f} mm/min exceeds safe limit "
            f"{safe_feed_max_mm_per_min:.0f} mm/min."
        )
        decision = "override-required"
        risk_level = "medium"
        requires_override = True

    # 3) Kerf drift constraint
    if kerf_result is not None and max_drift_deg is not None:
        if kerf_result.drift_total_deg > max_drift_deg:
            reasons.append(
                f"Cumulative kerf drift {kerf_result.drift_total_deg:.2f}° "
                f"exceeds limit {max_drift_deg:.2f}°."
            )
            # If we were already override-required, keep that, maybe bump risk:
            if decision == "allow":
                decision = "override-required"
                risk_level = "medium"
                requires_override = True
            elif decision == "override-required":
                # escalate severity but keep same decision
                risk_level = "high"

    return CNCSafetyDecision(
        decision=decision,
        risk_level=risk_level,
        requires_override=requires_override,
        reasons=reasons,
    )
