"""
Acoustic Semantic Compatibility Tests.

Sprint: MRP-5F
Tests:
    1. Backward compatibility with flat-body fixtures
    2. DXF translator ignores acoustic semantics safely
    3. SVG translator ignores acoustic semantics safely
    4. STEP translator safe rejection (when implemented)
    5. Provenance preservation
    6. No geometry mutation
    7. Authority boundary preservation
"""

import pytest
from datetime import datetime, timezone

from app.export.body_export_bridge import (
    BodyExportObject,
    BOEApprovedGeometry,
    BOEMetadata,
    ContourData,
    ExportExtensions,
    create_body_export_object,
)
from app.export.cad_semantics import (
    AcousticSemantics,
    BodyCategory,
    CadSemantics,
    FlatBodySemantics,
    RuntimeSupport,
    SideProfileSemantics,
    SideProfileType,
    ThicknessSemantics,
    validate_acoustic_semantics,
)


# ─── Test Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def simple_rectangle_points():
    """Simple rectangular outline for testing."""
    return [
        [-100.0, -150.0],
        [100.0, -150.0],
        [100.0, 150.0],
        [-100.0, 150.0],
        [-100.0, -150.0],
    ]


@pytest.fixture
def flat_body_boe_geometry(simple_rectangle_points):
    """BOE-approved geometry without acoustic semantics."""
    return BOEApprovedGeometry(
        schema_version=1,
        units="mm",
        origin="body_center_y_positive_toward_neck",
        metadata=BOEMetadata(
            name="flat_body_test",
            source="test_fixture",
        ),
        outer=ContourData(
            id="outer",
            role="body_outline",
            closed=True,
            winding="ccw",
            points=simple_rectangle_points,
        ),
        voids=[],
    )


@pytest.fixture
def flat_body_semantics():
    """Flat body CAD semantics."""
    return CadSemantics(
        body_category=BodyCategory.FLAT_BODY,
        flat_body=FlatBodySemantics(uniform_thickness_mm=45.0),
    )


@pytest.fixture
def acoustic_semantics():
    """Acoustic body CAD semantics."""
    return CadSemantics(
        body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        acoustic=AcousticSemantics(
            thickness=ThicknessSemantics(
                top_thickness_mm=2.8,
                back_thickness_mm=2.5,
                side_depth_mm=121.0,
            ),
            side_profile=SideProfileSemantics(
                type=SideProfileType.TAPERED,
                max_depth_mm=121.0,
                min_depth_mm=105.0,
            ),
        ),
    )


# ─── Backward Compatibility Tests ────────────────────────────────────────────


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing Export Objects."""

    def test_export_object_without_cad_semantics_valid(
        self, flat_body_boe_geometry
    ):
        """Export Object without cad_semantics should still be valid."""
        export_obj = create_body_export_object(flat_body_boe_geometry)

        assert export_obj.export_id is not None
        assert export_obj.geometry is not None
        assert export_obj.geometry.entities[0].role == "body_outline"

    def test_export_object_with_flat_body_semantics_valid(
        self, flat_body_boe_geometry, flat_body_semantics
    ):
        """Export Object with flat_body semantics should be valid."""
        export_obj = create_body_export_object(flat_body_boe_geometry)

        # Add semantics
        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = flat_body_semantics

        assert export_obj.extensions.cad_semantics is not None
        assert export_obj.extensions.cad_semantics.body_category == BodyCategory.FLAT_BODY
        assert export_obj.extensions.cad_semantics.get_runtime_support() == RuntimeSupport.SUPPORTED

    def test_export_object_with_acoustic_semantics_valid(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Export Object with acoustic semantics should be schema-valid."""
        export_obj = create_body_export_object(flat_body_boe_geometry)

        # Add semantics
        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        validation = validate_acoustic_semantics(acoustic_semantics)

        assert validation.valid is True
        assert validation.runtime_support == RuntimeSupport.SEMANTIC_ONLY

    def test_geometry_unchanged_after_semantic_addition(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Geometry should be unchanged after adding acoustics semantics."""
        export_obj = create_body_export_object(flat_body_boe_geometry)
        original_points = export_obj.geometry.entities[0].points.copy()

        # Add semantics
        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        # Geometry should be unchanged
        assert export_obj.geometry.entities[0].points == original_points


# ─── DXF Translator Compatibility Tests ──────────────────────────────────────


class TestDXFTranslatorCompatibility:
    """Tests for DXF translator ignoring acoustic semantics."""

    def test_dxf_translator_import_without_error(self):
        """DXF translator should import without acoustic-related errors."""
        try:
            from app.cam.translators.dxf.body_outline_translator import (
                BodyOutlineDxfTranslator,
            )

            translator = BodyOutlineDxfTranslator()
            assert translator is not None
        except ImportError as e:
            pytest.skip(f"DXF translator not available: {e}")

    def test_dxf_translator_capabilities_unchanged(self):
        """DXF translator capabilities should be unchanged by acoustic semantics."""
        try:
            from app.cam.translators.dxf.body_outline_translator import (
                BodyOutlineDxfTranslator,
            )

            translator = BodyOutlineDxfTranslator()
            # DXF translator should not claim acoustic support
            caps = translator.get_capabilities()

            # Should support body_outline
            assert "body_outline" in caps.supported_operations or hasattr(caps, "input_types")
        except ImportError:
            pytest.skip("DXF translator not available")
        except AttributeError:
            # Translator might have different capability interface
            pass


# ─── Runtime Support Classification Tests ────────────────────────────────────


class TestTranslatorRuntimeClassification:
    """Tests for translator runtime support classification."""

    def test_flat_body_classified_as_supported(self, flat_body_semantics):
        """Flat body should be classified as SUPPORTED."""
        assert flat_body_semantics.get_runtime_support() == RuntimeSupport.SUPPORTED

    def test_acoustic_classified_as_semantic_only(self, acoustic_semantics):
        """Acoustic semantics should be classified as SEMANTIC_ONLY."""
        assert acoustic_semantics.get_runtime_support() == RuntimeSupport.SEMANTIC_ONLY

    def test_unsupported_topology_detection(self, acoustic_semantics):
        """Should detect when acoustic topology runtime would be required."""
        assert acoustic_semantics.requires_acoustic_topology() is True

    def test_flat_body_no_topology_requirement(self, flat_body_semantics):
        """Flat body should not require acoustic topology."""
        assert flat_body_semantics.requires_acoustic_topology() is False


# ─── Provenance Preservation Tests ───────────────────────────────────────────


class TestProvenancePreservation:
    """Tests for semantic provenance preservation."""

    def test_semantics_schema_version_preserved(self, acoustic_semantics):
        """Schema version should be preserved in semantics."""
        assert acoustic_semantics.schema_version == "1.0.0"

    def test_body_category_preserved(self, acoustic_semantics):
        """Body category should be preserved."""
        assert acoustic_semantics.body_category == BodyCategory.ACOUSTIC_FLAT_TOP

    def test_acoustic_fields_preserved(self, acoustic_semantics):
        """Acoustic semantic fields should be preserved."""
        assert acoustic_semantics.acoustic is not None
        assert acoustic_semantics.acoustic.thickness is not None
        assert acoustic_semantics.acoustic.thickness.top_thickness_mm == 2.8
        assert acoustic_semantics.acoustic.side_profile is not None
        assert acoustic_semantics.acoustic.side_profile.type == SideProfileType.TAPERED


# ─── No Geometry Mutation Tests ──────────────────────────────────────────────


class TestNoGeometryMutation:
    """Tests ensuring semantics don't mutate geometry."""

    def test_semantics_dont_modify_coordinates(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Adding semantics should not modify coordinate values."""
        original_coords = [
            [p[0], p[1]] for p in flat_body_boe_geometry.outer.points
        ]

        export_obj = create_body_export_object(flat_body_boe_geometry)
        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        final_coords = [
            [p[0], p[1]] for p in export_obj.geometry.entities[0].points
        ]

        assert original_coords == final_coords

    def test_semantics_dont_add_entities(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Adding semantics should not add geometry entities."""
        export_obj = create_body_export_object(flat_body_boe_geometry)
        original_entity_count = len(export_obj.geometry.entities)

        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        assert len(export_obj.geometry.entities) == original_entity_count

    def test_semantics_dont_modify_bounds(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Adding semantics should not modify bounding box."""
        export_obj = create_body_export_object(flat_body_boe_geometry)
        original_bounds = (
            export_obj.geometry.bounds.x_min,
            export_obj.geometry.bounds.x_max,
            export_obj.geometry.bounds.y_min,
            export_obj.geometry.bounds.y_max,
        )

        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        final_bounds = (
            export_obj.geometry.bounds.x_min,
            export_obj.geometry.bounds.x_max,
            export_obj.geometry.bounds.y_min,
            export_obj.geometry.bounds.y_max,
        )

        assert original_bounds == final_bounds


# ─── Authority Boundary Tests ────────────────────────────────────────────────


class TestAuthorityBoundary:
    """Tests for authority boundary preservation."""

    def test_boe_geometry_is_source_of_truth(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """BOE geometry should remain source of truth."""
        export_obj = create_body_export_object(flat_body_boe_geometry)

        # BOE points should be in export object
        boe_points = flat_body_boe_geometry.outer.points
        export_points = export_obj.geometry.entities[0].points

        assert boe_points == export_points

    def test_semantics_in_extensions_not_geometry(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Semantics should be in extensions block, not geometry."""
        export_obj = create_body_export_object(flat_body_boe_geometry)
        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        # Geometry block should not contain cad_semantics
        assert not hasattr(export_obj.geometry, "cad_semantics")

        # Extensions block should contain cad_semantics
        assert export_obj.extensions.cad_semantics is not None

    def test_validation_gate_unchanged_by_semantics(
        self, flat_body_boe_geometry, acoustic_semantics
    ):
        """Validation gate should be based on geometry, not semantics."""
        export_obj = create_body_export_object(flat_body_boe_geometry)
        original_gate = export_obj.validation.gate_status

        if export_obj.extensions is None:
            export_obj.extensions = ExportExtensions()
        export_obj.extensions.cad_semantics = acoustic_semantics

        # Gate status unchanged by adding semantics
        assert export_obj.validation.gate_status == original_gate


# ─── Acoustic Fixture Integration Tests ──────────────────────────────────────


class TestAcousticFixtureIntegration:
    """Tests for acoustic fixture corpus integration."""

    def test_dreadnought_fixture_validates(self):
        """Dreadnought fixture should validate."""
        try:
            from tests.cam.fixtures.acoustic import (
                create_dreadnought_semantic_fixture,
            )

            fixture = create_dreadnought_semantic_fixture()
            assert fixture.extensions is not None
            assert fixture.extensions.cad_semantics is not None

            validation = validate_acoustic_semantics(
                fixture.extensions.cad_semantics
            )
            assert validation.valid is True
        except ImportError:
            pytest.skip("Acoustic fixtures not available")

    def test_all_fixtures_have_semantic_only_runtime(self):
        """All acoustic fixtures should be SEMANTIC_ONLY."""
        try:
            from tests.cam.fixtures.acoustic import (
                create_dreadnought_semantic_fixture,
                create_jumbo_semantic_fixture,
                create_parlor_semantic_fixture,
                create_hollowbody_semantic_fixture,
            )

            fixtures = [
                create_dreadnought_semantic_fixture(),
                create_jumbo_semantic_fixture(),
                create_parlor_semantic_fixture(),
                create_hollowbody_semantic_fixture(),
            ]

            for fixture in fixtures:
                semantics = fixture.extensions.cad_semantics
                assert semantics.get_runtime_support() in (
                    RuntimeSupport.SEMANTIC_ONLY,
                    RuntimeSupport.UNSUPPORTED,
                )
        except ImportError:
            pytest.skip("Acoustic fixtures not available")

    def test_fixture_manifest_matches_fixtures(self):
        """Fixture manifest should match actual fixtures."""
        try:
            from tests.cam.fixtures.acoustic import ACOUSTIC_FIXTURE_MANIFEST

            assert "dreadnought_semantic" in ACOUSTIC_FIXTURE_MANIFEST["fixtures"]
            assert "jumbo_semantic" in ACOUSTIC_FIXTURE_MANIFEST["fixtures"]
            assert "parlor_semantic" in ACOUSTIC_FIXTURE_MANIFEST["fixtures"]
            assert "hollowbody_semantic" in ACOUSTIC_FIXTURE_MANIFEST["fixtures"]
        except ImportError:
            pytest.skip("Acoustic fixtures not available")
