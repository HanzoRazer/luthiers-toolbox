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
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

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
    """Operation modality vocabulary entry."""

    modality_id: str = Field(..., description="Unique modality identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Modality description")

    cutter_family: CutterFamily = Field(..., description="Cutter family classification")

    executable_modality: bool = Field(
        default=False, description="Always False — 7S modalities are cognition only"
    )
    machine_output_allowed: bool = Field(
        default=False, description="Always False — 7S does not allow machine output"
    )
    requires_human_review: bool = Field(
        default=True, description="Whether operation requires human review"
    )

    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    typical_operations: List[str] = Field(default_factory=list, description="Typical operations")
    luthier_specific: bool = Field(default=False, description="Luthier-specific modality")

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMOperationModality":
        if self.executable_modality:
            raise ValueError("7S invariant violation: executable_modality must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        return self


CAM_OPERATION_MODALITY_REGISTRY: Dict[str, CAMOperationModality] = {
    "router_profile": CAMOperationModality(
        modality_id="router_profile",
        display_name="Router Profile",
        description="CNC router profile/contour cutting operations",
        cutter_family="router",
        safety_warnings=["Verify cutter diameter and offset direction", "Confirm safe Z clearance"],
        typical_operations=["profile_outside", "profile_inside", "slot"],
    ),
    "router_pocket": CAMOperationModality(
        modality_id="router_pocket",
        display_name="Router Pocket",
        description="CNC router pocket clearing operations",
        cutter_family="router",
        safety_warnings=["Verify stepover percentage", "Confirm depth per pass"],
        typical_operations=["pocket", "adaptive_pocket", "facing"],
    ),
    "laser_vector": CAMOperationModality(
        modality_id="laser_vector",
        display_name="Laser Vector",
        description="Laser vector cutting/engraving operations",
        cutter_family="laser",
        safety_warnings=["Verify laser power for material", "Confirm ventilation"],
        typical_operations=["laser_cut", "laser_engrave", "laser_score"],
    ),
    "laser_raster": CAMOperationModality(
        modality_id="laser_raster",
        display_name="Laser Raster",
        description="Laser raster fill/engraving operations",
        cutter_family="laser",
        safety_warnings=["Verify line spacing", "Confirm power scaling"],
        typical_operations=["laser_raster_fill", "laser_photo_engrave"],
    ),
    "plasma_profile": CAMOperationModality(
        modality_id="plasma_profile",
        display_name="Plasma Profile",
        description="Plasma cutting profile operations",
        cutter_family="plasma",
        safety_warnings=["Verify pierce delay", "Confirm IHS configuration"],
        typical_operations=["plasma_cut_outside", "plasma_cut_inside"],
    ),
    "drag_knife_profile": CAMOperationModality(
        modality_id="drag_knife_profile",
        display_name="Drag Knife Profile",
        description="Drag knife cutting for vinyl, paper, thin materials",
        cutter_family="drag_knife",
        safety_warnings=["Verify blade offset", "Confirm Z pressure"],
        typical_operations=["vinyl_cut", "paper_cut", "decal_cut"],
    ),
    "pen_plotter_profile": CAMOperationModality(
        modality_id="pen_plotter_profile",
        display_name="Pen Plotter",
        description="Pen/marker plotting operations",
        cutter_family="pen_plotter",
        safety_warnings=["Verify pen tip clearance"],
        typical_operations=["pen_draw", "marker_plot"],
    ),
    "luthier_rosette_strategy": CAMOperationModality(
        modality_id="luthier_rosette_strategy",
        display_name="Rosette Strategy",
        description="Luthier rosette inlay manufacturing strategy",
        cutter_family="luthier_strategy",
        luthier_specific=True,
        safety_warnings=["Verify rosette diameter", "Confirm top thickness", "Check bracing keepout"],
        typical_operations=["rosette_channel", "rosette_inlay"],
    ),
    "luthier_binding_channel_strategy": CAMOperationModality(
        modality_id="luthier_binding_channel_strategy",
        display_name="Binding Channel Strategy",
        description="Luthier binding channel routing strategy",
        cutter_family="luthier_strategy",
        luthier_specific=True,
        safety_warnings=["Verify binding width and depth", "Confirm bearing-guided cutter clearance"],
        typical_operations=["binding_channel", "purfling_channel"],
    ),
    "luthier_neck_profile_strategy": CAMOperationModality(
        modality_id="luthier_neck_profile_strategy",
        display_name="Neck Profile Strategy",
        description="Luthier neck carving and profiling strategy",
        cutter_family="luthier_strategy",
        luthier_specific=True,
        safety_warnings=["Verify truss rod channel clearance", "Confirm neck taper"],
        typical_operations=["neck_profile", "neck_carve", "heel_carve"],
    ),
    "luthier_fret_slotting_strategy": CAMOperationModality(
        modality_id="luthier_fret_slotting_strategy",
        display_name="Fret Slotting Strategy",
        description="Luthier fret slot cutting strategy",
        cutter_family="luthier_strategy",
        luthier_specific=True,
        safety_warnings=["Verify fret spacing calculation", "Confirm slot width for fret tang"],
        typical_operations=["fret_slot", "fret_slot_multiscale"],
    ),
    "luthier_fixture_setup": CAMOperationModality(
        modality_id="luthier_fixture_setup",
        display_name="Fixture Setup",
        description="Luthier workholding and fixture setup",
        cutter_family="fixture_setup",
        luthier_specific=True,
        safety_warnings=["Verify fixture clearance for tool paths"],
        typical_operations=["fixture_setup", "workholding_plan"],
    ),
    "inspection_pass": CAMOperationModality(
        modality_id="inspection_pass",
        display_name="Inspection Pass",
        description="Non-cutting inspection and verification pass",
        cutter_family="inspection",
        safety_warnings=["Verify safe Z height for inspection traverse"],
        typical_operations=["dry_run", "inspection", "probe_cycle"],
    ),
}

CAM_OPERATION_MODALITY_INDEX: Dict[str, CAMOperationModality] = dict(CAM_OPERATION_MODALITY_REGISTRY)


def get_operation_modality(modality_id: str) -> Optional[CAMOperationModality]:
    return CAM_OPERATION_MODALITY_INDEX.get(modality_id)


def list_operation_modalities() -> List[CAMOperationModality]:
    return list(CAM_OPERATION_MODALITY_INDEX.values())


def list_modalities_by_cutter_family(cutter_family: CutterFamily) -> List[CAMOperationModality]:
    return [m for m in CAM_OPERATION_MODALITY_INDEX.values() if m.cutter_family == cutter_family]


def list_luthier_modalities() -> List[CAMOperationModality]:
    return [m for m in CAM_OPERATION_MODALITY_INDEX.values() if m.luthier_specific]


def classify_modality_for_operation(operation_name: str, hints: Optional[Dict[str, Any]] = None) -> Optional[str]:
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
    modality = get_operation_modality(modality_id)
    return modality.safety_warnings.copy() if modality else []
