"""
Nut Slot CAM Preview Tests

CAM Dev Order 1: Tests for POST /api/cam/nut-slot/preview

Test coverage:
  - Unit tests for gate evaluation (RED/YELLOW/GREEN)
  - Unit tests for position generation
  - Endpoint tests for request/response validation
"""

import pytest
from fastapi.testclient import TestClient

from app.cam.nut_slot_cam import (
    CamGate,
    NutSlotPreviewRequest,
    generate_nut_slot_preview,
    generate_string_positions,
    evaluate_gate,
)
from app.main import app


client = TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def valid_6_string_request() -> NutSlotPreviewRequest:
    """Valid 6-string guitar nut request."""
    return NutSlotPreviewRequest(
        nut_width_mm=43.0,
        num_strings=6,
        edge_offset_bass_mm=3.5,
        edge_offset_treble_mm=3.5,
        string_positions_x_mm=None,
        slot_length_mm=4.0,
        slot_depth_mm=1.5,
        slot_width_mm=0.56,
        stock_thickness_mm=6.0,
        tool_diameter_mm=0.5,
        safe_z_mm=5.0,
    )


@pytest.fixture
def explicit_positions_request() -> NutSlotPreviewRequest:
    """Request with explicit string positions."""
    return NutSlotPreviewRequest(
        nut_width_mm=43.0,
        num_strings=6,
        edge_offset_bass_mm=3.5,
        edge_offset_treble_mm=3.5,
        string_positions_x_mm=[3.5, 10.7, 17.9, 25.1, 32.3, 39.5],
        slot_length_mm=4.0,
        slot_depth_mm=1.5,
        slot_width_mm=0.56,
        stock_thickness_mm=6.0,
        tool_diameter_mm=0.5,
        safe_z_mm=5.0,
    )


# =============================================================================
# Unit Tests: Gate Evaluation
# =============================================================================

class TestGateEvaluationGreen:
    """Tests for GREEN gate conditions."""

    def test_valid_6_string_generated_positions_green(self, valid_6_string_request):
        """Test 1: Valid 6-string with generated positions → GREEN."""
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.GREEN
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.statistics.total_slots == 6

    def test_valid_explicit_positions_green(self, explicit_positions_request):
        """Test 2: Valid explicit positions → GREEN."""
        result = generate_nut_slot_preview(explicit_positions_request)
        assert result.gate == CamGate.GREEN
        assert len(result.errors) == 0


class TestGateEvaluationRed:
    """Tests for RED gate conditions."""

    def test_slot_depth_equals_stock_thickness_red(self, valid_6_string_request):
        """Test 3: slot_depth_mm >= stock_thickness_mm → RED."""
        valid_6_string_request.slot_depth_mm = 6.0  # equals stock thickness
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("stock thickness" in e.lower() for e in result.errors)

    def test_slot_depth_over_80_percent_red(self, valid_6_string_request):
        """Test 4: slot_depth_mm > 80% stock thickness → RED."""
        valid_6_string_request.slot_depth_mm = 5.0  # 83% of 6.0
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("80%" in e for e in result.errors)

    def test_tool_larger_than_slot_red(self, valid_6_string_request):
        """Test 6: tool_diameter_mm > slot_width_mm → RED."""
        valid_6_string_request.tool_diameter_mm = 0.7  # larger than 0.56
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("tool diameter" in e.lower() for e in result.errors)

    def test_position_outside_nut_width_red(self, valid_6_string_request):
        """Test 8: position outside nut width → RED."""
        valid_6_string_request.string_positions_x_mm = [3.5, 10.0, 20.0, 30.0, 40.0, 50.0]  # 50 > 43
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("exceeds nut width" in e.lower() for e in result.errors)

    def test_positions_not_increasing_red(self, valid_6_string_request):
        """Test 9: positions not strictly increasing → RED."""
        valid_6_string_request.string_positions_x_mm = [3.5, 10.0, 10.0, 25.0, 32.0, 39.0]  # duplicate
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("not strictly increasing" in e.lower() for e in result.errors)

    def test_negative_position_red(self, valid_6_string_request):
        """Position negative → RED."""
        valid_6_string_request.string_positions_x_mm = [-1.0, 10.0, 20.0, 25.0, 32.0, 39.0]
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.RED
        assert any("negative" in e.lower() for e in result.errors)


class TestGateEvaluationYellow:
    """Tests for YELLOW gate conditions."""

    def test_slot_depth_60_to_80_percent_yellow(self, valid_6_string_request):
        """Test 5: slot_depth_mm 60-80% stock thickness → YELLOW."""
        valid_6_string_request.slot_depth_mm = 4.0  # 67% of 6.0
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("60-80%" in w for w in result.warnings)

    def test_tool_90_to_100_percent_of_slot_yellow(self, valid_6_string_request):
        """Test 7: tool_diameter_mm 90-100% of slot_width_mm → YELLOW."""
        valid_6_string_request.tool_diameter_mm = 0.52  # 93% of 0.56
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("tight fit" in w.lower() for w in result.warnings)

    def test_adjacent_spacing_under_5mm_yellow(self, valid_6_string_request):
        """Test 10: adjacent spacing under 5mm → YELLOW."""
        # With narrow nut, spacing will be tight
        valid_6_string_request.nut_width_mm = 30.0
        valid_6_string_request.edge_offset_bass_mm = 2.0
        valid_6_string_request.edge_offset_treble_mm = 2.0
        # spacing = (30 - 4) / 5 = 5.2mm, but let's make it tighter
        valid_6_string_request.string_positions_x_mm = [2.0, 6.0, 12.0, 18.0, 24.0, 28.0]  # 4mm spacing at start
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("spacing" in w.lower() for w in result.warnings)

    def test_edge_offset_under_2mm_yellow(self, valid_6_string_request):
        """Edge offset under 2mm → YELLOW."""
        valid_6_string_request.edge_offset_treble_mm = 1.5
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("edge offset" in w.lower() for w in result.warnings)

    def test_stock_thickness_under_3mm_yellow(self, valid_6_string_request):
        """Stock thickness under 3mm → YELLOW."""
        valid_6_string_request.stock_thickness_mm = 2.5
        valid_6_string_request.slot_depth_mm = 1.0  # keep depth ratio safe
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("stock thickness" in w.lower() for w in result.warnings)

    def test_slot_width_under_020mm_yellow(self, valid_6_string_request):
        """Slot width under 0.20mm → YELLOW."""
        valid_6_string_request.slot_width_mm = 0.15
        valid_6_string_request.tool_diameter_mm = 0.10  # keep tool smaller
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("slot width" in w.lower() for w in result.warnings)

    def test_slot_length_under_2mm_yellow(self, valid_6_string_request):
        """Slot length under 2mm → YELLOW."""
        valid_6_string_request.slot_length_mm = 1.5
        result = generate_nut_slot_preview(valid_6_string_request)
        assert result.gate == CamGate.YELLOW
        assert any("slot length" in w.lower() for w in result.warnings)


class TestNumStringsValidation:
    """Tests for num_strings validation."""

    def test_num_strings_zero_pydantic_error(self):
        """Test 11a: num_strings = 0 → Pydantic validation error."""
        with pytest.raises(ValueError):
            NutSlotPreviewRequest(
                nut_width_mm=43.0,
                num_strings=0,
                edge_offset_bass_mm=3.5,
                edge_offset_treble_mm=3.5,
                slot_length_mm=4.0,
                slot_depth_mm=1.5,
                slot_width_mm=0.56,
                stock_thickness_mm=6.0,
                tool_diameter_mm=0.5,
            )

    def test_num_strings_13_pydantic_error(self):
        """Test 11b: num_strings > 12 → Pydantic validation error."""
        with pytest.raises(ValueError):
            NutSlotPreviewRequest(
                nut_width_mm=43.0,
                num_strings=13,
                edge_offset_bass_mm=3.5,
                edge_offset_treble_mm=3.5,
                slot_length_mm=4.0,
                slot_depth_mm=1.5,
                slot_width_mm=0.56,
                stock_thickness_mm=6.0,
                tool_diameter_mm=0.5,
            )


class TestNegativeDimensions:
    """Tests for negative/zero dimensions."""

    def test_negative_slot_depth_pydantic_error(self):
        """Test 12a: negative slot_depth_mm → Pydantic error."""
        with pytest.raises(ValueError):
            NutSlotPreviewRequest(
                nut_width_mm=43.0,
                num_strings=6,
                edge_offset_bass_mm=3.5,
                edge_offset_treble_mm=3.5,
                slot_length_mm=4.0,
                slot_depth_mm=-1.0,
                slot_width_mm=0.56,
                stock_thickness_mm=6.0,
                tool_diameter_mm=0.5,
            )

    def test_zero_nut_width_pydantic_error(self):
        """Test 12b: zero nut_width_mm → Pydantic error."""
        with pytest.raises(ValueError):
            NutSlotPreviewRequest(
                nut_width_mm=0,
                num_strings=6,
                edge_offset_bass_mm=3.5,
                edge_offset_treble_mm=3.5,
                slot_length_mm=4.0,
                slot_depth_mm=1.5,
                slot_width_mm=0.56,
                stock_thickness_mm=6.0,
                tool_diameter_mm=0.5,
            )


# =============================================================================
# Unit Tests: Position Generation
# =============================================================================

class TestPositionGeneration:
    """Tests for string position generation."""

    def test_6_string_positions_count(self):
        """6 strings generates 6 positions."""
        positions = generate_string_positions(
            num_strings=6,
            nut_width_mm=43.0,
            edge_offset_treble_mm=3.5,
            edge_offset_bass_mm=3.5,
        )
        assert len(positions) == 6

    def test_positions_within_nut_width(self):
        """All positions within nut width."""
        positions = generate_string_positions(
            num_strings=6,
            nut_width_mm=43.0,
            edge_offset_treble_mm=3.5,
            edge_offset_bass_mm=3.5,
        )
        for pos in positions:
            assert 0 <= pos <= 43.0

    def test_positions_strictly_increasing(self):
        """Positions are strictly increasing."""
        positions = generate_string_positions(
            num_strings=6,
            nut_width_mm=43.0,
            edge_offset_treble_mm=3.5,
            edge_offset_bass_mm=3.5,
        )
        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]

    def test_single_string_position(self):
        """Single string at treble edge offset."""
        positions = generate_string_positions(
            num_strings=1,
            nut_width_mm=43.0,
            edge_offset_treble_mm=3.5,
            edge_offset_bass_mm=3.5,
        )
        assert len(positions) == 1
        assert positions[0] == 3.5


# =============================================================================
# Endpoint Tests
# =============================================================================

class TestEndpoint:
    """Tests for POST /api/cam/nut-slot/preview endpoint."""

    def test_valid_request_returns_200_green(self):
        """Test 13: valid request → 200 + GREEN."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": 43.0,
                "num_strings": 6,
                "edge_offset_bass_mm": 3.5,
                "edge_offset_treble_mm": 3.5,
                "slot_length_mm": 4.0,
                "slot_depth_mm": 1.5,
                "slot_width_mm": 0.56,
                "stock_thickness_mm": 6.0,
                "tool_diameter_mm": 0.5,
                "safe_z_mm": 5.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gate"] == "green"
        assert data["operation"] == "nut_slot_preview"
        assert data["status"] == "experimental"
        assert len(data["toolpaths"]) == 6

    def test_domain_violation_returns_200_red(self):
        """Test 14: domain/safety violation → 200 + RED."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": 43.0,
                "num_strings": 6,
                "edge_offset_bass_mm": 3.5,
                "edge_offset_treble_mm": 3.5,
                "slot_length_mm": 4.0,
                "slot_depth_mm": 6.0,  # equals stock thickness
                "slot_width_mm": 0.56,
                "stock_thickness_mm": 6.0,
                "tool_diameter_mm": 0.5,
                "safe_z_mm": 5.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gate"] == "red"
        assert len(data["errors"]) > 0

    def test_malformed_request_returns_422(self):
        """Test 15: malformed request → 422."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": "not a number",  # wrong type
                "num_strings": 6,
            },
        )
        assert response.status_code == 422

    def test_missing_required_field_returns_422(self):
        """Missing required field → 422."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": 43.0,
                # missing num_strings and other required fields
            },
        )
        assert response.status_code == 422

    def test_response_structure(self):
        """Response has expected structure."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": 43.0,
                "num_strings": 6,
                "edge_offset_bass_mm": 3.5,
                "edge_offset_treble_mm": 3.5,
                "slot_length_mm": 4.0,
                "slot_depth_mm": 1.5,
                "slot_width_mm": 0.56,
                "stock_thickness_mm": 6.0,
                "tool_diameter_mm": 0.5,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Check top-level fields
        assert "operation" in data
        assert "status" in data
        assert "gate" in data
        assert "units" in data
        assert "coordinate_system" in data
        assert "machine_profile" in data
        assert "tool" in data
        assert "toolpaths" in data
        assert "warnings" in data
        assert "errors" in data
        assert "statistics" in data

        # Check coordinate system
        cs = data["coordinate_system"]
        assert cs["origin"] == "local_nut_left_face"
        assert cs["z_zero"] == "top_of_stock"
        assert cs["x_axis"] == "string_to_string"
        assert cs["y_axis"] == "slot_length"

        # Check toolpath structure
        tp = data["toolpaths"][0]
        assert "slot_index" in tp
        assert "string_number" in tp
        assert "x_mm" in tp
        assert "moves" in tp
        assert len(tp["moves"]) == 4  # rapid, plunge, linear, retract

    def test_toolpath_move_sequence(self):
        """Toolpath moves follow correct sequence."""
        response = client.post(
            "/api/cam/nut-slot/preview",
            json={
                "nut_width_mm": 43.0,
                "num_strings": 1,
                "edge_offset_bass_mm": 3.5,
                "edge_offset_treble_mm": 3.5,
                "slot_length_mm": 4.0,
                "slot_depth_mm": 1.5,
                "slot_width_mm": 0.56,
                "stock_thickness_mm": 6.0,
                "tool_diameter_mm": 0.5,
                "safe_z_mm": 5.0,
            },
        )
        data = response.json()
        moves = data["toolpaths"][0]["moves"]

        assert moves[0]["type"] == "rapid"
        assert moves[0]["z"] == 5.0  # safe_z

        assert moves[1]["type"] == "plunge"
        assert moves[1]["z"] == -1.5  # -slot_depth

        assert moves[2]["type"] == "linear"
        assert moves[2]["y"] == 4.0  # slot_length
        assert moves[2]["z"] == -1.5

        assert moves[3]["type"] == "retract"
        assert moves[3]["z"] == 5.0  # safe_z
