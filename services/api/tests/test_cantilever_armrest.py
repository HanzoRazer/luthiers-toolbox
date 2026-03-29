"""
Tests for cantilever arm rest calculator and endpoint.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.calculators.cantilever_armrest_calc import (
    ArmRestSpec,
    ArmRestSection,
    GcodeConfig,
    compute_armrest,
    compute_section,
    compute_ruled_surface,
    generate_gcode,
    f_taper,
    preset_standard,
    preset_classical,
    preset_archtop,
)


client = TestClient(app)


# --- Core Math Tests ---

class TestFTaper:
    def test_f_taper_at_zero(self):
        assert f_taper(0.0, 0.38) == 0.0

    def test_f_taper_at_apex(self):
        assert f_taper(0.38, 0.38) == pytest.approx(1.0, abs=0.001)

    def test_f_taper_at_one(self):
        assert f_taper(1.0, 0.38) == pytest.approx(0.0, abs=0.001)

    def test_f_taper_clamped_below_zero(self):
        assert f_taper(-0.5, 0.38) == 0.0

    def test_f_taper_clamped_above_one(self):
        assert f_taper(1.5, 0.38) == pytest.approx(0.0, abs=0.001)

    def test_f_taper_with_zero_apex(self):
        result = f_taper(0.5, 0.0)
        assert 0 <= result <= 1


# --- Validate Tests ---

class TestArmRestSpecValidate:
    def test_validate_t_apex_too_low(self):
        spec = ArmRestSpec(t_apex=0.1)
        warnings = spec.validate()
        assert any("t_apex" in w for w in warnings)

    def test_validate_t_apex_too_high(self):
        spec = ArmRestSpec(t_apex=0.7)
        warnings = spec.validate()
        assert any("t_apex" in w for w in warnings)

    def test_validate_t_veneer_too_thin(self):
        spec = ArmRestSpec(t_veneer_mm=1.5)
        warnings = spec.validate()
        assert any("t_veneer" in w for w in warnings)

    def test_validate_r_edge_too_large(self):
        spec = ArmRestSpec(h_max_mm=10.0, r_edge_mm=9.0)
        warnings = spec.validate()
        assert any("r_edge" in w for w in warnings)

    def test_validate_w_glue_too_wide(self):
        spec = ArmRestSpec(w_glue_max_mm=30.0)
        warnings = spec.validate()
        assert any("w_glue_max" in w for w in warnings)

    def test_validate_valid_spec_no_warnings(self):
        spec = preset_standard()
        warnings = spec.validate()
        assert len(warnings) == 0


# --- Section Tests ---

class TestComputeSection:
    def test_compute_section_at_apex(self):
        spec = preset_standard()
        section = compute_section(spec.t_apex, spec)
        assert section.h_total_mm == pytest.approx(spec.h_max_mm, abs=0.1)
        assert section.theta_deg == pytest.approx(spec.theta_max_deg, abs=0.5)

    def test_compute_section_at_tips(self):
        spec = preset_standard()
        section_0 = compute_section(0.0, spec)
        section_1 = compute_section(1.0, spec)
        assert section_0.h_total_mm == pytest.approx(0.0, abs=0.1)
        assert section_1.h_total_mm == pytest.approx(0.0, abs=0.1)

    def test_section_to_dict(self):
        spec = preset_standard()
        section = compute_section(0.5, spec)
        d = section.to_dict()
        assert isinstance(d, dict)
        assert "t" in d


# --- Ruled Surface Tests ---

class TestComputeRuledSurface:
    def test_ruled_surface_grid_dimensions(self):
        spec = preset_standard()
        grid = compute_ruled_surface(spec, n_span=10, n_cross=4)
        assert len(grid) == 11
        assert len(grid[0]) == 5

    def test_ruled_surface_point_structure(self):
        spec = preset_standard()
        grid = compute_ruled_surface(spec, n_span=5, n_cross=3)
        pt = grid[2][1]
        assert hasattr(pt, "t")
        assert hasattr(pt, "u")
        assert hasattr(pt, "x_mm")

    def test_ruled_surface_y_progression(self):
        spec = preset_standard()
        grid = compute_ruled_surface(spec, n_span=10, n_cross=3)
        y_start = grid[0][0].y_mm
        y_end = grid[-1][0].y_mm
        assert y_start == pytest.approx(0.0, abs=0.1)
        assert y_end == pytest.approx(spec.span_mm, abs=0.1)


# --- G-code Tests ---

class TestGenerateGcode:
    def test_gcode_header(self):
        spec = preset_standard()
        cfg = GcodeConfig()
        gcode = generate_gcode(spec, cfg, n_span=5)
        assert "Cantilever Arm Rest" in gcode
        assert "G90 G21 G17" in gcode

    def test_gcode_footer(self):
        spec = preset_standard()
        cfg = GcodeConfig()
        gcode = generate_gcode(spec, cfg, n_span=5)
        assert "M5" in gcode
        assert "M30" in gcode

    def test_gcode_contains_feed_moves(self):
        spec = preset_standard()
        cfg = GcodeConfig()
        gcode = generate_gcode(spec, cfg, n_span=5)
        assert "G1" in gcode

    def test_gcode_config_defaults(self):
        cfg = GcodeConfig()
        assert cfg.feed_roughing > 0
        assert cfg.spindle_rpm > 0


# --- Result and Report Tests ---

class TestArmRestResult:
    def test_format_report_structure(self):
        spec = preset_standard()
        result = compute_armrest(spec, n_stations=5)
        report = result.format_report()
        assert isinstance(report, str)
        assert "CANTILEVER ARM REST" in report
        assert "INPUTS" in report

    def test_format_report_with_warnings(self):
        spec = ArmRestSpec(
            span_mm=50.0,
            h_max_mm=5.0,
            t_veneer_mm=1.0,
        )
        result = compute_armrest(spec, n_stations=5)
        report = result.format_report()
        assert "WARNINGS" in report


# --- Presets Tests ---

class TestPresets:
    def test_preset_archtop(self):
        spec = preset_archtop()
        assert spec.span_mm == 160
        assert spec.h_max_mm == 18
        assert spec.theta_max_deg == 45

    def test_all_presets_valid(self):
        for preset_fn in [preset_standard, preset_classical, preset_archtop]:
            spec = preset_fn()
            result = compute_armrest(spec)
            assert result.apex_section is not None


# --- Original Unit Tests ---

def test_compute_armrest_standard_preset():
    spec = preset_standard()
    result = compute_armrest(spec, n_stations=11)
    assert len(result.sections) == 11
    assert result.apex_section is not None
    assert result.max_overhang_mm > 0


def test_compute_armrest_validates_spec():
    spec = ArmRestSpec(span_mm=50.0, h_max_mm=30.0, theta_max_deg=75.0)
    result = compute_armrest(spec)
    assert len(result.sections) > 0


def test_sections_ordered_by_t():
    spec = preset_classical()
    result = compute_armrest(spec, n_stations=11)
    t_values = [s.t for s in result.sections]
    assert t_values == sorted(t_values)
    assert t_values[0] == 0.0
    assert t_values[-1] == 1.0


# --- Endpoint Tests ---
# NOTE: These endpoints only exist in the deprecated monolith (instrument_geometry_router.py)


@pytest.mark.skip(reason="Endpoint only in deprecated monolith (instrument_geometry_router.py)")
def test_cantilever_armrest_endpoint_with_preset():
    response = client.post("/api/instrument/cantilever-armrest", json={"preset": "standard"})
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert "apex_section" in data


@pytest.mark.skip(reason="Endpoint only in deprecated monolith (instrument_geometry_router.py)")
def test_cantilever_armrest_endpoint_custom_params():
    response = client.post("/api/instrument/cantilever-armrest", json={
        "span_mm": 160.0, "t_apex": 0.4, "h_max_mm": 12.0, "theta_max_deg": 40.0, "n_stations": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["sections"]) == 5


@pytest.mark.skip(reason="Endpoint only in deprecated monolith (instrument_geometry_router.py)")
def test_cantilever_armrest_presets_endpoint():
    response = client.get("/api/instrument/cantilever-armrest/presets")
    assert response.status_code == 200
    data = response.json()
    assert "standard" in data
    assert "classical" in data
    assert "archtop" in data
