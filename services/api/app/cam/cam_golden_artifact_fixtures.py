"""
CAM Golden Artifact Fixtures

CAM Dev Order 7S: Non-executable golden fixture registry.

Provides:
  - Golden fixture model (reference workholding configurations)
  - Fixture library with luthier-specific setups
  - Fixture compatibility evaluation
  - Material clearance calculations

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - generates_motion always False

Salvaged pattern:
  OpenBuilds-CAM fixture/workholding workflow concept — configurable
  workholding with clearance verification. Implementation is repo-native;
  no OpenBuilds code imported.

Golden fixtures are reference configurations for common luthier workholding
scenarios. They are NOT machine-executable — they inform strategy selection
and provide clearance zone data for envelope validation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


FixtureType = Literal[
    "vacuum_table",
    "side_clamp",
    "corner_clamp",
    "toggle_clamp",
    "t_slot",
    "dedicated_jig",
    "double_sided_tape",
    "wax_chuck",
    "combination",
]

WorkpieceShape = Literal[
    "body_blank",
    "neck_blank",
    "fretboard_blank",
    "headstock_overlay",
    "binding_strip",
    "rosette_blank",
    "bridge_blank",
    "nut_blank",
    "saddle_blank",
    "inlay_blank",
    "rectangular",
    "irregular",
]


class ClearanceZone(BaseModel):
    """
    Clearance zone definition for fixture keepouts.

    All dimensions in millimeters.
    """

    zone_id: str = Field(
        default_factory=lambda: f"zone-{uuid4().hex[:6]}",
        description="Unique zone identifier"
    )
    zone_type: Literal["clamp", "screw", "vacuum_port", "registration", "custom"] = Field(
        ..., description="Type of clearance zone"
    )

    min_x_mm: float = Field(..., description="Minimum X (mm)")
    max_x_mm: float = Field(..., description="Maximum X (mm)")
    min_y_mm: float = Field(..., description="Minimum Y (mm)")
    max_y_mm: float = Field(..., description="Maximum Y (mm)")
    height_mm: float = Field(
        default=50.0,
        description="Height above workpiece (mm)"
    )

    description: str = Field(default="", description="Zone description")

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within this clearance zone."""
        return (
            self.min_x_mm <= x <= self.max_x_mm and
            self.min_y_mm <= y <= self.max_y_mm
        )

    @property
    def area_mm2(self) -> float:
        """Zone area in square millimeters."""
        return (self.max_x_mm - self.min_x_mm) * (self.max_y_mm - self.min_y_mm)


class FixtureCompatibilityHints(BaseModel):
    """
    Compatibility hints for fixture selection.
    """

    recommended_for: List[WorkpieceShape] = Field(
        default_factory=list,
        description="Workpiece shapes this fixture is recommended for"
    )
    not_recommended_for: List[WorkpieceShape] = Field(
        default_factory=list,
        description="Workpiece shapes to avoid with this fixture"
    )
    requires_flat_bottom: bool = Field(
        default=False,
        description="Whether workpiece must have flat bottom"
    )
    minimum_thickness_mm: Optional[float] = Field(
        default=None,
        description="Minimum workpiece thickness (mm)"
    )
    maximum_thickness_mm: Optional[float] = Field(
        default=None,
        description="Maximum workpiece thickness (mm)"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Additional compatibility notes"
    )


class CAMGoldenFixture(BaseModel):
    """
    Golden fixture artifact for reference workholding configurations.

    Golden fixtures are reference configurations, NOT executable machine
    instructions. They inform strategy selection and provide clearance
    data for envelope validation.

    7S invariants (model-enforced):
      - execution_authorized always False
      - machine_output_allowed always False
      - generates_motion always False
    """

    fixture_id: str = Field(
        default_factory=lambda: f"fixture-{uuid4().hex[:10]}",
        description="Unique fixture identifier"
    )
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Fixture description")

    fixture_type: FixtureType = Field(..., description="Primary fixture type")
    secondary_types: List[FixtureType] = Field(
        default_factory=list,
        description="Secondary fixture types if combination"
    )

    clearance_zones: List[ClearanceZone] = Field(
        default_factory=list,
        description="Clearance zones for this fixture"
    )

    safe_z_mm: float = Field(
        default=25.0,
        description="Safe Z height above workpiece (mm)"
    )
    rapid_z_mm: float = Field(
        default=10.0,
        description="Rapid Z height for moves (mm)"
    )

    workpiece_origin: Literal["lower_left", "center", "custom"] = Field(
        default="lower_left",
        description="Workpiece origin convention"
    )

    compatibility: FixtureCompatibilityHints = Field(
        default_factory=FixtureCompatibilityHints,
        description="Compatibility hints"
    )

    setup_notes: List[str] = Field(
        default_factory=list,
        description="Human setup notes"
    )
    safety_warnings: List[str] = Field(
        default_factory=list,
        description="Safety warnings"
    )

    luthier_specific: bool = Field(
        default=False,
        description="Whether this is a luthier-specific fixture"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7S does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )
    generates_motion: bool = Field(
        default=False,
        description="Always False — fixtures do not generate motion"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    deterministic_hash: str = Field(
        default="",
        description="Deterministic hash of fixture definition"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMGoldenFixture":
        """
        Enforce 7S invariants:
        - execution_authorized must be False
        - machine_output_allowed must be False
        - generates_motion must be False
        """
        if self.execution_authorized:
            raise ValueError(
                "7S invariant violation: execution_authorized must be False — "
                "7S does not authorize execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False — "
                "7S does not allow machine output"
            )

        if self.generates_motion:
            raise ValueError(
                "7S invariant violation: generates_motion must be False — "
                "golden fixtures do not generate motion commands"
            )

        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of fixture definition."""
        hash_input = {
            "fixture_id": self.fixture_id,
            "display_name": self.display_name,
            "fixture_type": self.fixture_type,
            "clearance_zones": [
                {
                    "zone_type": z.zone_type,
                    "min_x": z.min_x_mm,
                    "max_x": z.max_x_mm,
                    "min_y": z.min_y_mm,
                    "max_y": z.max_y_mm,
                }
                for z in self.clearance_zones
            ],
            "safe_z_mm": self.safe_z_mm,
            "rapid_z_mm": self.rapid_z_mm,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def check_point_clearance(self, x: float, y: float) -> List[ClearanceZone]:
        """
        Check which clearance zones contain a point.

        Args:
            x: X coordinate (mm)
            y: Y coordinate (mm)

        Returns: List of clearance zones containing the point
        """
        return [z for z in self.clearance_zones if z.contains_point(x, y)]

    def total_clearance_area_mm2(self) -> float:
        """Calculate total clearance zone area (may overlap)."""
        return sum(z.area_mm2 for z in self.clearance_zones)


GOLDEN_FIXTURE_REGISTRY: Dict[str, CAMGoldenFixture] = {
    "luthier_body_vacuum": CAMGoldenFixture(
        fixture_id="luthier_body_vacuum",
        display_name="Luthier Body Vacuum Table",
        description="Vacuum table fixture for guitar body blanks",
        fixture_type="vacuum_table",
        safe_z_mm=30.0,
        rapid_z_mm=15.0,
        workpiece_origin="center",
        luthier_specific=True,
        compatibility=FixtureCompatibilityHints(
            recommended_for=["body_blank", "headstock_overlay"],
            not_recommended_for=["neck_blank", "binding_strip"],
            requires_flat_bottom=True,
            minimum_thickness_mm=15.0,
            notes=["Ensure gasket seal around workpiece perimeter"],
        ),
        setup_notes=[
            "Verify vacuum pump is running before starting",
            "Check seal around workpiece edges",
            "Confirm spoilboard is flat",
        ],
        safety_warnings=[
            "Loss of vacuum during cut may release workpiece",
            "Do not exceed vacuum pump duty cycle",
        ],
    ),
    "luthier_neck_side_clamp": CAMGoldenFixture(
        fixture_id="luthier_neck_side_clamp",
        display_name="Luthier Neck Side Clamps",
        description="Side clamp fixture for neck blank profiling",
        fixture_type="side_clamp",
        safe_z_mm=25.0,
        rapid_z_mm=10.0,
        workpiece_origin="lower_left",
        luthier_specific=True,
        clearance_zones=[
            ClearanceZone(
                zone_type="clamp",
                min_x_mm=-30.0,
                max_x_mm=0.0,
                min_y_mm=0.0,
                max_y_mm=750.0,
                height_mm=40.0,
                description="Left side clamp zone",
            ),
            ClearanceZone(
                zone_type="clamp",
                min_x_mm=100.0,
                max_x_mm=130.0,
                min_y_mm=0.0,
                max_y_mm=750.0,
                height_mm=40.0,
                description="Right side clamp zone",
            ),
        ],
        compatibility=FixtureCompatibilityHints(
            recommended_for=["neck_blank", "fretboard_blank"],
            not_recommended_for=["body_blank", "irregular"],
            minimum_thickness_mm=20.0,
            maximum_thickness_mm=50.0,
            notes=["Side pressure must not deflect thin stock"],
        ),
        setup_notes=[
            "Apply even clamping pressure on both sides",
            "Verify workpiece is parallel to Y axis",
            "Check that clamps clear tool path",
        ],
        safety_warnings=[
            "Excessive side pressure may bow thin stock",
            "Verify clamp height clears tool",
        ],
    ),
    "luthier_fretboard_tape": CAMGoldenFixture(
        fixture_id="luthier_fretboard_tape",
        display_name="Luthier Fretboard Tape Hold",
        description="Double-sided tape fixture for fretboard slotting",
        fixture_type="double_sided_tape",
        safe_z_mm=20.0,
        rapid_z_mm=8.0,
        workpiece_origin="lower_left",
        luthier_specific=True,
        compatibility=FixtureCompatibilityHints(
            recommended_for=["fretboard_blank", "binding_strip", "nut_blank"],
            not_recommended_for=["body_blank", "neck_blank"],
            requires_flat_bottom=True,
            minimum_thickness_mm=5.0,
            maximum_thickness_mm=15.0,
            notes=["Clean surfaces for good tape adhesion"],
        ),
        setup_notes=[
            "Clean spoilboard and workpiece bottom with alcohol",
            "Apply tape in strips, not patches",
            "Press firmly to ensure adhesion",
        ],
        safety_warnings=[
            "Aggressive cuts may release workpiece from tape",
            "Keep cutting forces low",
            "Do not attempt full-depth cuts",
        ],
    ),
    "luthier_rosette_jig": CAMGoldenFixture(
        fixture_id="luthier_rosette_jig",
        display_name="Luthier Rosette Cutting Jig",
        description="Dedicated jig for rosette channel routing on guitar tops",
        fixture_type="dedicated_jig",
        safe_z_mm=20.0,
        rapid_z_mm=8.0,
        workpiece_origin="center",
        luthier_specific=True,
        clearance_zones=[
            ClearanceZone(
                zone_type="registration",
                min_x_mm=-200.0,
                max_x_mm=-180.0,
                min_y_mm=-10.0,
                max_y_mm=10.0,
                height_mm=15.0,
                description="Registration pin zone",
            ),
        ],
        compatibility=FixtureCompatibilityHints(
            recommended_for=["rosette_blank", "body_blank"],
            requires_flat_bottom=False,
            minimum_thickness_mm=2.0,
            maximum_thickness_mm=5.0,
            notes=["Top must be registered to soundhole center"],
        ),
        setup_notes=[
            "Locate soundhole center precisely",
            "Verify top is seated flat in jig",
            "Check registration pins are engaged",
        ],
        safety_warnings=[
            "Verify bit depth before cutting",
            "Do not exceed top thickness",
        ],
    ),
    "generic_corner_clamp": CAMGoldenFixture(
        fixture_id="generic_corner_clamp",
        display_name="Generic Corner Clamps",
        description="Corner clamp fixture for rectangular blanks",
        fixture_type="corner_clamp",
        safe_z_mm=25.0,
        rapid_z_mm=12.0,
        workpiece_origin="lower_left",
        luthier_specific=False,
        clearance_zones=[
            ClearanceZone(
                zone_type="clamp",
                min_x_mm=-25.0,
                max_x_mm=0.0,
                min_y_mm=-25.0,
                max_y_mm=0.0,
                height_mm=35.0,
                description="Lower-left corner clamp",
            ),
            ClearanceZone(
                zone_type="clamp",
                min_x_mm=-25.0,
                max_x_mm=0.0,
                min_y_mm=300.0,
                max_y_mm=325.0,
                height_mm=35.0,
                description="Upper-left corner clamp",
            ),
        ],
        compatibility=FixtureCompatibilityHints(
            recommended_for=["rectangular", "bridge_blank", "saddle_blank"],
            not_recommended_for=["irregular", "body_blank"],
            minimum_thickness_mm=10.0,
            notes=["Workpiece must have square corners"],
        ),
        setup_notes=[
            "Verify corners are square",
            "Apply even pressure at all corners",
        ],
        safety_warnings=[
            "Corner clamps may obstruct tool paths near edges",
        ],
    ),
    "generic_t_slot": CAMGoldenFixture(
        fixture_id="generic_t_slot",
        display_name="Generic T-Slot Table",
        description="T-slot table with toggle clamps",
        fixture_type="t_slot",
        secondary_types=["toggle_clamp"],
        safe_z_mm=30.0,
        rapid_z_mm=15.0,
        workpiece_origin="lower_left",
        luthier_specific=False,
        compatibility=FixtureCompatibilityHints(
            recommended_for=["rectangular", "body_blank", "neck_blank"],
            minimum_thickness_mm=15.0,
            notes=["Flexible clamp positioning via T-slots"],
        ),
        setup_notes=[
            "Position clamps to avoid tool paths",
            "Verify clamp bolts are tight",
            "Check clamp height clearance",
        ],
        safety_warnings=[
            "Mark clamp locations before cutting",
            "Verify safe Z clears all clamps",
        ],
    ),
}


GOLDEN_FIXTURE_INDEX: Dict[str, CAMGoldenFixture] = {}


def _initialize_fixture_index() -> None:
    """Initialize fixture index from registry."""
    for fixture_id, fixture in GOLDEN_FIXTURE_REGISTRY.items():
        fixture.deterministic_hash = fixture.compute_hash()
        GOLDEN_FIXTURE_INDEX[fixture_id] = fixture


_initialize_fixture_index()


def get_golden_fixture(fixture_id: str) -> Optional[CAMGoldenFixture]:
    """Get a golden fixture by ID."""
    return GOLDEN_FIXTURE_INDEX.get(fixture_id)


def list_golden_fixtures() -> List[CAMGoldenFixture]:
    """List all golden fixtures."""
    return list(GOLDEN_FIXTURE_INDEX.values())


def list_luthier_fixtures() -> List[CAMGoldenFixture]:
    """List luthier-specific fixtures."""
    return [f for f in GOLDEN_FIXTURE_INDEX.values() if f.luthier_specific]


def list_fixtures_by_type(fixture_type: FixtureType) -> List[CAMGoldenFixture]:
    """List fixtures by type."""
    return [
        f for f in GOLDEN_FIXTURE_INDEX.values()
        if f.fixture_type == fixture_type or fixture_type in f.secondary_types
    ]


def find_compatible_fixtures(
    workpiece_shape: WorkpieceShape,
    thickness_mm: Optional[float] = None,
    requires_flat_bottom: bool = False,
) -> List[CAMGoldenFixture]:
    """
    Find fixtures compatible with a workpiece.

    Args:
        workpiece_shape: Shape of the workpiece
        thickness_mm: Workpiece thickness (mm)
        requires_flat_bottom: Whether workpiece has flat bottom

    Returns: List of compatible fixtures, sorted by recommendation
    """
    compatible: List[CAMGoldenFixture] = []

    for fixture in GOLDEN_FIXTURE_INDEX.values():
        compat = fixture.compatibility

        if workpiece_shape in compat.not_recommended_for:
            continue

        if compat.requires_flat_bottom and not requires_flat_bottom:
            continue

        if thickness_mm is not None:
            if compat.minimum_thickness_mm and thickness_mm < compat.minimum_thickness_mm:
                continue
            if compat.maximum_thickness_mm and thickness_mm > compat.maximum_thickness_mm:
                continue

        compatible.append(fixture)

    recommended = [
        f for f in compatible
        if workpiece_shape in f.compatibility.recommended_for
    ]
    others = [
        f for f in compatible
        if workpiece_shape not in f.compatibility.recommended_for
    ]

    return recommended + others


def register_custom_fixture(fixture: CAMGoldenFixture) -> None:
    """
    Register a custom golden fixture.

    Custom fixtures must satisfy 7S invariants (enforced by model).
    """
    fixture.deterministic_hash = fixture.compute_hash()
    GOLDEN_FIXTURE_INDEX[fixture.fixture_id] = fixture


def evaluate_fixture_clearance(
    fixture_id: str,
    tool_path_points: List[tuple[float, float]],
) -> Dict[str, Any]:
    """
    Evaluate tool path points against fixture clearance zones.

    Args:
        fixture_id: Fixture to evaluate against
        tool_path_points: List of (x, y) points from tool path

    Returns: Evaluation result with violations
    """
    fixture = GOLDEN_FIXTURE_INDEX.get(fixture_id)
    if not fixture:
        return {
            "fixture_found": False,
            "error": f"Fixture '{fixture_id}' not found",
        }

    violations: List[Dict[str, Any]] = []

    for i, (x, y) in enumerate(tool_path_points):
        conflicting_zones = fixture.check_point_clearance(x, y)
        if conflicting_zones:
            violations.append({
                "point_index": i,
                "x": x,
                "y": y,
                "zones": [z.zone_id for z in conflicting_zones],
            })

    return {
        "fixture_found": True,
        "fixture_id": fixture_id,
        "points_checked": len(tool_path_points),
        "violations_found": len(violations),
        "violations": violations,
        "clearance_ok": len(violations) == 0,
    }


def clear_fixture_index() -> None:
    """Clear fixture index (for testing)."""
    GOLDEN_FIXTURE_INDEX.clear()
