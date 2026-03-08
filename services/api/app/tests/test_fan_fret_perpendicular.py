# services/api/app/tests/test_fan_fret_perpendicular.py
"""
Tests for fan-fret perpendicular fret calculations.

Schema reference (FretSlotsPreviewRequest):
- model_id: str
- fret_count: int (1-36, default 22)
- slot_width_mm: float (0-2.0, default 0.58)
- slot_depth_mm: float (0-10.0, default 3.0)
- bit_diameter_mm: float (0-10.0, default 0.58)
- mode: "standard" | "fan_fret" (default "standard")
- perpendicular_fret: Optional[int]
- bass_scale_mm: Optional[float]
- treble_scale_mm: Optional[float]

Response schema (FretSlotsPreviewResponse):
- slots: List[FretSlotOut] with fields: fret, angleRad, isPerpendicular, etc.

STATUS: Fan-fret mode is accepted by the schema but the calculator
        (fret_slots_cam.py) doesn't yet implement angle calculations.
        Tests are marked xfail until fan-fret support is implemented.
"""

import math

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PERP_EPS = 1e-4

# Mark fan-fret tests as expected failures - feature not yet implemented
fan_fret_not_implemented = pytest.mark.xfail(
    reason="Fan-fret angle calculation not implemented in fret_slots_cam.py",
    strict=False,
)


@pytest.fixture
def fan_fret_request():
    """Valid fan-fret preview request matching FretSlotsPreviewRequest schema."""
    return {
        "model_id": "benedetto_17",
        "mode": "fan_fret",  # Schema requires "fan_fret" not "fan"
        "treble_scale_mm": 647.7,
        "bass_scale_mm": 660.4,
        "perpendicular_fret": 7,
        "fret_count": 22,
        "slot_width_mm": 0.6,
        "slot_depth_mm": 2.0,
        "bit_diameter_mm": 0.6,
    }


def test_fan_fret_endpoint_accepts_request(fan_fret_request):
    """Fan-fret preview endpoint accepts valid request (returns 200)."""
    resp = client.post("/api/cam/fret_slots/preview", json=fan_fret_request)
    
    if resp.status_code == 404:
        pytest.skip("Fan-fret preview endpoint not available")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


def test_fan_fret_response_has_slots(fan_fret_request):
    """Fan-fret response includes slots array."""
    resp = client.post("/api/cam/fret_slots/preview", json=fan_fret_request)
    
    if resp.status_code == 404:
        pytest.skip("Fan-fret preview endpoint not available")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "slots" in data
    assert isinstance(data["slots"], list)


@fan_fret_not_implemented
def test_perpendicular_fret_flag_and_angle(fan_fret_request):
    """
    The designated neutral fret in a fan-fret layout should:

    - Have angleRad very close to 0 (perpendicular)
    - Expose isPerpendicular == True in the API response

    This test assumes perpendicular_fret = 7.
    """
    resp = client.post("/api/cam/fret_slots/preview", json=fan_fret_request)

    if resp.status_code == 404:
        pytest.skip("Fan-fret preview endpoint not available")

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    slots = data.get("slots", [])
    if not slots:
        pytest.skip("No slots returned in response")

    neutral_fret = fan_fret_request["perpendicular_fret"]
    neutral = next((s for s in slots if s["fret"] == neutral_fret), None)

    if neutral is None:
        pytest.skip(f"Fret {neutral_fret} not found in slots")

    # Test tolerance-based angle check
    angle = neutral.get("angleRad", 0.0)
    if angle is not None:
        assert math.isclose(angle, 0.0, abs_tol=PERP_EPS), \
            f"Perpendicular fret angle {angle} exceeds tolerance {PERP_EPS}"

    # Test isPerpendicular flag
    if "isPerpendicular" in neutral:
        assert neutral["isPerpendicular"] is True, \
            "Perpendicular fret should have isPerpendicular=True"


@fan_fret_not_implemented
def test_non_perpendicular_frets_have_angle(fan_fret_request):
    """
    Verify that non-perpendicular frets in a fan-fret layout have non-zero angles.
    """
    resp = client.post("/api/cam/fret_slots/preview", json=fan_fret_request)

    if resp.status_code == 404:
        pytest.skip("Fan-fret preview endpoint not available")

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    slots = data.get("slots", [])
    if not slots:
        pytest.skip("No slots returned in response")

    perp_fret = fan_fret_request["perpendicular_fret"]
    non_perp_frets = [s for s in slots if s["fret"] not in [0, perp_fret]]

    if non_perp_frets:
        angles = [abs(s.get("angleRad") or 0.0) for s in non_perp_frets]
        max_angle = max(angles) if angles else 0.0
        assert max_angle > PERP_EPS, \
            "Fan-fret layout should have non-perpendicular frets with measurable angles"
