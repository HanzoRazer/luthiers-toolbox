"""
Tests for Nut Slot Export Object (CAM Dev Order 6B)

Tests the export object prototype that transforms governed previews
into portable manufacturing representations.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.export_object import EXPORT_SCHEMA_VERSION, ExportObjectResponse
from app.cam.nut_slot_cam import CamGate, NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import (
    create_nut_slot_export_object,
    generate_nut_slot_export_object,
    compute_preview_hash,
    generate_export_id,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Valid Request Fixture
# -----------------------------------------------------------------------------

VALID_REQUEST = NutSlotPreviewRequest(
    nut_width_mm=50.0,  # Wider nut for better spacing
    num_strings=6,
    edge_offset_bass_mm=4.0,  # Above 2.0mm to avoid YELLOW
    edge_offset_treble_mm=4.0,  # Above 2.0mm to avoid YELLOW
    slot_length_mm=4.5,
    slot_depth_mm=1.5,
    slot_width_mm=0.70,  # Larger than tool for GREEN (tool/slot < 90%)
    stock_thickness_mm=9.5,
    tool_diameter_mm=0.56,  # 80% of slot width - no warning
    safe_z_mm=5.0,
)

YELLOW_REQUEST = NutSlotPreviewRequest(
    nut_width_mm=43.0,
    num_strings=6,
    edge_offset_bass_mm=1.5,  # Low edge offset triggers YELLOW
    edge_offset_treble_mm=3.5,
    slot_length_mm=4.5,
    slot_depth_mm=1.5,
    slot_width_mm=0.56,
    stock_thickness_mm=9.5,
    tool_diameter_mm=0.56,
    safe_z_mm=5.0,
)

RED_REQUEST = NutSlotPreviewRequest(
    nut_width_mm=43.0,
    num_strings=6,
    edge_offset_bass_mm=3.5,
    edge_offset_treble_mm=3.5,
    slot_length_mm=4.5,
    slot_depth_mm=8.0,  # Exceeds 80% of stock thickness - RED
    slot_width_mm=0.56,
    stock_thickness_mm=9.5,
    tool_diameter_mm=0.56,
    safe_z_mm=5.0,
)


# -----------------------------------------------------------------------------
# Pure Function Tests
# -----------------------------------------------------------------------------

class TestCreateExportObject:
    """Tests for create_nut_slot_export_object pure function."""

    def test_creates_export_object_from_green_preview(self):
        """Export object is created from GREEN preview."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        assert preview.gate == CamGate.GREEN

        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        assert export_obj.schema_version == EXPORT_SCHEMA_VERSION
        assert export_obj.export_id.startswith("EXP-NUT-")
        assert export_obj.export_type.value == "toolpath"

    def test_creates_export_object_from_yellow_preview(self):
        """Export object is created from YELLOW preview."""
        preview = generate_nut_slot_preview(YELLOW_REQUEST)
        assert preview.gate == CamGate.YELLOW

        export_obj = create_nut_slot_export_object(preview, YELLOW_REQUEST)

        assert export_obj.validation.gate_status == "yellow"
        assert len(export_obj.validation.warnings) > 0

    def test_export_object_has_all_blocks(self):
        """Export object contains all required blocks."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        # All blocks present
        assert export_obj.metadata is not None
        assert export_obj.geometry is not None
        assert export_obj.toolpaths is not None
        assert export_obj.tooling is not None
        assert export_obj.material is not None
        assert export_obj.stock is not None
        assert export_obj.validation is not None
        assert export_obj.intent is not None

    def test_metadata_block_populated(self):
        """Metadata block has required fields."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        meta = export_obj.metadata
        assert meta.export_id == export_obj.export_id
        assert meta.schema_version == EXPORT_SCHEMA_VERSION
        assert meta.source.generator_id == "nut_slot_cam"
        assert meta.source.generator_version == "1.0.0"
        assert meta.operation_category == "slot_cutting"

    def test_geometry_block_populated(self):
        """Geometry block has coordinate system and bounds."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        geom = export_obj.geometry
        assert geom.coordinate_system.units == "mm"
        assert geom.coordinate_system.z_zero == "top_of_stock"
        assert geom.bounds.x_min >= 0
        assert geom.bounds.x_max <= VALID_REQUEST.nut_width_mm
        assert len(geom.entities) == VALID_REQUEST.num_strings

    def test_toolpaths_block_populated(self):
        """Toolpaths block has operations matching preview."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        tp = export_obj.toolpaths
        assert len(tp.operations) == VALID_REQUEST.num_strings
        assert tp.statistics.total_operations == VALID_REQUEST.num_strings

        # Each operation has 4 moves (rapid, plunge, linear, retract)
        for op in tp.operations:
            assert len(op.moves) == 4

    def test_tooling_block_populated(self):
        """Tooling block has tool geometry."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        tool = export_obj.tooling
        assert tool.tool_type == "slot_saw"
        assert tool.geometry.diameter_mm == VALID_REQUEST.tool_diameter_mm
        assert "slot_cutting" in tool.operation_class

    def test_material_block_default(self):
        """Material block has default values."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        mat = export_obj.material
        assert mat.material_type == "unknown"
        assert mat.material_profile_id is None

    def test_stock_block_populated(self):
        """Stock block has dimensions from request."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        stock = export_obj.stock
        assert stock.dimensions.length_mm == VALID_REQUEST.nut_width_mm
        assert stock.dimensions.thickness_mm == VALID_REQUEST.stock_thickness_mm

    def test_validation_block_populated(self):
        """Validation block has gate status and preview hash."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        val = export_obj.validation
        assert val.gate_status == "green"
        assert val.preview_gate == "green"
        assert val.export_gate == "green"
        assert val.source_preview_hash.startswith("sha256:")

    def test_intent_block_populated(self):
        """Intent block preserves manufacturing intent."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        intent = export_obj.intent
        assert intent.operation_type == "nut_slot_cutting"
        assert intent.depth_strategy == "full_depth_single_pass"


# -----------------------------------------------------------------------------
# Endpoint Function Tests
# -----------------------------------------------------------------------------

class TestGenerateExportObject:
    """Tests for generate_nut_slot_export_object endpoint function."""

    def test_green_preview_returns_exportable_true(self):
        """GREEN preview results in exportable=True."""
        response = generate_nut_slot_export_object(VALID_REQUEST)

        assert response.exportable is True
        assert response.gate == "green"
        assert response.export_object is not None
        assert len(response.errors) == 0

    def test_yellow_preview_returns_exportable_true(self):
        """YELLOW preview results in exportable=True with warnings."""
        response = generate_nut_slot_export_object(YELLOW_REQUEST)

        assert response.exportable is True
        assert response.gate == "yellow"
        assert response.export_object is not None
        assert len(response.warnings) > 0

    def test_red_preview_returns_exportable_false(self):
        """RED preview results in exportable=False with errors."""
        response = generate_nut_slot_export_object(RED_REQUEST)

        assert response.exportable is False
        assert response.gate == "red"
        assert response.export_object is None
        assert len(response.errors) > 0


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestExportObjectEndpoint:
    """Tests for POST /api/cam/nut-slot/export-object endpoint."""

    def test_valid_request_returns_200_exportable(self):
        """Valid request returns 200 with exportable export object."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json=VALID_REQUEST.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exportable"] is True
        assert data["gate"] == "green"
        assert data["export_object"] is not None

    def test_yellow_request_returns_200_exportable_with_warnings(self):
        """YELLOW request returns 200 with exportable and warnings."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json=YELLOW_REQUEST.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exportable"] is True
        assert data["gate"] == "yellow"
        assert len(data["warnings"]) > 0

    def test_red_request_returns_200_not_exportable(self):
        """RED request returns 200 with exportable=False (not 500)."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json=RED_REQUEST.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exportable"] is False
        assert data["gate"] == "red"
        assert len(data["errors"]) > 0
        assert data["export_object"] is None

    def test_malformed_request_returns_422(self):
        """Malformed request returns 422 (not 200 or 500)."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json={"invalid": "data"},
        )

        assert response.status_code == 422

    def test_export_object_schema_version(self):
        """Export object has correct schema version."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json=VALID_REQUEST.model_dump(),
        )

        data = response.json()
        export_obj = data["export_object"]
        assert export_obj["schema_version"] == EXPORT_SCHEMA_VERSION

    def test_export_object_id_format(self):
        """Export object ID follows EXP-{type}-{date}-{hash} pattern."""
        response = client.post(
            "/api/cam/nut-slot/export-object",
            json=VALID_REQUEST.model_dump(),
        )

        data = response.json()
        export_id = data["export_object"]["export_id"]
        assert export_id.startswith("EXP-NUT-")
        parts = export_id.split("-")
        assert len(parts) == 4


# -----------------------------------------------------------------------------
# Utility Function Tests
# -----------------------------------------------------------------------------

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_compute_preview_hash_returns_sha256(self):
        """Preview hash is SHA256 format."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        hash_val = compute_preview_hash(preview)

        assert hash_val.startswith("sha256:")
        assert len(hash_val) == 23  # "sha256:" + 16 hex chars

    def test_generate_export_id_format(self):
        """Export ID follows expected pattern."""
        export_id = generate_export_id("NUT")

        assert export_id.startswith("EXP-NUT-")
        parts = export_id.split("-")
        assert len(parts) == 4
        assert len(parts[2]) == 8  # YYYYMMDD
        assert len(parts[3]) == 8  # 8 hex chars


# -----------------------------------------------------------------------------
# Serialization Tests
# -----------------------------------------------------------------------------

class TestSerialization:
    """Tests for export object JSON serialization."""

    def test_export_object_json_serializable(self):
        """Export object can be serialized to JSON."""
        preview = generate_nut_slot_preview(VALID_REQUEST)
        export_obj = create_nut_slot_export_object(preview, VALID_REQUEST)

        # Should not raise
        json_str = export_obj.model_dump_json()
        assert len(json_str) > 0

    def test_export_response_json_serializable(self):
        """Export response can be serialized to JSON."""
        response = generate_nut_slot_export_object(VALID_REQUEST)

        # Should not raise
        json_str = response.model_dump_json()
        assert len(json_str) > 0
