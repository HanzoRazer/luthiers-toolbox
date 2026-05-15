"""
Acoustic Semantic Fixture Generator.

Sprint: MRP-5F
Classification: SEMANTIC_ONLY

Generates Export Objects with acoustic cad_semantics for testing
schema validation and translator awareness. These fixtures do NOT
represent runtime-generatable CAD geometry.

Key Rule:
    These are semantic descriptors only. No topology generation.
    STEP translator should classify as UNSUPPORTED_TOPOLOGY_RUNTIME.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.export.body_export_bridge import (
    BodyExportObject,
    Bounds,
    CoordinateSystem,
    ExportExtensions,
    ExportGeometry,
    ExportIntent,
    ExportMetadata,
    ExportSource,
    ExportValidation,
    GeometryEntity,
    ValidationCheck,
)
from app.export.cad_semantics import (
    AcousticSemantics,
    BodyCategory,
    CadSemantics,
    ClosureType,
    ContinuityTarget,
    FlatBodySemantics,
    PlateRelationshipSemantics,
    PlateType,
    RimSemantics,
    RuntimeSupport,
    SideProfileSemantics,
    SideProfileType,
    ThicknessSemantics,
)


# ─── Fixture Manifest ────────────────────────────────────────────────────────


ACOUSTIC_FIXTURE_MANIFEST = {
    "schema_version": "1.0.0",
    "sprint": "MRP-5F",
    "classification": "SEMANTIC_ONLY",
    "runtime_topology": False,
    "fixtures": {
        "dreadnought_semantic": {
            "body_category": "acoustic_flat_top",
            "description": "Dreadnought acoustic guitar semantic fixture",
            "runtime_support": "SEMANTIC_ONLY",
            "has_tapered_sides": True,
            "continuity_target": "G1",
        },
        "jumbo_semantic": {
            "body_category": "acoustic_flat_top",
            "description": "Jumbo acoustic guitar semantic fixture",
            "runtime_support": "SEMANTIC_ONLY",
            "has_tapered_sides": True,
            "continuity_target": "G1",
        },
        "parlor_semantic": {
            "body_category": "acoustic_flat_top",
            "description": "Parlor acoustic guitar semantic fixture",
            "runtime_support": "SEMANTIC_ONLY",
            "has_tapered_sides": False,
            "continuity_target": "G1",
        },
        "hollowbody_semantic": {
            "body_category": "hollow_electric",
            "description": "Hollow electric guitar semantic fixture",
            "runtime_support": "SEMANTIC_ONLY",
            "has_tapered_sides": False,
            "continuity_target": "G0",
        },
    },
}


# ─── Instrument Dimensions ───────────────────────────────────────────────────

# Approximate dimensions for semantic fixtures (mm)
# These are for generating plausible profile outlines, not precision CAD

ACOUSTIC_DIMENSIONS = {
    "dreadnought": {
        "body_width_mm": 395,
        "body_length_mm": 505,
        "upper_bout_mm": 290,
        "waist_mm": 275,
        "lower_bout_mm": 395,
        "butt_depth_mm": 121,
        "shoulder_depth_mm": 105,
        "top_thickness_mm": 2.8,
        "back_thickness_mm": 2.5,
        "back_radius_mm": 7620,  # 25ft standard
    },
    "jumbo": {
        "body_width_mm": 432,
        "body_length_mm": 530,
        "upper_bout_mm": 310,
        "waist_mm": 280,
        "lower_bout_mm": 432,
        "butt_depth_mm": 125,
        "shoulder_depth_mm": 108,
        "top_thickness_mm": 3.0,
        "back_thickness_mm": 2.8,
        "back_radius_mm": 7620,
    },
    "parlor": {
        "body_width_mm": 340,
        "body_length_mm": 440,
        "upper_bout_mm": 245,
        "waist_mm": 210,
        "lower_bout_mm": 340,
        "butt_depth_mm": 100,
        "shoulder_depth_mm": 95,
        "top_thickness_mm": 2.5,
        "back_thickness_mm": 2.3,
        "back_radius_mm": 6096,  # 20ft
    },
    "hollowbody": {
        "body_width_mm": 406,
        "body_length_mm": 483,
        "upper_bout_mm": 280,
        "waist_mm": 260,
        "lower_bout_mm": 406,
        "butt_depth_mm": 57,  # Shallower
        "shoulder_depth_mm": 57,  # Uniform for hollow electric
        "top_thickness_mm": 6.0,  # Laminate
        "back_thickness_mm": 6.0,
        "back_radius_mm": None,  # Flat
    },
}


# ─── Profile Generation ──────────────────────────────────────────────────────


def generate_simplified_body_outline(
    width_mm: float,
    length_mm: float,
    num_points: int = 24,
) -> List[List[float]]:
    """
    Generate a simplified elliptical body outline.

    This is NOT accurate guitar geometry - it's a placeholder for
    semantic fixture testing. Real geometry comes from BOE.

    Args:
        width_mm: Body width.
        length_mm: Body length.
        num_points: Number of points in outline.

    Returns:
        List of [x, y] coordinate pairs forming closed contour.
    """
    import math

    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = (width_mm / 2) * math.cos(angle)
        y = (length_mm / 2) * math.sin(angle)
        points.append([round(x, 3), round(y, 3)])

    # Close the contour
    points.append(points[0].copy())

    return points


# ─── Fixture Generators ──────────────────────────────────────────────────────


def _create_base_export_object(
    name: str,
    dims: Dict[str, Any],
    body_category: BodyCategory,
    cad_semantics: CadSemantics,
) -> BodyExportObject:
    """Create base Export Object with acoustic semantics."""
    points = generate_simplified_body_outline(
        dims["body_width_mm"],
        dims["body_length_mm"],
    )

    export_id = f"FIXTURE-ACOUSTIC-{name.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    return BodyExportObject(
        schema_version="1.0.0",
        export_id=export_id,
        export_type="geometry",
        metadata=ExportMetadata(
            export_id=export_id,
            schema_version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            source=ExportSource(
                preview_id=f"fixture_{name}",
                preview_hash="semantic_fixture_hash",
                generator_id="mrp5f_fixture_generator",
                generator_version="1.0.0",
            ),
            operation_category="body_profiling",
            description=f"MRP-5F acoustic semantic fixture: {name}",
        ),
        geometry=ExportGeometry(
            coordinate_system=CoordinateSystem(units="mm"),
            bounds=Bounds(
                x_min=-dims["body_width_mm"] / 2,
                x_max=dims["body_width_mm"] / 2,
                y_min=-dims["body_length_mm"] / 2,
                y_max=dims["body_length_mm"] / 2,
            ),
            entities=[
                GeometryEntity(
                    type="closed_contour",
                    id="outer",
                    role="body_outline",
                    winding="ccw",
                    points=points,
                )
            ],
        ),
        validation=ExportValidation(
            gate_status="green",
            preview_gate="green",
            export_gate="green",
            issues=[],
            warnings=[],
            checks_performed=[
                ValidationCheck(
                    check="semantic_fixture",
                    result="passed",
                    detail="MRP-5F semantic fixture - no runtime topology",
                ),
            ],
        ),
        intent=ExportIntent(),
        extensions=ExportExtensions(
            cad_semantics=cad_semantics,
        ),
    )


def create_dreadnought_semantic_fixture() -> BodyExportObject:
    """
    Create dreadnought acoustic guitar semantic fixture.

    Classification: SEMANTIC_ONLY
    Runtime support: No topology generation
    Features:
        - Tapered side profile (121mm butt → 105mm shoulder)
        - Radiused back (25ft)
        - G1 continuity target
    """
    dims = ACOUSTIC_DIMENSIONS["dreadnought"]

    cad_semantics = CadSemantics(
        schema_version="1.0.0",
        body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        acoustic=AcousticSemantics(
            thickness=ThicknessSemantics(
                top_thickness_mm=dims["top_thickness_mm"],
                back_thickness_mm=dims["back_thickness_mm"],
                side_depth_mm=dims["butt_depth_mm"],
            ),
            side_profile=SideProfileSemantics(
                type=SideProfileType.TAPERED,
                taper_axis="tail_to_neck",
                max_depth_mm=dims["butt_depth_mm"],
                min_depth_mm=dims["shoulder_depth_mm"],
            ),
            rim=RimSemantics(
                continuity_target=ContinuityTarget.G1,
                closure_type=ClosureType.CLOSED_RIM,
            ),
            plate_relationship=PlateRelationshipSemantics(
                top_type=PlateType.FLAT,
                back_type=PlateType.RADIUSED,
                back_radius_mm=dims["back_radius_mm"],
            ),
            use_ibg_side_heights=False,
        ),
    )

    return _create_base_export_object(
        "dreadnought",
        dims,
        BodyCategory.ACOUSTIC_FLAT_TOP,
        cad_semantics,
    )


def create_jumbo_semantic_fixture() -> BodyExportObject:
    """
    Create jumbo acoustic guitar semantic fixture.

    Classification: SEMANTIC_ONLY
    Features:
        - Larger body dimensions
        - Tapered side profile
        - Radiused back
    """
    dims = ACOUSTIC_DIMENSIONS["jumbo"]

    cad_semantics = CadSemantics(
        schema_version="1.0.0",
        body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        acoustic=AcousticSemantics(
            thickness=ThicknessSemantics(
                top_thickness_mm=dims["top_thickness_mm"],
                back_thickness_mm=dims["back_thickness_mm"],
                side_depth_mm=dims["butt_depth_mm"],
            ),
            side_profile=SideProfileSemantics(
                type=SideProfileType.TAPERED,
                taper_axis="tail_to_neck",
                max_depth_mm=dims["butt_depth_mm"],
                min_depth_mm=dims["shoulder_depth_mm"],
            ),
            rim=RimSemantics(
                continuity_target=ContinuityTarget.G1,
                closure_type=ClosureType.CLOSED_RIM,
            ),
            plate_relationship=PlateRelationshipSemantics(
                top_type=PlateType.FLAT,
                back_type=PlateType.RADIUSED,
                back_radius_mm=dims["back_radius_mm"],
            ),
        ),
    )

    return _create_base_export_object(
        "jumbo",
        dims,
        BodyCategory.ACOUSTIC_FLAT_TOP,
        cad_semantics,
    )


def create_parlor_semantic_fixture() -> BodyExportObject:
    """
    Create parlor acoustic guitar semantic fixture.

    Classification: SEMANTIC_ONLY
    Features:
        - Smaller body dimensions
        - Uniform side depth (no taper)
        - Radiused back (20ft)
    """
    dims = ACOUSTIC_DIMENSIONS["parlor"]

    cad_semantics = CadSemantics(
        schema_version="1.0.0",
        body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        acoustic=AcousticSemantics(
            thickness=ThicknessSemantics(
                top_thickness_mm=dims["top_thickness_mm"],
                back_thickness_mm=dims["back_thickness_mm"],
                side_depth_mm=dims["butt_depth_mm"],
            ),
            side_profile=SideProfileSemantics(
                type=SideProfileType.UNIFORM,
                max_depth_mm=dims["butt_depth_mm"],
            ),
            rim=RimSemantics(
                continuity_target=ContinuityTarget.G1,
                closure_type=ClosureType.CLOSED_RIM,
            ),
            plate_relationship=PlateRelationshipSemantics(
                top_type=PlateType.FLAT,
                back_type=PlateType.RADIUSED,
                back_radius_mm=dims["back_radius_mm"],
            ),
        ),
    )

    return _create_base_export_object(
        "parlor",
        dims,
        BodyCategory.ACOUSTIC_FLAT_TOP,
        cad_semantics,
    )


def create_hollowbody_semantic_fixture() -> BodyExportObject:
    """
    Create hollow electric guitar semantic fixture.

    Classification: SEMANTIC_ONLY
    Features:
        - Shallow body depth
        - Uniform side profile
        - Flat back
        - G0 continuity target (sharper junctions)
    """
    dims = ACOUSTIC_DIMENSIONS["hollowbody"]

    cad_semantics = CadSemantics(
        schema_version="1.0.0",
        body_category=BodyCategory.HOLLOW_ELECTRIC,
        acoustic=AcousticSemantics(
            thickness=ThicknessSemantics(
                top_thickness_mm=dims["top_thickness_mm"],
                back_thickness_mm=dims["back_thickness_mm"],
                side_depth_mm=dims["butt_depth_mm"],
            ),
            side_profile=SideProfileSemantics(
                type=SideProfileType.UNIFORM,
                max_depth_mm=dims["butt_depth_mm"],
            ),
            rim=RimSemantics(
                continuity_target=ContinuityTarget.G0,
                closure_type=ClosureType.CLOSED_RIM,
            ),
            plate_relationship=PlateRelationshipSemantics(
                top_type=PlateType.FLAT,
                back_type=PlateType.FLAT,
            ),
        ),
    )

    return _create_base_export_object(
        "hollowbody",
        dims,
        BodyCategory.HOLLOW_ELECTRIC,
        cad_semantics,
    )


# ─── Fixture Validation ──────────────────────────────────────────────────────


def validate_fixture_semantics(
    fixture: BodyExportObject,
) -> Dict[str, Any]:
    """
    Validate fixture semantic configuration.

    Returns dict with:
        - valid: bool
        - body_category: str
        - runtime_support: str
        - has_acoustic_semantics: bool
        - requires_acoustic_topology: bool
        - validation_notes: list
    """
    from app.export.cad_semantics import validate_acoustic_semantics

    result = {
        "valid": True,
        "body_category": "unknown",
        "runtime_support": "UNSUPPORTED",
        "has_acoustic_semantics": False,
        "requires_acoustic_topology": False,
        "validation_notes": [],
    }

    if not fixture.extensions or not fixture.extensions.cad_semantics:
        result["validation_notes"].append("No cad_semantics extension")
        return result

    semantics = fixture.extensions.cad_semantics
    result["body_category"] = semantics.body_category.value
    result["runtime_support"] = semantics.get_runtime_support().value
    result["has_acoustic_semantics"] = semantics.acoustic is not None
    result["requires_acoustic_topology"] = semantics.requires_acoustic_topology()

    validation = validate_acoustic_semantics(semantics)
    result["valid"] = validation.valid

    if validation.blocking_errors:
        result["validation_notes"].extend(
            [f"ERROR: {e}" for e in validation.blocking_errors]
        )
    if validation.warnings:
        result["validation_notes"].extend(
            [f"WARNING: {w}" for w in validation.warnings]
        )

    return result
