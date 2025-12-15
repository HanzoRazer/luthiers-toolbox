# services/api/app/tests/test_tool_profiles.py

"""
Tool & Material Profile tests (Wave 6).

Tests that:
- The library loads and resolves profiles
- Helpers return correct defaults and overrides
"""

from __future__ import annotations

import pytest

from app.data.tool_library import (
    load_tool_library,
    get_tool_profile,
    get_material_profile,
    reset_cache,
)
from app.calculators.tool_profiles import (
    resolve_flute_count,
    resolve_chipload_band,
    resolve_heat_weight_for_material,
)


@pytest.fixture(autouse=True)
def reset_library_cache():
    """Reset the library cache before each test."""
    reset_cache()
    yield
    reset_cache()


def test_tool_library_loads():
    """Test that the tool library loads without error."""
    lib = load_tool_library()
    assert lib is not None


def test_tool_profile_lookup():
    """Test that existing tools can be looked up."""
    # flat_6.0 exists in tool_library.json
    tp = get_tool_profile("flat_6.0")
    assert tp is not None
    assert tp.flutes == 2
    assert tp.diameter_mm == 6.0
    assert tp.chipload_min_mm < tp.chipload_max_mm


def test_tool_profile_missing():
    """Test that missing tools return None."""
    tp = get_tool_profile("nonexistent_tool_xyz")
    assert tp is None


def test_material_profile_lookup():
    """Test that existing materials can be looked up."""
    # Ebony exists in tool_library.json
    mp = get_material_profile("Ebony")
    assert mp is not None
    assert mp.heat_sensitivity in ("low", "medium", "high")


def test_material_profile_case_insensitive():
    """Test case-insensitive material lookup."""
    mp1 = get_material_profile("Ebony")
    mp2 = get_material_profile("ebony")
    assert mp1 is not None
    assert mp2 is not None


def test_material_profile_missing():
    """Test that missing materials return None."""
    mp = get_material_profile("nonexistent_material_xyz")
    assert mp is None


def test_resolve_flute_count_known_tool():
    """Test flute count resolution for known tool."""
    flutes = resolve_flute_count("flat_6.0", default=4)
    assert flutes == 2  # From JSON


def test_resolve_flute_count_unknown_tool():
    """Test flute count resolution falls back to default."""
    flutes = resolve_flute_count("unknown_tool", default=4)
    assert flutes == 4


def test_resolve_chipload_band_known_tool():
    """Test chipload band resolution for known tool."""
    cmin, cmax = resolve_chipload_band("flat_6.0")
    assert cmin > 0
    assert cmax > cmin


def test_resolve_chipload_band_unknown_tool():
    """Test chipload band resolution falls back to defaults."""
    cmin, cmax = resolve_chipload_band(
        "unknown_tool",
        default_min=0.02,
        default_max=0.05
    )
    assert cmin == 0.02
    assert cmax == 0.05


def test_resolve_heat_weight_high_sensitivity():
    """Test heat weight for high-sensitivity material."""
    weight = resolve_heat_weight_for_material("Ebony")
    assert weight >= 1.0  # Ebony is hard = high sensitivity


def test_resolve_heat_weight_unknown_material():
    """Test heat weight for unknown material returns 1.0."""
    weight = resolve_heat_weight_for_material("unknown_wood")
    assert weight == 1.0
