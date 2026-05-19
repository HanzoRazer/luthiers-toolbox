"""
MRP-2B: Body Export Bridge Tests

Tests for the BOE → Export Object bridge endpoint and adapter.

Sprint: MRP-2B
"""

import pytest
from datetime import datetime

from app.export.body_export_bridge import (
    BOEApprovedGeometry,
    BOEMetadata,
    ContourData,
    IBGContext,
    BodyExportObject,
    compute_bounds,
    generate_export_id,
    validate_body_geometry,
    create_body_export_object,
    is_export_ready,
)


# ─── Test Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def valid_outer_contour():
    """Valid closed outer contour (guitar body shape with enough points)."""
    return ContourData(
        id="body",
        role="outer",
        closed=True,
        winding="ccw",
        points=[
            [0.0, 0.0],
            [50.0, 10.0],
            [100.0, 0.0],
            [150.0, 20.0],
            [200.0, 0.0],
            [200.0, 100.0],
            [200.0, 200.0],
            [200.0, 300.0],
            [200.0, 400.0],
            [150.0, 400.0],
            [100.0, 400.0],
            [50.0, 400.0],
            [0.0, 400.0],
            [0.0, 300.0],
            [0.0, 200.0],
            [0.0, 100.0],
            [0.0, 0.0],  # Closed - back to start
        ],
    )


@pytest.fixture
def valid_soundhole_void():
    """Valid soundhole void."""
    return ContourData(
        id="soundhole_0",
        role="soundhole",
        closed=True,
        winding="cw",
        points=[
            [100.0, 200.0],
            [120.0, 200.0],
            [120.0, 220.0],
            [100.0, 220.0],
            [100.0, 200.0],
        ],
    )


@pytest.fixture
def valid_boe_geometry(valid_outer_contour):
    """Valid BOE-approved geometry."""
    return BOEApprovedGeometry(
        schema_version=1,
        units="mm",
        origin="body_center_y_positive_toward_neck",
        metadata=BOEMetadata(
            name="test_body",
            source="body_outline_editor_sandbox",
            created_at=datetime.utcnow().isoformat(),
        ),
        outer=valid_outer_contour,
        voids=[],
    )


@pytest.fixture
def valid_ibg_context():
    """Valid IBG session context."""
    return IBGContext(
        session_id="sess_abc123",
        confidence=0.87,
        dimensions={
            "body_length_mm": 521.3,
            "lower_bout_mm": 382.1,
            "upper_bout_mm": 293.5,
            "waist_mm": 240.8,
        },
        instrument_spec="dreadnought",
        side_heights_mm=[94.2, 95.1, 96.0],
        radii_by_zone={"lower_bout": 265.3, "waist": 85.2, "upper_bout": 175.6},
    )


@pytest.fixture
def full_ibg_context():
    """MRP-2C: Full IBG context with missing_landmarks and recovery_mode."""
    return IBGContext(
        session_id="sess_full_123",
        confidence=0.72,
        dimensions={
            "body_length_mm": 480.5,
            "lower_bout_mm": 360.2,
        },
        instrument_spec="cuatro_venezolano",
        side_heights_mm=[85.0, 86.5, 88.0],
        radii_by_zone={"lower_bout": 245.0, "waist": 80.0},
        missing_landmarks=["upper_bout_max", "waist_min"],
        recovery_mode="spec_fallback",
    )


# ─── Bounds Computation Tests ────────────────────────────────────────────────


class TestComputeBounds:
    """Tests for compute_bounds function."""

    def test_simple_rectangle(self):
        """Computes correct bounds for rectangle."""
        points = [[0, 0], [100, 0], [100, 200], [0, 200]]
        bounds = compute_bounds(points)

        assert bounds.x_min == 0
        assert bounds.x_max == 100
        assert bounds.y_min == 0
        assert bounds.y_max == 200
        assert bounds.z_min == 0.0
        assert bounds.z_max == 0.0

    def test_negative_coordinates(self):
        """Handles negative coordinates correctly."""
        points = [[-50, -100], [50, -100], [50, 100], [-50, 100]]
        bounds = compute_bounds(points)

        assert bounds.x_min == -50
        assert bounds.x_max == 50
        assert bounds.y_min == -100
        assert bounds.y_max == 100

    def test_empty_points(self):
        """Returns zero bounds for empty points."""
        bounds = compute_bounds([])

        assert bounds.x_min == 0
        assert bounds.x_max == 0
        assert bounds.y_min == 0
        assert bounds.y_max == 0


# ─── Export ID Generation Tests ──────────────────────────────────────────────


class TestGenerateExportId:
    """Tests for generate_export_id function."""

    def test_format_pattern(self):
        """Export ID follows EXP-BODY-{date}-{hash} pattern."""
        points = [[0, 0], [100, 0], [100, 200]]
        export_id = generate_export_id(points)

        assert export_id.startswith("EXP-BODY-")
        parts = export_id.split("-")
        assert len(parts) == 4
        assert len(parts[2]) == 8  # YYYYMMDD
        assert len(parts[3]) == 8  # 8-char hash

    def test_deterministic(self):
        """Same points produce same export ID (deterministic hash)."""
        points = [[0, 0], [100, 0], [100, 200]]
        id1 = generate_export_id(points)
        id2 = generate_export_id(points)

        # Hash part should match (date might differ if midnight crossed)
        assert id1.split("-")[3] == id2.split("-")[3]

    def test_different_points_different_hash(self):
        """Different points produce different hash."""
        points1 = [[0, 0], [100, 0]]
        points2 = [[0, 0], [200, 0]]

        id1 = generate_export_id(points1)
        id2 = generate_export_id(points2)

        assert id1.split("-")[3] != id2.split("-")[3]


# ─── Validation Tests ────────────────────────────────────────────────────────


class TestValidateBodyGeometry:
    """Tests for validate_body_geometry function."""

    def test_valid_geometry_green_gate(self, valid_outer_contour):
        """Valid geometry produces green gate."""
        validation = validate_body_geometry(valid_outer_contour, [])

        assert validation.gate_status == "green"
        assert len(validation.issues) == 0

    def test_open_contour_red_gate(self):
        """Open contour produces red gate."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,  # Says closed but points don't match
            winding="ccw",
            points=[
                [0.0, 0.0],
                [20.0, 0.0],
                [40.0, 0.0],
                [60.0, 0.0],
                [80.0, 0.0],
                [100.0, 0.0],
                [100.0, 50.0],
                [100.0, 100.0],
                [100.0, 150.0],
                [100.0, 200.0],
                # Missing closing point - ends at [100, 200] instead of [0, 0]
            ],
        )
        validation = validate_body_geometry(outer, [])

        assert validation.gate_status == "red"
        assert "not closed" in str(validation.issues).lower()

    def test_wrong_winding_yellow_gate(self):
        """Wrong winding produces yellow gate (warning)."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,
            winding="cw",  # Should be ccw
            points=[
                [0.0, 0.0],
                [25.0, 0.0],
                [50.0, 0.0],
                [75.0, 0.0],
                [100.0, 0.0],
                [100.0, 50.0],
                [100.0, 100.0],
                [100.0, 150.0],
                [100.0, 200.0],
                [75.0, 200.0],
                [50.0, 200.0],
                [25.0, 200.0],
                [0.0, 200.0],
                [0.0, 150.0],
                [0.0, 100.0],
                [0.0, 50.0],
                [0.0, 0.0],  # Closed
            ],
        )
        validation = validate_body_geometry(outer, [])

        assert validation.gate_status == "yellow"
        assert any("winding" in w.lower() for w in validation.warnings)

    def test_too_few_points_warning(self):
        """Too few points produces warning."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,
            winding="ccw",
            points=[
                [0.0, 0.0],
                [100.0, 0.0],
                [100.0, 200.0],
                [0.0, 0.0],  # Only 4 points
            ],
        )
        validation = validate_body_geometry(outer, [])

        # Should have warning about low point count
        assert any("points" in w.lower() for w in validation.warnings)

    def test_no_points_red_gate(self):
        """No points produces red gate."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,
            winding="ccw",
            points=[],
        )
        validation = validate_body_geometry(outer, [])

        assert validation.gate_status == "red"
        assert any("no points" in i.lower() for i in validation.issues)

    def test_void_winding_check(self, valid_outer_contour):
        """Void with wrong winding produces warning."""
        void = ContourData(
            id="soundhole",
            role="soundhole",
            closed=True,
            winding="ccw",  # Should be cw for voids
            points=[[50, 50], [60, 50], [60, 60], [50, 60], [50, 50]],
        )
        validation = validate_body_geometry(valid_outer_contour, [void])

        assert any("void" in w.lower() for w in validation.warnings)


# ─── Export Object Creation Tests ────────────────────────────────────────────


class TestCreateBodyExportObject:
    """Tests for create_body_export_object function."""

    def test_minimal_export(self, valid_boe_geometry):
        """Creates valid Export Object from minimal BOE geometry."""
        export_obj = create_body_export_object(valid_boe_geometry)

        assert export_obj.schema_version == "1.0.0"
        assert export_obj.export_type == "geometry"
        assert export_obj.export_id.startswith("EXP-BODY-")
        assert export_obj.metadata.operation_category == "body_profiling"
        assert len(export_obj.geometry.entities) == 1

    def test_with_voids(self, valid_boe_geometry, valid_soundhole_void):
        """Includes voids in geometry entities."""
        valid_boe_geometry.voids = [valid_soundhole_void]
        export_obj = create_body_export_object(valid_boe_geometry)

        assert len(export_obj.geometry.entities) == 2
        roles = [e.role for e in export_obj.geometry.entities]
        assert "outer" in roles
        assert "soundhole" in roles

    def test_with_ibg_context(self, valid_boe_geometry, valid_ibg_context):
        """IBG context is preserved in extensions."""
        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=valid_ibg_context,
        )

        assert export_obj.extensions is not None
        assert export_obj.extensions.ibg_morphology is not None
        assert export_obj.extensions.ibg_morphology.confidence == 0.87
        assert export_obj.extensions.ibg_morphology.session_id == "sess_abc123"
        assert export_obj.extensions.ibg_morphology.instrument_spec == "dreadnought"

    def test_ibg_context_in_source_metadata(self, valid_boe_geometry, valid_ibg_context):
        """IBG context appears in source metadata."""
        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=valid_ibg_context,
        )

        assert export_obj.metadata.source.ibg_session_id == "sess_abc123"
        assert export_obj.metadata.source.ibg_confidence == 0.87
        assert export_obj.metadata.source.instrument_spec == "dreadnought"

    def test_embedded_ibg_context(self, valid_boe_geometry, valid_ibg_context):
        """IBG context embedded in BOE geometry is used."""
        valid_boe_geometry.ibg_context = valid_ibg_context
        export_obj = create_body_export_object(valid_boe_geometry)

        assert export_obj.extensions is not None
        assert export_obj.extensions.ibg_morphology.session_id == "sess_abc123"

    def test_explicit_ibg_context_overrides(self, valid_boe_geometry, valid_ibg_context):
        """Explicit IBG context parameter overrides embedded."""
        embedded_ctx = IBGContext(
            session_id="sess_embedded",
            confidence=0.5,
            dimensions={},
            instrument_spec="jumbo",
        )
        valid_boe_geometry.ibg_context = embedded_ctx

        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=valid_ibg_context,  # Should override
        )

        assert export_obj.extensions.ibg_morphology.session_id == "sess_abc123"

    def test_no_dxf_fields(self, valid_boe_geometry):
        """Export Object contains no DXF-specific fields."""
        export_obj = create_body_export_object(valid_boe_geometry)
        export_dict = export_obj.model_dump()

        # Convert to string and check for DXF leakage
        export_str = str(export_dict).lower()

        forbidden = ["dxf", "lwpolyline", "ac1009", "ac1015", "ezdxf", "layer_0"]
        for term in forbidden:
            assert term not in export_str, f"DXF term '{term}' found in Export Object"

    def test_coordinate_system_defaults(self, valid_boe_geometry):
        """Coordinate system has correct defaults."""
        export_obj = create_body_export_object(valid_boe_geometry)
        cs = export_obj.geometry.coordinate_system

        assert cs.origin == "body_center"
        assert cs.units == "mm"
        assert cs.handedness == "right_handed"
        assert cs.z_zero == "top_face"

    def test_bounds_computed(self, valid_boe_geometry):
        """Bounds are computed from geometry."""
        export_obj = create_body_export_object(valid_boe_geometry)
        bounds = export_obj.geometry.bounds

        # Should have non-zero bounds for our test geometry
        assert bounds.x_max > bounds.x_min
        assert bounds.y_max > bounds.y_min

    def test_validation_block_present(self, valid_boe_geometry):
        """Validation block is present and populated."""
        export_obj = create_body_export_object(valid_boe_geometry)

        assert export_obj.validation is not None
        assert export_obj.validation.gate_status in ("green", "yellow", "red")
        assert len(export_obj.validation.checks_performed) > 0

    def test_intent_defaults(self, valid_boe_geometry):
        """Intent block has correct defaults."""
        export_obj = create_body_export_object(valid_boe_geometry)
        intent = export_obj.intent

        assert intent.operation_type == "body_profiling"
        assert intent.depth_strategy == "full_thickness"
        assert intent.finish_requirements.surface_finish == "router_quality"

    def test_missing_landmarks_preserved(self, valid_boe_geometry, full_ibg_context):
        """MRP-2C: missing_landmarks preserved in extensions."""
        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=full_ibg_context,
        )

        assert export_obj.extensions is not None
        assert export_obj.extensions.ibg_morphology.missing_landmarks == [
            "upper_bout_max",
            "waist_min",
        ]

    def test_recovery_mode_preserved(self, valid_boe_geometry, full_ibg_context):
        """MRP-2C: recovery_mode preserved in extensions."""
        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=full_ibg_context,
        )

        assert export_obj.extensions is not None
        assert export_obj.extensions.ibg_morphology.recovery_mode == "spec_fallback"

    def test_optional_fields_can_be_none(self, valid_boe_geometry, valid_ibg_context):
        """MRP-2C: missing_landmarks and recovery_mode can be None."""
        export_obj = create_body_export_object(
            valid_boe_geometry,
            ibg_context=valid_ibg_context,
        )

        assert export_obj.extensions is not None
        assert export_obj.extensions.ibg_morphology.missing_landmarks is None
        assert export_obj.extensions.ibg_morphology.recovery_mode is None


# ─── Export Ready Tests ──────────────────────────────────────────────────────


class TestIsExportReady:
    """Tests for is_export_ready function."""

    def test_green_is_ready(self, valid_boe_geometry):
        """Green gate geometry is export-ready."""
        export_obj = create_body_export_object(valid_boe_geometry)
        assert is_export_ready(export_obj.validation)

    def test_yellow_is_ready(self):
        """Yellow gate geometry is export-ready (with warnings)."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,
            winding="cw",  # Wrong winding -> yellow
            points=[
                [0.0, 0.0],
                [25.0, 0.0],
                [50.0, 0.0],
                [75.0, 0.0],
                [100.0, 0.0],
                [100.0, 50.0],
                [100.0, 100.0],
                [100.0, 150.0],
                [100.0, 200.0],
                [75.0, 200.0],
                [50.0, 200.0],
                [25.0, 200.0],
                [0.0, 200.0],
                [0.0, 150.0],
                [0.0, 100.0],
                [0.0, 50.0],
                [0.0, 0.0],  # Closed
            ],
        )
        boe = BOEApprovedGeometry(outer=outer, voids=[])
        export_obj = create_body_export_object(boe)

        assert export_obj.validation.gate_status == "yellow"
        assert is_export_ready(export_obj.validation)

    def test_red_not_ready(self):
        """Red gate geometry is not export-ready."""
        outer = ContourData(
            id="body",
            role="outer",
            closed=True,
            winding="ccw",
            points=[],  # No points -> red
        )
        boe = BOEApprovedGeometry(outer=outer, voids=[])
        export_obj = create_body_export_object(boe)

        assert export_obj.validation.gate_status == "red"
        assert not is_export_ready(export_obj.validation)


# ─── API Endpoint Tests ──────────────────────────────────────────────────────


class TestBodyExportEndpoint:
    """Integration tests for /api/export/body-outline endpoint."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"Could not load app: {e}")

    def test_valid_geometry_returns_export_object(self, client):
        """Valid geometry returns Export Object with 200."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center_y_positive_toward_neck",
                "metadata": {
                    "name": "test_body",
                    "source": "test",
                },
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [
                        [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                        [100, 50], [100, 100], [100, 150], [100, 200],
                        [75, 200], [50, 200], [25, 200], [0, 200],
                        [0, 150], [0, 100], [0, 50], [0, 0],
                    ],
                },
                "voids": [],
            }
        }

        response = client.post("/api/export/body-outline", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        if response.status_code == 422:
            print(f"Validation error: {response.json()}")

        assert response.status_code == 200
        data = response.json()

        assert "export_object" in data
        assert data["export_ready"] is True
        assert data["gate_status"] == "green"
        assert data["export_object"]["schema_version"] == "1.0.0"
        assert data["export_object"]["export_type"] == "geometry"

    def test_invalid_geometry_returns_red_gate(self, client):
        """Invalid geometry returns red gate status."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center",
                "metadata": {"name": "test", "source": "test"},
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [],  # Empty -> validation failure
                },
                "voids": [],
            }
        }

        response = client.post("/api/export/body-outline", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        if response.status_code == 422:
            print(f"Validation error: {response.json()}")

        assert response.status_code == 200  # Still 200, validation in response
        data = response.json()

        assert data["export_ready"] is False
        assert data["gate_status"] == "red"
        assert len(data["issues"]) > 0

    def test_with_ibg_context(self, client):
        """IBG context is included in response."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center",
                "metadata": {"name": "test", "source": "test"},
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [
                        [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                        [100, 50], [100, 100], [100, 150], [100, 200],
                        [75, 200], [50, 200], [25, 200], [0, 200],
                        [0, 150], [0, 100], [0, 50], [0, 0],
                    ],
                },
                "voids": [],
            },
            "ibg_context": {
                "session_id": "sess_test123",
                "confidence": 0.92,
                "dimensions": {"body_length_mm": 500},
                "instrument_spec": "dreadnought",
            },
        }

        response = client.post("/api/export/body-outline", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        if response.status_code == 422:
            print(f"Validation error: {response.json()}")

        assert response.status_code == 200
        data = response.json()

        export_obj = data["export_object"]
        assert "extensions" in export_obj
        assert export_obj["extensions"]["ibg_morphology"]["session_id"] == "sess_test123"

    def test_validate_only_endpoint(self, client):
        """Validate-only endpoint returns validation without Export Object."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center",
                "metadata": {"name": "test", "source": "test"},
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [
                        [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                        [100, 50], [100, 100], [100, 150], [100, 200],
                        [75, 200], [50, 200], [25, 200], [0, 200],
                        [0, 150], [0, 100], [0, 50], [0, 0],
                    ],
                },
                "voids": [],
            }
        }

        response = client.post("/api/export/body-outline/validate", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        if response.status_code == 422:
            print(f"Validation error: {response.json()}")

        assert response.status_code == 200
        data = response.json()

        assert "valid" in data
        assert "gate_status" in data
        assert "checks" in data
        assert "export_object" not in data

    def test_with_full_ibg_context(self, client):
        """MRP-2C: Full IBG context with missing_landmarks and recovery_mode."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center",
                "metadata": {"name": "test", "source": "test"},
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [
                        [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                        [100, 50], [100, 100], [100, 150], [100, 200],
                        [75, 200], [50, 200], [25, 200], [0, 200],
                        [0, 150], [0, 100], [0, 50], [0, 0],
                    ],
                },
                "voids": [],
            },
            "ibg_context": {
                "session_id": "sess_mrp2c",
                "confidence": 0.65,
                "dimensions": {"body_length_mm": 450},
                "instrument_spec": "cuatro_venezolano",
                "missing_landmarks": ["waist_min"],
                "recovery_mode": "partial_spec",
            },
        }

        response = client.post("/api/export/body-outline", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        if response.status_code == 422:
            print(f"Validation error: {response.json()}")

        assert response.status_code == 200
        data = response.json()

        export_obj = data["export_object"]
        ibg_ext = export_obj["extensions"]["ibg_morphology"]
        assert ibg_ext["missing_landmarks"] == ["waist_min"]
        assert ibg_ext["recovery_mode"] == "partial_spec"

    def test_export_without_ibg_context(self, client):
        """MRP-2C: Export without IBG context is valid."""
        request_body = {
            "geometry": {
                "schema_version": 1,
                "units": "mm",
                "origin": "body_center",
                "metadata": {"name": "test", "source": "test"},
                "outer": {
                    "id": "body",
                    "role": "outer",
                    "closed": True,
                    "winding": "ccw",
                    "points": [
                        [0, 0], [25, 0], [50, 0], [75, 0], [100, 0],
                        [100, 50], [100, 100], [100, 150], [100, 200],
                        [75, 200], [50, 200], [25, 200], [0, 200],
                        [0, 150], [0, 100], [0, 50], [0, 0],
                    ],
                },
                "voids": [],
            },
            # No ibg_context
        }

        response = client.post("/api/export/body-outline", json=request_body)

        if response.status_code == 404:
            pytest.skip("Body export router not loaded")

        assert response.status_code == 200
        data = response.json()

        export_obj = data["export_object"]
        # extensions should be None when no IBG context
        assert export_obj.get("extensions") is None
