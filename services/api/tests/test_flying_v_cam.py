# tests/test_flying_v_cam.py
"""
Flying V CAM Module Tests

Tests for:
- FV-GAP-05: Pocket toolpath generator for parametric cavity placement
- FV-GAP-10: Neck pocket depth validation
"""

import pytest
from pathlib import Path


class TestFlyingVSpecLoading:
    """Test spec JSON loading."""

    def test_load_default_variant(self):
        """Load default 1958 variant."""
        from app.cam.flying_v import load_flying_v_spec

        spec = load_flying_v_spec()

        assert spec.model_id == "flying_v"
        assert spec.variant == "original_1958"
        assert spec.body_thickness_mm == 44.45
        assert spec.scale_length_mm == 628.65

    def test_load_reissue_variant(self):
        """Load 2023 reissue variant."""
        from app.cam.flying_v import load_flying_v_spec

        spec = load_flying_v_spec("reissue_2023")

        assert spec.variant == "reissue_2023"
        assert spec.scale_length_mm == 628.65

    def test_neck_pocket_dimensions(self):
        """Verify neck pocket dimensions from spec."""
        from app.cam.flying_v import load_flying_v_spec

        spec = load_flying_v_spec()
        pocket = spec.neck_pocket

        # From gibson_flying_v_1958.json
        assert pocket.width_mm == 38.0  # tenon_width_mm
        assert pocket.length_mm == 76.0  # tenon_length_mm
        assert pocket.depth_mm == 19.0  # tenon_depth_mm
        assert pocket.center_x == 0.0  # Centered

    def test_control_cavity_dimensions(self):
        """Verify control cavity dimensions from spec."""
        from app.cam.flying_v import load_flying_v_spec

        spec = load_flying_v_spec()
        cavity = spec.control_cavity

        assert cavity.length_mm == 95.0
        assert cavity.width_mm == 60.0
        assert cavity.depth_mm == 35.0

    def test_pickup_cavity_dimensions(self):
        """Verify pickup cavity dimensions from spec."""
        from app.cam.flying_v import load_flying_v_spec

        spec = load_flying_v_spec()

        # Neck pickup
        assert spec.neck_pickup.length_mm == 71.0  # PAF humbucker
        assert spec.neck_pickup.width_mm == 40.0
        assert spec.neck_pickup.depth_mm == 19.0
        assert spec.neck_pickup.center_y == 155.0  # From bridge

        # Bridge pickup
        assert spec.bridge_pickup.length_mm == 71.0
        assert spec.bridge_pickup.center_y == 20.0


class TestControlCavityToolpath:
    """Test control cavity pocket generation."""

    def test_generates_valid_gcode(self):
        """Control cavity generates valid G-code."""
        from app.cam.flying_v import load_flying_v_spec, generate_control_cavity_toolpath

        spec = load_flying_v_spec()
        gcode = generate_control_cavity_toolpath(spec)

        # Check header
        assert "Flying V 1958" in gcode
        assert "Control Cavity" in gcode
        assert "35.0mm deep" in gcode  # Depth from spec

        # Check G-code basics
        assert "G90" in gcode  # Absolute mode
        assert "G21" in gcode  # Metric
        assert "M3 S18000" in gcode  # Spindle on

    def test_depth_matches_spec(self):
        """Control cavity reaches correct depth."""
        from app.cam.flying_v import (
            load_flying_v_spec,
            generate_control_cavity_toolpath,
            validate_control_cavity_depth,
        )

        spec = load_flying_v_spec()
        gcode = generate_control_cavity_toolpath(spec)

        result = validate_control_cavity_depth(gcode, spec)

        assert result.ok, f"Validation failed: {result.errors}"
        assert result.max_depth == pytest.approx(35.0, abs=0.5)

    def test_parametric_placement(self):
        """Cavity position matches spec."""
        from app.cam.flying_v import load_flying_v_spec, generate_control_cavity_toolpath

        spec = load_flying_v_spec()
        gcode = generate_control_cavity_toolpath(spec)

        # Check that the cavity center is used (X=30, Y=-80)
        assert "X=30" in gcode or "X30" in gcode or "X=30.0" in gcode
        assert "Y=-80" in gcode or "Y-80" in gcode or "Y=-80.0" in gcode


class TestNeckPocketToolpath:
    """Test neck pocket mortise generation."""

    def test_generates_valid_gcode(self):
        """Neck pocket generates valid G-code."""
        from app.cam.flying_v import load_flying_v_spec, generate_neck_pocket_toolpath

        spec = load_flying_v_spec()
        gcode = generate_neck_pocket_toolpath(spec)

        assert "Neck Pocket Mortise" in gcode
        assert "19.0mm deep" in gcode or "19mm" in gcode  # From spec
        assert "ROUGHING" in gcode
        assert "FINISHING" in gcode

    def test_depth_matches_spec(self):
        """Neck pocket reaches correct depth."""
        from app.cam.flying_v import (
            load_flying_v_spec,
            generate_neck_pocket_toolpath,
            validate_neck_pocket_depth,
        )

        spec = load_flying_v_spec()
        gcode = generate_neck_pocket_toolpath(spec)

        result = validate_neck_pocket_depth(gcode, spec)

        assert result.ok, f"Validation failed: {result.errors}"
        assert result.expected_depth_mm == 19.0
        assert result.max_depth == pytest.approx(19.0, abs=0.5)

    def test_uses_downcut_for_finish(self):
        """Finishing pass uses downcut spiral for clean walls."""
        from app.cam.flying_v import load_flying_v_spec, generate_neck_pocket_toolpath

        spec = load_flying_v_spec()
        gcode = generate_neck_pocket_toolpath(spec)

        assert "DOWNCUT" in gcode.upper()


class TestPickupCavityToolpath:
    """Test pickup cavity pocket generation."""

    def test_generates_both_pickups(self):
        """Can generate both pickup cavities."""
        from app.cam.flying_v import load_flying_v_spec, generate_pickup_cavity_toolpath

        spec = load_flying_v_spec()
        gcode = generate_pickup_cavity_toolpath(spec, pickup="both")

        assert "NECK PICKUP" in gcode.upper()
        assert "BRIDGE PICKUP" in gcode.upper()

    def test_generates_single_pickup(self):
        """Can generate single pickup cavity."""
        from app.cam.flying_v import load_flying_v_spec, generate_pickup_cavity_toolpath

        spec = load_flying_v_spec()

        neck_gcode = generate_pickup_cavity_toolpath(spec, pickup="neck")
        assert "NECK PICKUP" in neck_gcode.upper()
        assert "BRIDGE PICKUP" not in neck_gcode.upper()

        bridge_gcode = generate_pickup_cavity_toolpath(spec, pickup="bridge")
        assert "BRIDGE PICKUP" in bridge_gcode.upper()


class TestDepthValidation:
    """Test depth validation (FV-GAP-10)."""

    def test_validates_correct_depth(self):
        """Accepts G-code with correct depth."""
        from app.cam.flying_v import validate_neck_pocket_depth

        # G-code with correct 19mm depth
        gcode = """
        G90
        G21
        M3 S18000
        G0 Z5.0
        G1 Z-19.0 F600
        G1 X10 Y10 F2000
        G0 Z5.0
        M30
        """

        result = validate_neck_pocket_depth(gcode)

        assert result.ok
        assert result.max_depth == 19.0
        assert len(result.errors) == 0

    def test_rejects_incorrect_depth(self):
        """Rejects G-code with wrong depth."""
        from app.cam.flying_v import validate_neck_pocket_depth

        # G-code with wrong depth (15mm instead of 19mm)
        gcode = """
        G90
        G21
        M3 S18000
        G0 Z5.0
        G1 Z-15.0 F600
        G1 X10 Y10 F2000
        G0 Z5.0
        M30
        """

        result = validate_neck_pocket_depth(gcode, tolerance_mm=0.5)

        assert not result.ok
        assert result.max_depth == 15.0
        assert len(result.errors) > 0
        assert "mismatch" in result.errors[0].lower()

    def test_warns_on_deep_cut(self):
        """Warns when cutting deeper than spec."""
        from app.cam.flying_v import validate_neck_pocket_depth

        # G-code cutting too deep (25mm)
        gcode = """
        G1 Z-25.0 F600
        """

        result = validate_neck_pocket_depth(gcode, tolerance_mm=0.5)

        # Should fail because depth doesn't match 19mm
        assert not result.ok
        # Should also warn about going deeper than spec
        assert any("deeper" in w.lower() for w in result.warnings)

    def test_validates_control_cavity_depth(self):
        """Validates control cavity against 35mm spec."""
        from app.cam.flying_v import validate_control_cavity_depth

        gcode = """
        G1 Z-35.0 F600
        """

        result = validate_control_cavity_depth(gcode)

        assert result.ok
        assert result.expected_depth_mm == 35.0
        assert result.max_depth == 35.0

    def test_validate_all_depths(self):
        """Validates multiple operations at once."""
        from app.cam.flying_v import validate_all_depths

        gcode_dict = {
            "neck_pocket": "G1 Z-19.0 F600",
            "control_cavity": "G1 Z-35.0 F600",
        }

        results = validate_all_depths(gcode_dict)

        assert "neck_pocket" in results
        assert "control_cavity" in results
        assert results["neck_pocket"].ok
        assert results["control_cavity"].ok


class TestExistingGcodeValidation:
    """Test validation against existing G-code files."""

    @pytest.fixture
    def exports_dir(self):
        """Get exports directory."""
        return Path(__file__).parent.parent.parent.parent / "exports"

    def test_validate_existing_neck_control_file(self, exports_dir):
        """Validate existing Flying V neck/control G-code file."""
        from app.cam.flying_v import validate_flying_v_gcode_file

        nc_file = exports_dir / "flying_v_1958_neck_control_strings_mach4.nc"

        if not nc_file.exists():
            pytest.skip(f"G-code file not found: {nc_file}")

        # Validate neck pocket depth
        result = validate_flying_v_gcode_file(nc_file, "neck_pocket")

        # Should find depths in the file
        assert len(result.actual_depths) > 0, "No depths extracted from file"

        # Check that 19mm depth is present
        assert any(
            18.5 <= d <= 19.5 for d in result.actual_depths
        ), f"Expected ~19mm depth, found: {result.actual_depths}"
