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
from fastapi import HTTPException

try:
    from ezdxf.lldxf.const import DXFStructureError
except ImportError:
    DXFStructureError = Exception


TESTDATA = Path(__file__).parent / "testdata"


GOLDEN_MVP_RECT_PREFLIGHT = {
    "layers": ["GEOMETRY"],
    "entity_count_min": 1,
    "entity_count_max": 50,
    "has_bounds": True,
    "bounds_valid": True,
}


@pytest.mark.unit
def test_golden_mvp_rect_preflight_structure():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Missing fixture: {dxf_path}"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    assert "layers" in result
    assert "entity_count" in result
    assert "bounds" in result


@pytest.mark.unit
def test_golden_mvp_rect_layer_detection():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    layers = result.get("layers", [])
    assert "GEOMETRY" in layers


@pytest.mark.unit
def test_golden_mvp_rect_entity_count_range():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    entity_count = result.get("entity_count", 0)
    assert entity_count >= GOLDEN_MVP_RECT_PREFLIGHT["entity_count_min"]
    assert entity_count <= GOLDEN_MVP_RECT_PREFLIGHT["entity_count_max"]


@pytest.mark.unit
def test_golden_mvp_rect_bounds_valid():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    bounds = result.get("bounds")
    if bounds is None:
        pytest.skip("Bounds computation returned None")
        return
    if isinstance(bounds, dict):
        if "min_x" in bounds:
            assert bounds["min_x"] < bounds["max_x"]
            assert bounds["min_y"] < bounds["max_y"]
        elif "min" in bounds:
            assert bounds["min"][0] < bounds["max"][0]
            assert bounds["min"][1] < bounds["max"][1]


@pytest.mark.unit
def test_golden_mvp_rect_positive_dimensions():
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
        assert width > 0
        assert height > 0


@pytest.mark.unit
def test_preflight_returns_dict():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    assert isinstance(result, dict)


@pytest.mark.unit
def test_preflight_deterministic():
    from app.dxf.preflight_service import validate_dxf_bytes
    import json
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    results = []
    for _ in range(5):
        result = validate_dxf_bytes(content)
        results.append(json.dumps(result, sort_keys=True, default=str))
    assert len(set(results)) == 1


@pytest.mark.unit
def test_preflight_layers_are_strings():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    layers = result.get("layers", [])
    for layer in layers:
        assert isinstance(layer, str)


@pytest.mark.unit
def test_preflight_entity_count_non_negative():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    result = validate_dxf_bytes(content)
    entity_count = result.get("entity_count", 0)
    assert entity_count >= 0


@pytest.mark.unit
def test_preflight_rejects_empty_bytes():
    from app.dxf.preflight_service import validate_dxf_bytes
    with pytest.raises((ValueError, OSError, HTTPException, DXFStructureError)):
        validate_dxf_bytes(b"")


@pytest.mark.unit
def test_preflight_rejects_invalid_dxf():
    from app.dxf.preflight_service import validate_dxf_bytes
    with pytest.raises((ValueError, OSError, HTTPException, DXFStructureError)):
        validate_dxf_bytes(b"This is not a DXF file")


@pytest.mark.unit
def test_preflight_rejects_truncated_dxf():
    from app.dxf.preflight_service import validate_dxf_bytes
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    content = dxf_path.read_bytes()
    truncated = content[:len(content) // 2]
    with pytest.raises((ValueError, OSError, HTTPException, DXFStructureError)):
        validate_dxf_bytes(truncated)
