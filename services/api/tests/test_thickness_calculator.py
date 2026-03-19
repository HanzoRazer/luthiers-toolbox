"""
Tests for plate_design thickness calculator (ported from tap-tone-pi).

Covers: calibration presets, analyze_plate, analyze_coupled_system,
list_materials, list_body_styles.
"""
import pytest

from app.calculators.plate_design import (
    get_material_preset,
    get_body_calibration,
    list_materials,
    list_body_styles,
    analyze_plate,
    analyze_coupled_system,
    thickness_for_target_frequency,
    BodyStyle,
)


def test_get_material_preset_sitka():
    m = get_material_preset("sitka_spruce")
    assert m is not None
    assert m.E_L_GPa > 0
    assert m.E_C_GPa > 0
    assert m.density_kg_m3 > 0


def test_get_material_preset_unknown_returns_none():
    assert get_material_preset("nonexistent_wood") is None


def test_get_body_calibration_om():
    b = get_body_calibration(BodyStyle.OM)
    assert b is not None
    assert b.top_a_m > 0
    assert b.top_b_m > 0
    assert b.f_monopole_target > 0


def test_get_body_calibration_by_string():
    b = get_body_calibration("om")
    assert b is not None
    assert b.style == BodyStyle.OM


def test_list_materials_returns_non_empty():
    materials = list_materials()
    assert len(materials) >= 1
    names = [m["name"] for m in materials]
    assert "sitka_spruce" in names


def test_list_body_styles_returns_non_empty():
    styles = list_body_styles()
    assert len(styles) >= 1
    style_values = [s["style"] for s in styles]
    assert "om" in style_values or "jumbo" in style_values


def test_analyze_plate_returns_plate_thickness_result():
    result = analyze_plate(
        E_L_GPa=12.5,
        E_C_GPa=0.85,
        density_kg_m3=420.0,
        length_mm=500.0,
        width_mm=400.0,
        target_f_Hz=98.0,
        material_name="sitka_spruce",
    )
    assert result.recommended_h_mm > 0
    assert result.target_f_Hz == 98.0
    assert result.material == "sitka_spruce"


def test_thickness_for_target_frequency():
    # API: f_target (Hz), E_L_Pa, E_C_Pa, rho (kg/m³), a (m), b (m)
    h = thickness_for_target_frequency(
        f_target=98.0,
        E_L_Pa=12.5e9,
        E_C_Pa=0.85e9,
        rho=420.0,
        a=0.5,
        b=0.4,
    )
    assert h > 0
    assert h < 0.01  # reasonable thickness in m (e.g. 2–5 mm)


def test_analyze_coupled_system():
    calibration = get_body_calibration(BodyStyle.OM)
    assert calibration is not None
    result = analyze_coupled_system(
        body=calibration,
        top_E_L_GPa=12.5,
        top_E_C_GPa=0.85,
        top_rho=420.0,
        top_h_mm=2.8,
        back_E_L_GPa=10.2,
        back_E_C_GPa=0.65,
        back_rho=540.0,
        back_h_mm=2.5,
    )
    assert result.f1_Hz > 0
    assert result.f2_Hz > 0
    assert result.f3_Hz > 0
    assert result.recommendation is not None
