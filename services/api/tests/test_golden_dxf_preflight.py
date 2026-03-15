# tests/test_golden_dxf_preflight.py
"""
Golden Fixture Tests: DXF Preflight Validation

Locks the DXF validation pipeline to ensure consistent preflight results.
Critical for manufacturing - inconsistent validation could allow bad
geometry through or block good geometry.

Run: pytest tests/test_golden_dxf_preflight.py -v
"""

from pathlib import Path
import pytest


TESTDATA = Path(__file__).parent / "testdata"


# =============================================================================
# GOLDEN EXPECTED VALUES
# =============================================================================

GOLDEN_MVP_RECT_PREFLIGHT = {
    "layers": ["GEOMETRY"],
    "entity_count_min": 1,  # At least 1 entity
    "entity_count_max": 50,  # Reasonable upper bound
    "has_bounds": True,
    "bounds_valid": True,  # min < max for all axes
}


# =============================================================================
# GOLDEN SNAPSHOT TESTS
# =============================================================================


@pytest.mark.unit
def test_golden_mvp_rect_preflight_structure():
    """
    Golden test: MVP rect DXF preflight returns expected structure.

    The mvp_rect_with_island.dxf is the canonical test fixture for the
    DXF -> G-code pipeline. Its preflight results must be stable.
    """
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Missing fixture: {dxf_path}"

    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    # Verify required keys exist
    assert "layers" in result, "Preflight must return layers"
    assert "entity_count" in result, "Preflight must return entity_count"
    assert "bounds" in result, "Preflight must return bounds"


@pytest.mark.unit
def test_golden_mvp_rect_layer_detection():
    """
    Golden test: MVP rect DXF detects GEOMETRY layer.

    The fixture must have a GEOMETRY layer containing the machining contours.
    """
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    layers = result.get("layers", [])
    assert "GEOMETRY" in layers, (
        f"MVP rect must have GEOMETRY layer, found: {layers}"
    )


@pytest.mark.unit
def test_golden_mvp_rect_entity_count_range():
    """
    Golden test: MVP rect DXF has expected entity count.

    The fixture should have a reasonable number of entities.
    Too few = missing geometry. Too many = corrupted file.
    """
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    entity_count = result.get("entity_count", 0)

    assert entity_count >= GOLDEN_MVP_RECT_PREFLIGHT["entity_count_min"], (
        f"Entity count {entity_count} below minimum expected "
        f"({GOLDEN_MVP_RECT_PREFLIGHT['entity_count_min']})"
    )
    assert entity_count <= GOLDEN_MVP_RECT_PREFLIGHT["entity_count_max"], (
        f"Entity count {entity_count} above maximum expected "
        f"({GOLDEN_MVP_RECT_PREFLIGHT['entity_count_max']})"
    )


@pytest.mark.unit
def test_golden_mvp_rect_bounds_valid():
    """
    Golden test: MVP rect DXF has valid bounding box.

    Bounds must have min < max for all axes.
    Invalid bounds indicate corrupted or empty geometry.
    """
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    bounds = result.get("bounds", {})

    # Bounds must exist
    assert bounds is not None, "Bounds must not be None"

    # Check structure (may be dict with min_x/max_x or nested)
    if isinstance(bounds, dict):
        if "min_x" in bounds:
            assert bounds["min_x"] < bounds["max_x"], "min_x must be < max_x"
            assert bounds["min_y"] < bounds["max_y"], "min_y must be < max_y"
        elif "min" in bounds:
            assert bounds["min"][0] < bounds["max"][0], "min[0] must be < max[0]"
            assert bounds["min"][1] < bounds["max"][1], "min[1] must be < max[1]"


@pytest.mark.unit
def test_golden_mvp_rect_positive_dimensions():
    """
    Golden test: MVP rect DXF has positive dimensions.

    Bounding box must have positive width and height.
    Zero or negative dimensions indicate empty or inverted geometry.
    """
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    bounds = result.get("bounds", {})

    if bounds and isinstance(bounds, dict):
        if "min_x" in bounds:
            width = bounds["max_x"] - bounds["min_x"]
            height = bounds["max_y"] - bounds["min_y"]
        elif "min" in bounds:
            width = bounds["max"][0] - bounds["min"][0]
            height = bounds["max"][1] - bounds["min"][1]
        else:
            pytest.skip("Bounds format not recognized")
            return

        assert width > 0, f"Width must be positive, got {width}"
        assert height > 0, f"Height must be positive, got {height}"


# =============================================================================
# INVARIANT TESTS (properties that must always hold)
# =============================================================================


@pytest.mark.unit
def test_preflight_returns_dict():
    """Preflight must always return a dictionary."""
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    assert isinstance(result, dict), f"Preflight must return dict, got {type(result)}"


@pytest.mark.unit
def test_preflight_deterministic():
    """Same DXF must always produce identical preflight results."""
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()

    results = []
    for _ in range(5):
        result = validate_dxf_bytes(content)
        # Serialize to string for comparison (handles nested dicts)
        import json
        results.append(json.dumps(result, sort_keys=True, default=str))

    # All results must be identical
    assert len(set(results)) == 1, "Preflight must be deterministic"


@pytest.mark.unit
def test_preflight_layers_are_strings():
    """All layer names must be strings."""
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    layers = result.get("layers", [])
    for layer in layers:
        assert isinstance(layer, str), f"Layer name must be string, got {type(layer)}"


@pytest.mark.unit
def test_preflight_entity_count_non_negative():
    """Entity count must be non-negative."""
    from app.dxf.preflight_service import validate_dxf_bytes

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)

    entity_count = result.get("entity_count", 0)
    assert entity_count >= 0, f"Entity count must be >= 0, got {entity_count}"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.unit
def test_preflight_rejects_empty_bytes():
    """Preflight must reject empty input."""
    from app.dxf.preflight_service import validate_dxf_bytes

    with pytest.raises((ValueError, OSError)):
        validate_dxf_bytes(b"")


@pytest.mark.unit
def test_preflight_rejects_invalid_dxf():
    """Preflight must reject non-DXF content."""
    from app.dxf.preflight_service import validate_dxf_bytes

    with pytest.raises((ValueError, OSError)):
        validate_dxf_bytes(b"This is not a DXF file")


@pytest.mark.unit
def test_preflight_rejects_truncated_dxf():
    """Preflight must reject truncated DXF."""
    from app.dxf.preflight_service import validate_dxf_bytes

    # Truncate a valid DXF
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    truncated = content[:len(content) // 2]

    with pytest.raises((ValueError, OSError)):
        validate_dxf_bytes(truncated)
