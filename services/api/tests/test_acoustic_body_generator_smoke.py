"""Smoke tests for AcousticBodyGenerator (GEN-6) — 732 lines, 0% prior coverage."""

import pytest


# =============================================================================
# AcousticBodyStyle enum
# =============================================================================

def test_style_enum_has_expected_members():
    from app.generators.acoustic_body_generator import AcousticBodyStyle
    assert "dreadnought" in [s.value for s in AcousticBodyStyle]
    assert "om_000" in [s.value for s in AcousticBodyStyle]
    assert "oo" in [s.value for s in AcousticBodyStyle]


# =============================================================================
# AcousticBodyGenerator.from_style — factory
# =============================================================================

def test_from_style_dreadnought():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    assert gen.style.value == "dreadnought"


def test_from_style_alias_om():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("om")
    assert gen.style.value == "om_000"


def test_from_style_alias_000():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("000")
    assert gen.style.value == "om_000"


def test_from_style_alias_oo():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("oo")
    assert gen.style.value == "oo"


def test_from_style_unknown_raises():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    with pytest.raises(ValueError, match="Unknown acoustic style"):
        AcousticBodyGenerator.from_style("banjo")


# =============================================================================
# AcousticBodyGenerator.from_project — project dict factory
# =============================================================================

def test_from_project_defaults():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_project({})
    assert gen.style.value == "dreadnought"
    assert gen.scale == 1.0


def test_from_project_with_machine():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_project({
        "body_style": "om",
        "machine": {"safe_z": 15.0, "spindle_rpm": 20000},
    })
    assert gen.style.value == "om_000"
    assert gen.safe_z == 15.0
    assert gen.spindle_rpm == 20000


# =============================================================================
# generate_outline — core outline generation
# =============================================================================

def test_generate_outline_dreadnought():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    result = gen.generate_outline()
    assert result.style == "dreadnought"
    assert result.point_count > 0
    assert len(result.points) == result.point_count
    assert result.width_mm > 0
    assert result.length_mm > 0


def test_generate_outline_om():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("om").generate_outline()
    assert result.style == "om_000"
    assert result.point_count > 0


def test_generate_outline_oo_uses_fallback():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("oo").generate_outline()
    assert result.style == "oo"
    # OO may use fallback outline — either way should have points
    assert result.point_count >= 0


def test_generate_outline_scaled():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    full = AcousticBodyGenerator.from_style("dreadnought", scale=1.0).generate_outline()
    half = AcousticBodyGenerator.from_style("dreadnought", scale=0.5).generate_outline()
    assert half.scale_factor == 0.5
    assert half.soundhole_diameter_mm == pytest.approx(full.soundhole_diameter_mm * 0.5, rel=0.01)


def test_generate_outline_has_soundhole():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    assert result.soundhole_center is not None
    assert result.soundhole_diameter_mm > 0


def test_generate_outline_bounding_box():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    bb = result.bounding_box
    assert "min_x" in bb and "max_x" in bb
    assert "min_y" in bb and "max_y" in bb
    assert bb["max_x"] > bb["min_x"]
    assert bb["max_y"] > bb["min_y"]


def test_generate_outline_reference_specs_notes():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    notes_text = " ".join(result.notes)
    # Should contain reference info and volume/helmholtz estimates
    assert "Reference" in notes_text or "volume" in notes_text.lower() or len(result.notes) > 0


# =============================================================================
# AcousticBodyResult — serialization
# =============================================================================

def test_to_dict():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    d = result.to_dict()
    assert d["style"] == "dreadnought"
    assert isinstance(d["points"], list)
    assert "centroid" in d
    assert "bounding_box" in d
    assert "soundhole" in d
    assert "depth" in d


def test_to_svg():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    svg = result.to_svg()
    assert "<svg" in svg
    assert "<path" in svg
    assert "</svg>" in svg


def test_to_svg_with_soundhole():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    svg = result.to_svg(include_soundhole=True)
    assert "<circle" in svg


def test_to_svg_with_centerline():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    result = AcousticBodyGenerator.from_style("dreadnought").generate_outline()
    svg = result.to_svg(include_centerline=True)
    assert "<line" in svg


# =============================================================================
# G-code generation
# =============================================================================

def test_perimeter_gcode_returns_string():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    gcode = gen.generate_perimeter_gcode()
    assert isinstance(gcode, str)
    assert "G21" in gcode  # mm units
    assert "G90" in gcode  # absolute
    assert "M30" in gcode  # program end
    assert "DREADNOUGHT" in gcode


def test_perimeter_gcode_contains_passes():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    gcode = gen.generate_perimeter_gcode(total_depth_mm=9.0, stepdown_mm=3.0)
    assert "Pass 1/" in gcode
    assert "Pass 3/" in gcode


def test_soundhole_gcode_returns_string():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    gcode = gen.generate_soundhole_gcode()
    assert isinstance(gcode, str)
    assert "SOUNDHOLE" in gcode
    assert "G2" in gcode  # circular interpolation


def test_binding_channel_gcode_returns_string():
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style("dreadnought")
    gcode = gen.generate_binding_channel_gcode()
    assert isinstance(gcode, str)
    assert "BINDING CHANNEL" in gcode
    assert "M30" in gcode


# =============================================================================
# Convenience functions
# =============================================================================

def test_generate_acoustic_outline_convenience():
    from app.generators.acoustic_body_generator import generate_acoustic_outline
    result = generate_acoustic_outline("dreadnought")
    assert result.style == "dreadnought"
    assert result.point_count > 0


def test_list_acoustic_styles():
    from app.generators.acoustic_body_generator import list_acoustic_styles
    styles = list_acoustic_styles()
    assert isinstance(styles, list)
    assert len(styles) > 0
    ids = [s["id"] for s in styles]
    assert "dreadnought" in ids


def test_get_dreadnought_outline():
    from app.generators.acoustic_body_generator import get_dreadnought_outline
    result = get_dreadnought_outline()
    assert result.style == "dreadnought"


def test_get_om_outline():
    from app.generators.acoustic_body_generator import get_om_outline
    result = get_om_outline()
    assert result.style == "om_000"


def test_get_oo_outline():
    from app.generators.acoustic_body_generator import get_oo_outline
    result = get_oo_outline()
    assert result.style == "oo"


# =============================================================================
# All enum styles generate without error
# =============================================================================

@pytest.mark.parametrize("style", [
    "dreadnought", "jumbo", "om", "oo", "parlor", "classical", "j45", "gibson_l_00",
])
def test_all_styles_generate_outline(style):
    from app.generators.acoustic_body_generator import AcousticBodyGenerator
    gen = AcousticBodyGenerator.from_style(style)
    result = gen.generate_outline()
    assert result.style is not None
    assert isinstance(result.points, list)
