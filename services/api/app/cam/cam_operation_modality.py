"""
CAM Operation Modality

CAM Dev Order 7S: Operation modality vocabulary and classification.

Provides:
  - Operation modality vocabulary
  - Cutter family classification
  - Luthier-specific strategy modalities
  - Safety profile support

7S invariants:
  - executable_modality always False (cognition only)
  - machine_output_allowed always False
  - requires_human_review True for all luthier modalities

Salvaged pattern:
  CNC / laser / plasma / drag_knife / pen_plotter modality split
  from OpenBuilds-CAM review, implemented as repo-native vocabulary.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


CutterFamily = Literal[
    "router",
    "laser",
    "plasma",
    "drag_knife",
    "pen_plotter",
    "luthier_strategy",
    "inspection",
    "fixture_setup",
]


class CAMOperationModality(BaseModel):
    """
    Operation modality vocabulary entry.

    Modalities classify manufacturing operations by cutter family,
    safety requirements, and review needs.

    7S invariants (model-enforced):
      - executable_modality always False
      - machine_output_allowed always False
    """

    modality_id: str = Field(..., description="Unique modality identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Modality description")

    cutter_family: CutterFamily = Field(
        ..., description="Cutter family classification"
    )

    executable_modality: bool = Field(
        default=False,
        description="Always False — 7S modalities are cognition only"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )
    requires_human_review: bool = Field(
        default=True,
        description="Whether operation requires human review before execution"
    )

    safety_warnings: List[str] = Field(
        default_factory=list,
        description="Safety warnings for this modality"
    )

    typical_operations: List[str] = Field(
        default_factory=list,
        description="Typical operation names for this modality"
    )

    luthier_specific: bool = Field(
        default=False,
        description="Whether this is a luthier-specific modality"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMOperationModality":
        """
        Enforce 7S invariants:
        - executable_modality must be False
        - machine_output_allowed must be False
        """
        if self.executable_modality:
            raise ValueError(
                "7S invariant violation: executable_modality must be False — "
                "7S modalities are cognition only"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False — "
                "7S does not allow machine output"
            )

        return self


CAM_OPERATION_MODALITY_REGISTRY: Dict[str, CAMOperationModality] = {
    "router_profile": CAMOperationModality(
        modality_id="router_profile",
        display_name="Router Profile",
        description="CNC router profile/contour cutting operations",
        cutter_family="router",
        requires_human_review=True,
        safety_warnings=[
            "Verify cutter diameter and offset direction",
            "Confirm safe Z clearance for clamps/fixtures",
            "Check spindle speed and feed rate for material",
        ],
        typical_operations=["profile_outside", "profile_inside", "slot"],
    ),
    "router_pocket": CAMOperationModality(
        modality_id="router_pocket",
        display_name="Router Pocket",
        description="CNC router pocket clearing operations",
        cutter_family="router",
        requires_human_review=True,
        safety_warnings=[
            "Verify stepover percentage for cutter diameter",
            "Confirm depth per pass for material hardness",
            "Check for adequate chip evacuation",
        ],
        typical_operations=["pocket", "adaptive_pocket", "facing"],
    ),
    "laser_vector": CAMOperationModality(
        modality_id="laser_vector",
        display_name="Laser Vector",
        description="Laser vector cutting/engraving operations",
        cutter_family="laser",
        requires_human_review=True,
        safety_warnings=[
            "Verify laser power for material thickness",
            "Confirm adequate ventilation for fumes",
            "Check fire suppression availability",
        ],
        typical_operations=["laser_cut", "laser_engrave", "laser_score"],
    ),
    "laser_raster": CAMOperationModality(
        modality_id="laser_raster",
        display_name="Laser Raster",
        description="Laser raster fill/engraving operations",
        cutter_family="laser",
        requires_human_review=True,
        safety_warnings=[
            "Verify line spacing for desired resolution",
            "Confirm power scaling for gradient effects",
            "Check for material warping at high power",
        ],
        typical_operations=["laser_raster_fill", "laser_photo_engrave"],
    ),
    "plasma_profile": CAMOperationModality(
        modality_id="plasma_profile",
        display_name="Plasma Profile",
        description="Plasma cutting profile operations",
        cutter_family="plasma",
        requires_human_review=True,
        safety_warnings=[
            "Verify pierce delay for material thickness",
            "Confirm IHS (Initial Height Sensing) configuration",
            "Check consumable condition before cut",
            "Verify adequate ventilation for metal fumes",
        ],
        typical_operations=["plasma_cut_outside", "plasma_cut_inside"],
    ),
    "drag_knife_profile": CAMOperationModality(
        modality_id="drag_knife_profile",
        display_name="Drag Knife Profile",
        description="Drag knife cutting for vinyl, paper, thin materials",
        cutter_family="drag_knife",
        requires_human_review=True,
        safety_warnings=[
            "Verify blade offset for material thickness",
            "Confirm Z pressure for clean cuts",
            "Check blade sharpness",
        ],
        typical_operations=["vinyl_cut", "paper_cut", "decal_cut"],
    ),
    "pen_plotter_profile": CAMOperationModality(
        modality_id="pen_plotter_profile",
        display_name="Pen Plotter",
        description="Pen/marker plotting operations",
        cutter_family="pen_plotter",
        requires_human_review=True,
        safety_warnings=[
            "Verify pen tip clearance",
            "Confirm servo timing for pen up/down",
        ],
        typical_operations=["pen_draw", "marker_plot"],
    ),
    "luthier_rosette_strategy": CAMOperationModality(
        modality_id="luthier_rosette_strategy",
        display_name="Rosette Strategy",
        description="Luthier rosette inlay manufacturing strategy",
        cutter_family="luthier_strategy",
        requires_human_review=True,
        luthier_specific=True,
        safety_warnings=[
            "Verify rosette diameter against soundhole opening",
            "Confirm top thickness at rosette location",
            "Check bracing keepout zones",
            "Verify inlay depth for veneer thickness",
        ],
        typical_operations=["rosette_channel", "rosette_inlay"],
    ),
    "luthier_binding_channel_strategy": CAMOperationModality(
        modality_id="luthier_binding_channel_strategy",
        display_name="Binding Channel Strategy",
        description="Luthier binding channel routing strategy",
        cutter_family="luthier_strategy",
        requires_human_review=True,
        luthier_specific=True,
        safety_warnings=[
            "Verify binding width and depth dimensions",
            "Confirm bearing-guided cutter clearance",
            "Check for grain tearout risk at corners",
            "Verify purfling channel depth if applicable",
        ],
        typical_operations=["binding_channel", "purfling_channel"],
    ),
    "luthier_neck_profile_strategy": CAMOperationModality(
        modality_id="luthier_neck_profile_strategy",
        display_name="Neck Profile Strategy",
        description="Luthier neck carving and profiling strategy",
        cutter_family="luthier_strategy",
        requires_human_review=True,
        luthier_specific=True,
        safety_warnings=[
            "Verify truss rod channel clearance",
            "Confirm neck taper measurements",
            "Check fretboard overhang allowance",
            "Verify headstock transition geometry",
        ],
        typical_operations=["neck_profile", "neck_carve", "heel_carve"],
    ),
    "luthier_fret_slotting_strategy": CAMOperationModality(
        modality_id="luthier_fret_slotting_strategy",
        display_name="Fret Slotting Strategy",
        description="Luthier fret slot cutting strategy",
        cutter_family="luthier_strategy",
        requires_human_review=True,
        luthier_specific=True,
        safety_warnings=[
            "Verify fret spacing calculation and scale length",
            "Confirm slot width for fret tang",
            "Check slot depth for fretboard thickness",
            "Verify compensation if applicable",
        ],
        typical_operations=["fret_slot", "fret_slot_multiscale"],
    ),
    "luthier_fixture_setup": CAMOperationModality(
        modality_id="luthier_fixture_setup",
        display_name="Fixture Setup",
        description="Luthier workholding and fixture setup",
        cutter_family="fixture_setup",
        requires_human_review=True,
        luthier_specific=True,
        safety_warnings=[
            "Verify fixture clearance for tool paths",
            "Confirm workpiece registration points",
            "Check clamp locations against cut geometry",
        ],
        typical_operations=["fixture_setup", "workholding_plan"],
    ),
    "inspection_pass": CAMOperationModality(
        modality_id="inspection_pass",
        display_name="Inspection Pass",
        description="Non-cutting inspection and verification pass",
        cutter_family="inspection",
        requires_human_review=True,
        safety_warnings=[
            "Verify safe Z height for inspection traverse",
            "Confirm probe/sensor configuration if applicable",
        ],
        typical_operations=["dry_run", "inspection", "probe_cycle"],
    ),
}


CAM_OPERATION_MODALITY_INDEX: Dict[str, CAMOperationModality] = {}


def _initialize_modality_index() -> None:
    """Initialize the modality index from the registry."""
    for modality_id, modality in CAM_OPERATION_MODALITY_REGISTRY.items():
        CAM_OPERATION_MODALITY_INDEX[modality_id] = modality


_initialize_modality_index()


def get_operation_modality(modality_id: str) -> Optional[CAMOperationModality]:
    """Get a modality by ID."""
    return CAM_OPERATION_MODALITY_INDEX.get(modality_id)


def list_operation_modalities() -> List[CAMOperationModality]:
    """List all registered modalities."""
    return list(CAM_OPERATION_MODALITY_INDEX.values())


def list_modalities_by_cutter_family(
    cutter_family: CutterFamily,
) -> List[CAMOperationModality]:
    """List modalities by cutter family."""
    return [
        m for m in CAM_OPERATION_MODALITY_INDEX.values()
        if m.cutter_family == cutter_family
    ]


def list_luthier_modalities() -> List[CAMOperationModality]:
    """List luthier-specific modalities."""
    return [
        m for m in CAM_OPERATION_MODALITY_INDEX.values()
        if m.luthier_specific
    ]


def classify_modality_for_operation(
    operation_name: str,
    hints: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Attempt to classify an operation name to a modality ID.

    This is a best-effort heuristic. Returns None if no match found.

    Args:
        operation_name: Operation name to classify
        hints: Optional hints (e.g., cutter_family, material)

    Returns: modality_id or None
    """
    operation_lower = operation_name.lower()

    for modality in CAM_OPERATION_MODALITY_INDEX.values():
        for typical_op in modality.typical_operations:
            if typical_op.lower() in operation_lower or operation_lower in typical_op.lower():
                return modality.modality_id

    if hints:
        cutter_hint = hints.get("cutter_family")
        if cutter_hint:
            matching = list_modalities_by_cutter_family(cutter_hint)
            if matching:
                return matching[0].modality_id

    return None


def get_safety_warnings_for_modality(modality_id: str) -> List[str]:
    """Get safety warnings for a modality."""
    modality = get_operation_modality(modality_id)
    if modality:
        return modality.safety_warnings.copy()
    return []


def register_custom_modality(modality: CAMOperationModality) -> None:
    """
    Register a custom modality.

    Custom modalities must still satisfy 7S invariants.
    """
    CAM_OPERATION_MODALITY_INDEX[modality.modality_id] = modality
