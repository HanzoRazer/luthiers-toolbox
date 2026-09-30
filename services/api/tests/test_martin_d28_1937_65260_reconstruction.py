from app.instrument_geometry.bracing.martin_d28_1937_65260 import (
    D28_65260_RECONSTRUCTION_V01,
    get_martin_d28_1937_65260_reconstruction,
)


def test_d28_65260_reconstruction_validates():
    model = get_martin_d28_1937_65260_reconstruction()
    assert model is D28_65260_RECONSTRUCTION_V01
    assert model.maturity == "RECONSTRUCTION_CANDIDATE"


def test_soundhole_is_datum_a():
    model = get_martin_d28_1937_65260_reconstruction()
    assert model.datum_a.feature == "soundhole"
    assert model.datum_a.diameter_in == 4.0
    assert "center" in model.datum_a.allowed_references


def test_x_brace_angles_close():
    model = get_martin_d28_1937_65260_reconstruction()
    assert model.angles.x_leg_left_deg == 49.0
    assert model.angles.x_leg_right_deg == 49.0
    assert model.angles.x_included_deg == 98.0
    assert (
        model.angles.x_leg_left_deg + model.angles.x_leg_right_deg
        == model.angles.x_included_deg
    )


def test_source_dimensions_are_not_silently_mapped():
    model = get_martin_d28_1937_65260_reconstruction()
    assert model.unmapped_longitudinal_dimensions_in == (
        1.68,
        1.77,
        1.80,
        1.91,
        2.42,
        4.11,
        4.24,
        9.91,
        10.00,
        11.22,
        12.38,
    )


def test_unit_conversion():
    model = get_martin_d28_1937_65260_reconstruction()
    assert model.body_length_mm == 508.0
    assert round(model.upper_bout_width_mm, 2) == 297.18
    assert round(model.lower_bout_width_mm, 2) == 398.78
