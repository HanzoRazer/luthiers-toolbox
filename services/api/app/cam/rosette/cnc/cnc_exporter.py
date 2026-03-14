# Patch N14.0 - CNC export bundle skeleton
# Rosette Consolidation: absorbed cnc_simulation.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .cnc_toolpath import ToolpathPlan
from .cnc_jig_geometry import JigAlignment
from .cnc_safety_validator import CNCSafetyDecision


# ─────────────────────────────────────────────────────────────────────────────
# Simulation (absorbed from cnc_simulation.py)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CNCSimulationResult:
    passes: int
    estimated_runtime_sec: float
    max_feed_mm_per_min: float
    envelope_ok: bool


def simulate_toolpaths(
    toolpaths: ToolpathPlan,
    default_passes: int = 1,
    feed_scaling_factor: float = 1.0,
) -> CNCSimulationResult:
    """
    Very simple runtime estimator and envelope check.

    N14.x final behavior:
      - integrate distance along all segments
      - account for multi-pass Z depths

    N14.0 skeleton behavior:
      - uses a linear heuristic: runtime ~ sum(1 / feed) with a scalar.
    """
    if not toolpaths.segments:
        return CNCSimulationResult(
            passes=0,
            estimated_runtime_sec=0.0,
            max_feed_mm_per_min=0.0,
            envelope_ok=True,
        )

    max_feed = 0.0
    heuristic_sum = 0.0

    for seg in toolpaths.segments:
        feed = seg.feed_mm_per_min
        if feed <= 0:
            continue
        if feed > max_feed:
            max_feed = feed
        heuristic_sum += 1.0 / feed

    # Just an arbitrary scaling so numbers are nonzero/nonsilly.
    estimated_runtime_sec = heuristic_sum * 1000.0 * feed_scaling_factor

    return CNCSimulationResult(
        passes=default_passes,
        estimated_runtime_sec=estimated_runtime_sec,
        max_feed_mm_per_min=max_feed,
        envelope_ok=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Export Bundle
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CNCExportBundle:
    """
    Container for all CNC-related artifacts for a single ring export.

    N14.x will eventually include raw G-code text, operator checklist
    PDFs, and additional metadata.
    """
    ring_id: int
    toolpaths: ToolpathPlan
    jig_alignment: JigAlignment
    safety_decision: CNCSafetyDecision
    metadata: Dict[str, Any] = field(default_factory=dict)


def build_export_bundle_skeleton(
    ring_id: int,
    toolpaths: ToolpathPlan,
    jig_alignment: JigAlignment,
    safety_decision: CNCSafetyDecision,
) -> CNCExportBundle:
    """
    Simple constructor for the CNC export bundle.

    Later bundles will add:
      - G-code lines
      - operator_checklist.pdf generation
      - alignment.json serialization
    """
    metadata: Dict[str, Any] = {
        "ring_id": ring_id,
        "segment_count": len(toolpaths.segments),
        "origin": jig_alignment.as_dict(),
        "safety_decision": {
            "decision": safety_decision.decision,
            "risk_level": safety_decision.risk_level,
            "requires_override": safety_decision.requires_override,
            "reasons": safety_decision.reasons,
        },
    }

    return CNCExportBundle(
        ring_id=ring_id,
        toolpaths=toolpaths,
        jig_alignment=jig_alignment,
        safety_decision=safety_decision,
        metadata=metadata,
    )
