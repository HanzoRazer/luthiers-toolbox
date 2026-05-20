"""
Luthier Manufacturing Strategy

CAM Dev Order 7S: Non-executable manufacturing cognition output.

Provides:
  - Strategy hints for luthier workflows
  - Operation sequencing guidance
  - Fixture assumptions
  - Topology warnings
  - Review-oriented cognition artifacts

7S invariants:
  - executable_payload_present always False
  - execution_authorized always False
  - machine_output_allowed always False

This module generates strategy hints, NOT executable toolpaths.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


StrategyFamily = Literal[
    "rosette",
    "binding_channel",
    "neck_profile",
    "fret_slotting",
    "bridge_location",
    "body_outline",
    "fixture_setup",
    "inspection",
    "soundhole",
    "headstock",
    "bracing",
]

ReviewStatus = Literal[
    "draft",
    "pending_review",
    "approved_for_export_review",
    "rejected",
    "deferred",
]


class LuthierManufacturingStrategy(BaseModel):
    """
    Non-executable manufacturing strategy artifact.

    Contains cognition outputs:
      - Operation sequencing hints
      - Fixture assumptions
      - Keepout notes
      - Topology warnings
      - Tool assumptions
      - Review notes

    Does NOT contain:
      - Executable toolpaths
      - G-code
      - Machine commands
    """

    strategy_id: str = Field(
        default_factory=lambda: f"strategy-{uuid4().hex[:12]}",
        description="Unique strategy identifier"
    )

    operation_family: StrategyFamily = Field(
        ..., description="Strategy operation family"
    )
    modality_id: str = Field(
        default="", description="Associated modality ID from 7S vocabulary"
    )

    display_name: str = Field(default="", description="Human-readable name")
    description: str = Field(default="", description="Strategy description")

    geometry_reference_id: Optional[str] = Field(
        default=None, description="Reference to source geometry"
    )
    export_object_id: Optional[str] = Field(
        default=None, description="Reference to export object"
    )
    translation_artifact_id: Optional[str] = Field(
        default=None, description="Reference to translation artifact"
    )

    operation_sequence: List[str] = Field(
        default_factory=list,
        description="Recommended operation sequence (hints only)"
    )
    fixture_assumptions: List[str] = Field(
        default_factory=list,
        description="Fixture and workholding assumptions"
    )
    keepout_notes: List[str] = Field(
        default_factory=list,
        description="Areas to avoid or treat carefully"
    )
    topology_warnings: List[str] = Field(
        default_factory=list,
        description="Topology-related warnings"
    )
    tool_assumptions: List[str] = Field(
        default_factory=list,
        description="Tool selection assumptions"
    )
    review_notes: List[str] = Field(
        default_factory=list,
        description="Notes for human reviewer"
    )
    material_notes: List[str] = Field(
        default_factory=list,
        description="Material-specific considerations"
    )

    review_status: ReviewStatus = Field(
        default="draft",
        description="Strategy review status"
    )

    executable_payload_present: bool = Field(
        default=False,
        description="Always False — strategies are cognition only"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7S does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )
    generates_gcode: bool = Field(
        default=False,
        description="Always False — 7S does not generate G-code"
    )

    deterministic_strategy_hash: str = Field(
        default="",
        description="Deterministic hash of strategy content"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Strategy creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "LuthierManufacturingStrategy":
        """Enforce 7S invariants."""
        if self.executable_payload_present:
            raise ValueError(
                "7S invariant violation: executable_payload_present must be False"
            )
        if self.execution_authorized:
            raise ValueError(
                "7S invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False"
            )
        if self.generates_gcode:
            raise ValueError(
                "7S invariant violation: generates_gcode must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of strategy content."""
        hash_input = {
            "operation_family": self.operation_family,
            "modality_id": self.modality_id,
            "geometry_reference_id": self.geometry_reference_id,
            "export_object_id": self.export_object_id,
            "operation_sequence": self.operation_sequence,
            "fixture_assumptions": sorted(self.fixture_assumptions),
            "keepout_notes": sorted(self.keepout_notes),
            "topology_warnings": sorted(self.topology_warnings),
            "tool_assumptions": sorted(self.tool_assumptions),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


LUTHIER_MANUFACTURING_STRATEGY_INDEX: Dict[str, LuthierManufacturingStrategy] = {}


STRATEGY_FAMILY_HINTS: Dict[StrategyFamily, Dict[str, List[str]]] = {
    "rosette": {
        "operation_sequence": [
            "1. Verify rosette diameter matches soundhole specification",
            "2. Mark center point on top",
            "3. Route rosette channel to specified depth",
            "4. Test fit rosette ring",
            "5. Apply glue and install rosette",
            "6. Level rosette flush with top surface",
        ],
        "fixture_assumptions": [
            "Top plate secured flat on spoilboard",
            "Center point accurately marked and punched",
            "Adequate clamping away from rosette area",
        ],
        "keepout_notes": [
            "Avoid bracing locations when routing",
            "Do not route deeper than top thickness minus 1mm",
            "Keep router path clear of soundhole cutout line",
        ],
        "topology_warnings": [
            "Verify rosette outer diameter does not exceed soundhole diameter",
            "Check for grain runout that may cause tearout",
            "Confirm top thickness at rosette location",
        ],
        "tool_assumptions": [
            "Use sharp straight bit or rosette cutter",
            "Bit diameter should match rosette channel width",
            "Consider climb vs conventional cut for grain direction",
        ],
        "review_notes": [
            "Confirm rosette design matches instrument specification",
            "Verify material compatibility (wood-on-wood vs. shell inlay)",
            "Check depth tolerance for flush finish",
        ],
    },
    "binding_channel": {
        "operation_sequence": [
            "1. Verify binding dimensions (width x depth)",
            "2. Set router bit depth for binding thickness",
            "3. Route channel around perimeter",
            "4. Test fit binding strip",
            "5. Address any tight spots or gaps",
            "6. Prepare for binding installation",
        ],
        "fixture_assumptions": [
            "Body/top secured in binding routing fixture",
            "Bearing-guided cutter follows body edge",
            "Adequate clearance for router base",
        ],
        "keepout_notes": [
            "Avoid neck pocket area",
            "Watch for waist area where curvature is tight",
            "Be careful at cutaway transitions if present",
        ],
        "topology_warnings": [
            "Check for grain direction changes around curves",
            "Verify consistent edge thickness around perimeter",
            "Watch for end-grain tearout at cutaway",
        ],
        "tool_assumptions": [
            "Bearing-guided rabbeting bit",
            "Bit depth matches binding + purfling if applicable",
            "Sharp cutter essential for clean shoulder",
        ],
        "review_notes": [
            "Confirm binding width matches design specification",
            "Verify purfling channel depth if dual-channel",
            "Check corner miter approach",
        ],
    },
    "neck_profile": {
        "operation_sequence": [
            "1. Rough neck blank to approximate dimensions",
            "2. Cut neck taper on bandsaw or CNC",
            "3. Route truss rod channel",
            "4. Shape neck profile (carve or CNC)",
            "5. Blend heel transition",
            "6. Final shaping and sanding",
        ],
        "fixture_assumptions": [
            "Neck blank secured in carving fixture",
            "Reference surfaces established (fretboard plane, centerline)",
            "Adequate support for headstock during carving",
        ],
        "keepout_notes": [
            "Truss rod channel must not break through",
            "Maintain material for fretboard overhang",
            "Heel block area requires careful transition",
        ],
        "topology_warnings": [
            "Verify neck taper matches fretboard width",
            "Check headstock angle/scarf joint if applicable",
            "Confirm volute dimensions if included",
        ],
        "tool_assumptions": [
            "Ball nose or bullnose for profile carving",
            "Straight bit for truss rod channel",
            "Appropriate feed rates for wood species",
        ],
        "review_notes": [
            "Confirm neck profile matches target shape",
            "Verify heel fits body pocket",
            "Check headstock thickness for tuner clearance",
        ],
    },
    "fret_slotting": {
        "operation_sequence": [
            "1. Verify scale length and fret positions",
            "2. Set up slotting saw/CNC for correct spacing",
            "3. Cut slots to specified depth",
            "4. Verify slot width matches fret tang",
            "5. Clean slots of debris",
            "6. Test fit sample fret wire",
        ],
        "fixture_assumptions": [
            "Fretboard secured flat and square",
            "Reference edge aligned with cutting path",
            "Adequate hold-down without damaging surface",
        ],
        "keepout_notes": [
            "Do not slot past fretboard edges",
            "Maintain material at nut and last fret positions",
            "Watch for binding channel overlap if bound board",
        ],
        "topology_warnings": [
            "Verify slot depth does not exceed 2/3 fretboard thickness",
            "Check for slot width consistency",
            "Confirm multiscale angles if fan-fret design",
        ],
        "tool_assumptions": [
            "Fret slotting saw (0.023\" typical)",
            "Depth stop or CNC Z control",
            "Clean blade for consistent slot width",
        ],
        "review_notes": [
            "Confirm scale length matches specification",
            "Verify compensation if applied",
            "Check slot positions against calculation",
        ],
    },
    "bridge_location": {
        "operation_sequence": [
            "1. Calculate bridge position from scale length",
            "2. Mark centerline on top",
            "3. Locate bridge footprint",
            "4. Verify saddle position for intonation",
            "5. Mark or route pin holes if applicable",
            "6. Prepare surface for bridge gluing",
        ],
        "fixture_assumptions": [
            "Body top accessible for marking",
            "Centerline accurately established",
            "Saddle compensation determined",
        ],
        "keepout_notes": [
            "Bridge must clear any bracing underneath",
            "X-brace intersection typically under bridge area",
            "Avoid placing pins over brace positions",
        ],
        "topology_warnings": [
            "Verify top is flat in bridge area",
            "Check for adequate gluing surface",
            "Confirm bridge does not extend over binding",
        ],
        "tool_assumptions": [
            "Pin hole drill bit matched to pin size",
            "Flat scraper for surface prep",
            "Marking tools for position layout",
        ],
        "review_notes": [
            "Confirm scale length and compensation",
            "Verify bridge style matches design",
            "Check string spacing at bridge",
        ],
    },
    "body_outline": {
        "operation_sequence": [
            "1. Transfer body template to blank",
            "2. Rough cut outside line on bandsaw",
            "3. Route to final dimension with template",
            "4. Verify dimensions match specification",
            "5. Mark reference points for subsequent operations",
        ],
        "fixture_assumptions": [
            "Template accurately made and verified",
            "Blank secured to template with carpet tape or screws",
            "Router table or flush-trim setup ready",
        ],
        "keepout_notes": [
            "Allow material for binding if applicable",
            "Mark neck pocket location before routing",
            "Identify grain direction for cut direction",
        ],
        "topology_warnings": [
            "Check for voids or defects in blank",
            "Verify blank thickness is adequate",
            "Watch for grain runout that may cause tearout",
        ],
        "tool_assumptions": [
            "Flush-trim or pattern bit",
            "Sharp bit for clean edges",
            "Appropriate feed rate for species",
        ],
        "review_notes": [
            "Confirm body shape matches design",
            "Verify waist, upper bout, lower bout dimensions",
            "Check symmetry across centerline",
        ],
    },
    "fixture_setup": {
        "operation_sequence": [
            "1. Identify workpiece registration points",
            "2. Select appropriate workholding method",
            "3. Verify tool clearance around clamps",
            "4. Set work coordinate system origin",
            "5. Confirm safe Z clearance height",
        ],
        "fixture_assumptions": [
            "Fixture matches workpiece geometry",
            "Registration is repeatable",
            "Clamping force adequate but not excessive",
        ],
        "keepout_notes": [
            "Clamps must not interfere with tool paths",
            "Vacuum if used must maintain seal",
            "Consider chip evacuation paths",
        ],
        "topology_warnings": [
            "Verify workpiece sits flat in fixture",
            "Check for rocking or instability",
            "Confirm fixture does not obscure critical features",
        ],
        "tool_assumptions": [
            "Tools must clear fixture at safe Z",
            "Tool length must reach full depth",
            "Consider tool holder clearance",
        ],
        "review_notes": [
            "Confirm fixture setup before starting cut",
            "Verify work offset is correct",
            "Check emergency stop accessibility",
        ],
    },
    "inspection": {
        "operation_sequence": [
            "1. Visual inspection of workpiece",
            "2. Dimensional verification of critical features",
            "3. Surface quality assessment",
            "4. Documentation of any defects or issues",
            "5. Sign-off for next operation",
        ],
        "fixture_assumptions": [
            "Workpiece accessible for measurement",
            "Measuring tools calibrated",
            "Lighting adequate for visual inspection",
        ],
        "keepout_notes": [
            "Do not modify workpiece during inspection",
            "Handle carefully to avoid damage",
        ],
        "topology_warnings": [
            "Note any deviations from specification",
            "Document surface defects with location",
        ],
        "tool_assumptions": [
            "Calipers, rulers, templates as needed",
            "Go/no-go gauges for critical dimensions",
        ],
        "review_notes": [
            "Record all measurements",
            "Note any concerns for downstream operations",
            "Approve or reject for next step",
        ],
    },
    "soundhole": {
        "operation_sequence": [
            "1. Mark soundhole center on top",
            "2. Verify diameter matches specification",
            "3. Route or cut soundhole opening",
            "4. Verify edge quality and circularity",
            "5. Prepare for rosette installation if applicable",
        ],
        "fixture_assumptions": [
            "Top secured flat",
            "Center point accurately located",
            "Router or circle cutter set to correct radius",
        ],
        "keepout_notes": [
            "Rosette channel must be cut before soundhole",
            "Do not cut into bracing if pre-braced",
        ],
        "topology_warnings": [
            "Verify soundhole position relative to bridge",
            "Check for adequate top material around opening",
        ],
        "tool_assumptions": [
            "Circle cutter, router with trammel, or CNC",
            "Sharp bit for clean edge",
        ],
        "review_notes": [
            "Confirm diameter matches design",
            "Verify position on body centerline",
        ],
    },
    "headstock": {
        "operation_sequence": [
            "1. Layout tuner hole positions",
            "2. Drill tuner holes to specification",
            "3. Route headstock shape if not pre-cut",
            "4. Shape any overlay or veneer",
            "5. Verify tuner fit and spacing",
        ],
        "fixture_assumptions": [
            "Neck/headstock secured for drilling",
            "Drilling angle correct for tuner style",
            "Adequate support under headstock",
        ],
        "keepout_notes": [
            "Tuner holes must not interfere with truss rod",
            "Maintain edge material for binding if applicable",
        ],
        "topology_warnings": [
            "Verify headstock thickness for tuner bushings",
            "Check string angle to nut",
        ],
        "tool_assumptions": [
            "Forstner bits for tuner holes",
            "Reamer for bushing fit if needed",
        ],
        "review_notes": [
            "Confirm tuner layout matches specification",
            "Verify hole positions are symmetric",
        ],
    },
    "bracing": {
        "operation_sequence": [
            "1. Layout brace positions on top/back",
            "2. Prepare braces to rough dimensions",
            "3. Fit braces to plate curvature",
            "4. Glue braces in position",
            "5. Shape braces to final profile",
            "6. Scallop or taper as design requires",
        ],
        "fixture_assumptions": [
            "Go-bar deck or radius dish available",
            "Braces pre-shaped to approximate profile",
            "Adequate clamping pressure",
        ],
        "keepout_notes": [
            "Soundhole area must remain clear",
            "Bridge plate area coordinates with X-brace",
            "Avoid over-thinning at brace ends",
        ],
        "topology_warnings": [
            "Verify grain direction in braces",
            "Check for adequate glue surface",
            "Confirm tap tone after bracing",
        ],
        "tool_assumptions": [
            "Chisels and planes for brace shaping",
            "Finger planes for scalloping",
            "Sanding tools for final profile",
        ],
        "review_notes": [
            "Confirm brace layout matches pattern",
            "Verify structural integrity",
            "Document tap tone response",
        ],
    },
}


def create_manufacturing_strategy(
    operation_family: StrategyFamily,
    title: str = "",
    modality_id: str = "",
    geometry_reference_id: Optional[str] = None,
    export_object_id: Optional[str] = None,
    translation_artifact_id: Optional[str] = None,
    display_name: str = "",
    description: str = "",
    additional_hints: Optional[Dict[str, List[str]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    operation_sequence: Optional[List[str]] = None,
    fixture_assumptions: Optional[List[str]] = None,
    keepout_notes: Optional[List[str]] = None,
) -> LuthierManufacturingStrategy:
    """
    Create a manufacturing strategy with heuristic hints.

    Generates strategy hints based on operation family,
    then allows customization via additional_hints.

    Args:
        operation_family: Strategy operation family
        title: Alias for display_name
        modality_id: Associated modality ID
        geometry_reference_id: Reference to source geometry
        export_object_id: Reference to export object
        translation_artifact_id: Reference to translation artifact
        display_name: Human-readable name (title takes precedence)
        description: Strategy description
        additional_hints: Additional hints to merge
        metadata: Additional metadata
        operation_sequence: Additional operation sequence items
        fixture_assumptions: Additional fixture assumptions
        keepout_notes: Additional keepout notes

    Returns:
        LuthierManufacturingStrategy with computed hash, registered in index
    """
    base_hints = STRATEGY_FAMILY_HINTS.get(operation_family, {})

    op_seq = list(base_hints.get("operation_sequence", []))
    fix_assump = list(base_hints.get("fixture_assumptions", []))
    keep_notes = list(base_hints.get("keepout_notes", []))
    topology_warnings = list(base_hints.get("topology_warnings", []))
    tool_assumptions = list(base_hints.get("tool_assumptions", []))
    review_notes = list(base_hints.get("review_notes", []))
    material_notes: List[str] = []

    if additional_hints:
        op_seq.extend(additional_hints.get("operation_sequence", []))
        fix_assump.extend(additional_hints.get("fixture_assumptions", []))
        keep_notes.extend(additional_hints.get("keepout_notes", []))
        topology_warnings.extend(additional_hints.get("topology_warnings", []))
        tool_assumptions.extend(additional_hints.get("tool_assumptions", []))
        review_notes.extend(additional_hints.get("review_notes", []))
        material_notes.extend(additional_hints.get("material_notes", []))

    if operation_sequence:
        op_seq.extend(operation_sequence)
    if fixture_assumptions:
        fix_assump.extend(fixture_assumptions)
    if keepout_notes:
        keep_notes.extend(keepout_notes)

    resolved_modality_id = modality_id
    if not resolved_modality_id:
        modality_map = {
            "rosette": "luthier_rosette_strategy",
            "binding_channel": "luthier_binding_channel_strategy",
            "neck_profile": "luthier_neck_profile_strategy",
            "fret_slotting": "luthier_fret_slotting_strategy",
            "fixture_setup": "luthier_fixture_setup",
            "inspection": "inspection_pass",
        }
        resolved_modality_id = modality_map.get(operation_family, "")

    resolved_display_name = title or display_name
    if not resolved_display_name:
        resolved_display_name = f"{operation_family.replace('_', ' ').title()} Strategy"

    strategy = LuthierManufacturingStrategy(
        operation_family=operation_family,
        modality_id=resolved_modality_id,
        display_name=resolved_display_name,
        description=description,
        geometry_reference_id=geometry_reference_id,
        export_object_id=export_object_id,
        translation_artifact_id=translation_artifact_id,
        operation_sequence=op_seq,
        fixture_assumptions=fix_assump,
        keepout_notes=keep_notes,
        topology_warnings=topology_warnings,
        tool_assumptions=tool_assumptions,
        review_notes=review_notes,
        material_notes=material_notes,
        review_status="draft",
        metadata=metadata or {"dev_order": "7S"},
    )

    strategy.deterministic_strategy_hash = strategy.compute_hash()

    LUTHIER_MANUFACTURING_STRATEGY_INDEX[strategy.strategy_id] = strategy

    return strategy


def get_manufacturing_strategy(strategy_id: str) -> Optional[LuthierManufacturingStrategy]:
    """Get strategy by ID."""
    return LUTHIER_MANUFACTURING_STRATEGY_INDEX.get(strategy_id)


def list_manufacturing_strategies() -> List[LuthierManufacturingStrategy]:
    """List all strategies."""
    return list(LUTHIER_MANUFACTURING_STRATEGY_INDEX.values())


def list_strategies_by_family(
    operation_family: StrategyFamily,
) -> List[LuthierManufacturingStrategy]:
    """List strategies by operation family."""
    return [
        s for s in LUTHIER_MANUFACTURING_STRATEGY_INDEX.values()
        if s.operation_family == operation_family
    ]


def clear_strategy_index() -> None:
    """Clear strategy index (for testing)."""
    LUTHIER_MANUFACTURING_STRATEGY_INDEX.clear()


def hash_strategy(strategy: LuthierManufacturingStrategy) -> str:
    """Compute hash for a strategy."""
    return strategy.compute_hash()


def list_strategies_by_review_status(
    review_status: ReviewStatus,
) -> List[LuthierManufacturingStrategy]:
    """List strategies by review status."""
    return [
        s for s in LUTHIER_MANUFACTURING_STRATEGY_INDEX.values()
        if s.review_status == review_status
    ]


def update_strategy_review_status(
    strategy_id: str,
    review_status: ReviewStatus,
    review_notes: Optional[str] = None,
) -> Optional[LuthierManufacturingStrategy]:
    """Update strategy review status."""
    strategy = LUTHIER_MANUFACTURING_STRATEGY_INDEX.get(strategy_id)
    if not strategy:
        return None

    strategy.review_status = review_status
    if review_notes:
        strategy.review_notes.append(review_notes)

    return strategy


class StrategyFamilyHint(BaseModel):
    """Strategy hints for an operation family."""

    family: str = Field(..., description="Operation family")
    typical_sequence: List[str] = Field(
        default_factory=list, description="Typical operation sequence"
    )
    common_keepouts: List[str] = Field(
        default_factory=list, description="Common keepout zones"
    )
    fixture_recommendations: List[str] = Field(
        default_factory=list, description="Fixture recommendations"
    )
    tool_recommendations: List[str] = Field(
        default_factory=list, description="Tool recommendations"
    )


def get_family_hints(family: StrategyFamily) -> Optional[StrategyFamilyHint]:
    """Get strategy hints for an operation family."""
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


# Alias for backward compatibility with router
OperationFamily = StrategyFamily
