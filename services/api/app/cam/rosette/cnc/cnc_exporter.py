# Patch N14.0 - CNC export bundle skeleton

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .cnc_toolpath import ToolpathPlan
from .cnc_jig_geometry import JigAlignment
from .cnc_safety_validator import CNCSafetyDecision


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
