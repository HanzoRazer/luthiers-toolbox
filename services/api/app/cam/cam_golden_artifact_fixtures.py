"""
CAM Golden Artifact Fixtures

CAM Dev Order 7S: Non-executable golden fixture registry.

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - generates_motion always False
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


FixtureType = Literal["vacuum_table", "side_clamp", "corner_clamp", "toggle_clamp", "t_slot", "dedicated_jig", "double_sided_tape"]
WorkpieceShape = Literal["body_blank", "neck_blank", "fretboard_blank", "headstock_overlay", "binding_strip", "rosette_blank", "rectangular", "irregular"]


class ClearanceZone(BaseModel):
    """Clearance zone definition for fixture keepouts."""

    zone_id: str = Field(default_factory=lambda: f"zone-{uuid4().hex[:6]}")
    zone_type: Literal["clamp", "screw", "vacuum_port", "registration", "custom"]
    min_x_mm: float
    max_x_mm: float
    min_y_mm: float
    max_y_mm: float
    height_mm: float = 50.0
    description: str = ""

    def contains_point(self, x: float, y: float) -> bool:
        return self.min_x_mm <= x <= self.max_x_mm and self.min_y_mm <= y <= self.max_y_mm


class FixtureCompatibilityHints(BaseModel):
    """Compatibility hints for fixture selection."""

    recommended_for: List[WorkpieceShape] = Field(default_factory=list)
    not_recommended_for: List[WorkpieceShape] = Field(default_factory=list)
    requires_flat_bottom: bool = False
    minimum_thickness_mm: Optional[float] = None
    maximum_thickness_mm: Optional[float] = None
    notes: List[str] = Field(default_factory=list)


class CAMGoldenFixture(BaseModel):
    """Golden fixture artifact for reference workholding configurations."""

    fixture_id: str = Field(default_factory=lambda: f"fixture-{uuid4().hex[:10]}")
    display_name: str
    description: str = ""
    fixture_type: FixtureType
    clearance_zones: List[ClearanceZone] = Field(default_factory=list)
    safe_z_mm: float = 25.0
    rapid_z_mm: float = 10.0
    compatibility: FixtureCompatibilityHints = Field(default_factory=FixtureCompatibilityHints)
    setup_notes: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    luthier_specific: bool = False

    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)
    generates_motion: bool = Field(default=False)

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMGoldenFixture":
        if self.execution_authorized:
            raise ValueError("7S invariant violation: execution_authorized must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        if self.generates_motion:
            raise ValueError("7S invariant violation: generates_motion must be False")
        return self

    def check_point_clearance(self, x: float, y: float) -> List[ClearanceZone]:
        return [z for z in self.clearance_zones if z.contains_point(x, y)]


GOLDEN_FIXTURE_REGISTRY: Dict[str, CAMGoldenFixture] = {
    "luthier_body_vacuum": CAMGoldenFixture(
        fixture_id="luthier_body_vacuum",
        display_name="Luthier Body Vacuum Table",
        fixture_type="vacuum_table",
        luthier_specific=True,
        compatibility=FixtureCompatibilityHints(
            recommended_for=["body_blank", "headstock_overlay"],
            not_recommended_for=["neck_blank", "binding_strip"],
            requires_flat_bottom=True,
            minimum_thickness_mm=15.0,
        ),
    ),
    "luthier_neck_side_clamp": CAMGoldenFixture(
        fixture_id="luthier_neck_side_clamp",
        display_name="Luthier Neck Side Clamps",
        fixture_type="side_clamp",
        luthier_specific=True,
        clearance_zones=[
            ClearanceZone(zone_type="clamp", min_x_mm=-30.0, max_x_mm=0.0, min_y_mm=0.0, max_y_mm=750.0, height_mm=40.0),
            ClearanceZone(zone_type="clamp", min_x_mm=100.0, max_x_mm=130.0, min_y_mm=0.0, max_y_mm=750.0, height_mm=40.0),
        ],
        compatibility=FixtureCompatibilityHints(
            recommended_for=["neck_blank", "fretboard_blank"],
            not_recommended_for=["body_blank", "irregular"],
            minimum_thickness_mm=20.0,
            maximum_thickness_mm=50.0,
        ),
    ),
    "luthier_fretboard_tape": CAMGoldenFixture(
        fixture_id="luthier_fretboard_tape",
        display_name="Luthier Fretboard Tape Hold",
        fixture_type="double_sided_tape",
        luthier_specific=True,
        compatibility=FixtureCompatibilityHints(
            recommended_for=["fretboard_blank", "binding_strip"],
            requires_flat_bottom=True,
            minimum_thickness_mm=5.0,
            maximum_thickness_mm=15.0,
        ),
    ),
    "luthier_rosette_jig": CAMGoldenFixture(
        fixture_id="luthier_rosette_jig",
        display_name="Luthier Rosette Cutting Jig",
        fixture_type="dedicated_jig",
        luthier_specific=True,
        compatibility=FixtureCompatibilityHints(recommended_for=["rosette_blank", "body_blank"]),
    ),
    "generic_corner_clamp": CAMGoldenFixture(
        fixture_id="generic_corner_clamp",
        display_name="Generic Corner Clamps",
        fixture_type="corner_clamp",
        compatibility=FixtureCompatibilityHints(recommended_for=["rectangular"], not_recommended_for=["irregular", "body_blank"]),
    ),
    "generic_t_slot": CAMGoldenFixture(
        fixture_id="generic_t_slot",
        display_name="Generic T-Slot Table",
        fixture_type="t_slot",
        compatibility=FixtureCompatibilityHints(recommended_for=["rectangular", "body_blank", "neck_blank"]),
    ),
}

GOLDEN_FIXTURE_INDEX: Dict[str, CAMGoldenFixture] = dict(GOLDEN_FIXTURE_REGISTRY)


def get_golden_fixture(fixture_id: str) -> Optional[CAMGoldenFixture]:
    return GOLDEN_FIXTURE_INDEX.get(fixture_id)


def list_golden_fixtures() -> List[CAMGoldenFixture]:
    return list(GOLDEN_FIXTURE_INDEX.values())


def list_luthier_fixtures() -> List[CAMGoldenFixture]:
    return [f for f in GOLDEN_FIXTURE_INDEX.values() if f.luthier_specific]


def list_fixtures_by_type(fixture_type: FixtureType) -> List[CAMGoldenFixture]:
    return [f for f in GOLDEN_FIXTURE_INDEX.values() if f.fixture_type == fixture_type]


def find_compatible_fixtures(
    workpiece_shape: WorkpieceShape,
    thickness_mm: Optional[float] = None,
    requires_flat_bottom: bool = False,
) -> List[CAMGoldenFixture]:
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
    recommended = [f for f in compatible if workpiece_shape in f.compatibility.recommended_for]
    others = [f for f in compatible if workpiece_shape not in f.compatibility.recommended_for]
    return recommended + others


def evaluate_fixture_clearance(fixture_id: str, tool_path_points: List[tuple[float, float]]) -> Dict[str, Any]:
    fixture = GOLDEN_FIXTURE_INDEX.get(fixture_id)
    if not fixture:
        return {"fixture_found": False, "error": f"Fixture '{fixture_id}' not found"}
    violations: List[Dict[str, Any]] = []
    for i, (x, y) in enumerate(tool_path_points):
        conflicting_zones = fixture.check_point_clearance(x, y)
        if conflicting_zones:
            violations.append({"point_index": i, "x": x, "y": y, "zones": [z.zone_id for z in conflicting_zones]})
    return {
        "fixture_found": True,
        "fixture_id": fixture_id,
        "points_checked": len(tool_path_points),
        "violations_found": len(violations),
        "violations": violations,
        "clearance_ok": len(violations) == 0,
    }


def clear_fixture_index() -> None:
    GOLDEN_FIXTURE_INDEX.clear()
