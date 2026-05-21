"""
Luthier Manufacturing Strategy

CAM Dev Order 7S: Non-executable manufacturing cognition output.

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - generates_gcode always False
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


StrategyFamily = Literal[
    "rosette", "binding_channel", "neck_profile", "fret_slotting",
    "bridge_location", "body_outline", "fixture_setup", "inspection",
    "soundhole", "headstock", "bracing",
]
OperationFamily = StrategyFamily
ReviewStatus = Literal["draft", "pending_review", "approved_for_export_review", "rejected", "deferred"]


class LuthierManufacturingStrategy(BaseModel):
    """Non-executable manufacturing strategy artifact."""

    strategy_id: str = Field(default_factory=lambda: f"strategy-{uuid4().hex[:12]}")
    operation_family: StrategyFamily
    modality_id: str = ""
    display_name: str = ""
    description: str = ""

    geometry_reference_id: Optional[str] = None
    geometry_authority_ref_id: Optional[str] = None
    operation_sequence: List[str] = Field(default_factory=list)
    fixture_assumptions: List[str] = Field(default_factory=list)
    keepout_notes: List[str] = Field(default_factory=list)
    topology_warnings: List[str] = Field(default_factory=list)
    tool_assumptions: List[str] = Field(default_factory=list)
    review_notes: List[str] = Field(default_factory=list)

    # 7V: Fixture topology cognition refs (strategy may reference, not mutate)
    fixture_constraint_refs: List[str] = Field(default_factory=list)
    topology_evaluation_refs: List[str] = Field(default_factory=list)

    review_status: ReviewStatus = "draft"

    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)
    generates_gcode: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "LuthierManufacturingStrategy":
        if self.execution_authorized:
            raise ValueError("7S invariant violation: execution_authorized must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        if self.generates_gcode:
            raise ValueError("7S invariant violation: generates_gcode must be False")
        return self


LUTHIER_MANUFACTURING_STRATEGY_INDEX: Dict[str, LuthierManufacturingStrategy] = {}

STRATEGY_FAMILY_HINTS: Dict[StrategyFamily, Dict[str, List[str]]] = {
    "rosette": {
        "operation_sequence": ["Verify rosette diameter", "Mark center", "Route channel", "Test fit", "Install"],
        "keepout_notes": ["Avoid bracing locations", "Do not exceed top thickness"],
        "fixture_assumptions": ["Top secured flat", "Center marked"],
        "tool_assumptions": ["Sharp straight bit", "Correct diameter"],
    },
    "binding_channel": {
        "operation_sequence": ["Verify binding dimensions", "Set router depth", "Route channel", "Test fit"],
        "keepout_notes": ["Avoid neck pocket", "Watch waist curvature"],
        "fixture_assumptions": ["Body secured in fixture", "Bearing-guided cutter"],
        "tool_assumptions": ["Bearing-guided rabbeting bit"],
    },
    "neck_profile": {
        "operation_sequence": ["Rough blank", "Cut taper", "Route truss rod", "Shape profile", "Blend heel"],
        "keepout_notes": ["Truss rod channel clearance", "Fretboard overhang"],
        "fixture_assumptions": ["Neck blank secured", "Reference surfaces established"],
        "tool_assumptions": ["Ball nose or bullnose", "Straight bit for truss rod"],
    },
    "fret_slotting": {
        "operation_sequence": ["Verify scale length", "Set up slotting", "Cut slots", "Clean slots", "Test fit"],
        "keepout_notes": ["Do not slot past edges", "Binding channel overlap"],
        "fixture_assumptions": ["Fretboard secured flat", "Reference edge aligned"],
        "tool_assumptions": ["Fret slotting saw", "Depth stop"],
    },
    "soundhole": {
        "operation_sequence": ["Mark center", "Verify diameter", "Route/cut opening", "Verify edge quality"],
        "keepout_notes": ["Rosette channel first", "Do not cut bracing"],
        "fixture_assumptions": ["Top secured flat", "Center located"],
        "tool_assumptions": ["Circle cutter or router trammel"],
    },
}


class StrategyFamilyHint(BaseModel):
    family: str
    typical_sequence: List[str] = Field(default_factory=list)
    common_keepouts: List[str] = Field(default_factory=list)
    fixture_recommendations: List[str] = Field(default_factory=list)
    tool_recommendations: List[str] = Field(default_factory=list)


def get_family_hints(family: StrategyFamily) -> Optional[StrategyFamilyHint]:
    hints = STRATEGY_FAMILY_HINTS.get(family)
    if not hints:
        return None
    return StrategyFamilyHint(
        family=family,
        typical_sequence=hints.get("operation_sequence", []),
        common_keepouts=hints.get("keepout_notes", []),
        fixture_recommendations=hints.get("fixture_assumptions", []),
        tool_recommendations=hints.get("tool_assumptions", []),
    )


def create_manufacturing_strategy(
    operation_family: StrategyFamily,
    title: str = "",
    description: str = "",
    modality_id: str = "",
    operation_sequence: Optional[List[str]] = None,
    fixture_assumptions: Optional[List[str]] = None,
    keepout_notes: Optional[List[str]] = None,
) -> LuthierManufacturingStrategy:
    hints = STRATEGY_FAMILY_HINTS.get(operation_family, {})
    op_seq = list(hints.get("operation_sequence", []))
    fix_assump = list(hints.get("fixture_assumptions", []))
    keep_notes = list(hints.get("keepout_notes", []))
    tool_assump = list(hints.get("tool_assumptions", []))

    if operation_sequence:
        op_seq.extend(operation_sequence)
    if fixture_assumptions:
        fix_assump.extend(fixture_assumptions)
    if keepout_notes:
        keep_notes.extend(keepout_notes)

    display_name = title or f"{operation_family.replace('_', ' ').title()} Strategy"

    strategy = LuthierManufacturingStrategy(
        operation_family=operation_family,
        modality_id=modality_id,
        display_name=display_name,
        description=description,
        operation_sequence=op_seq,
        fixture_assumptions=fix_assump,
        keepout_notes=keep_notes,
        tool_assumptions=tool_assump,
    )
    LUTHIER_MANUFACTURING_STRATEGY_INDEX[strategy.strategy_id] = strategy
    return strategy


def get_manufacturing_strategy(strategy_id: str) -> Optional[LuthierManufacturingStrategy]:
    return LUTHIER_MANUFACTURING_STRATEGY_INDEX.get(strategy_id)


def list_manufacturing_strategies() -> List[LuthierManufacturingStrategy]:
    return list(LUTHIER_MANUFACTURING_STRATEGY_INDEX.values())


def list_strategies_by_family(operation_family: StrategyFamily) -> List[LuthierManufacturingStrategy]:
    return [s for s in LUTHIER_MANUFACTURING_STRATEGY_INDEX.values() if s.operation_family == operation_family]


def list_strategies_by_review_status(review_status: ReviewStatus) -> List[LuthierManufacturingStrategy]:
    return [s for s in LUTHIER_MANUFACTURING_STRATEGY_INDEX.values() if s.review_status == review_status]


def update_strategy_review_status(
    strategy_id: str, review_status: ReviewStatus, review_notes: Optional[str] = None
) -> Optional[LuthierManufacturingStrategy]:
    strategy = LUTHIER_MANUFACTURING_STRATEGY_INDEX.get(strategy_id)
    if not strategy:
        return None
    strategy.review_status = review_status
    if review_notes:
        strategy.review_notes.append(review_notes)
    return strategy


def clear_strategy_index() -> None:
    LUTHIER_MANUFACTURING_STRATEGY_INDEX.clear()
