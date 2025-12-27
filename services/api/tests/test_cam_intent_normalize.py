"""
CAM Intent Normalization Tests (H7.1.1)

Tests for normalize_cam_intent_v1() covering:
- Units conversion (inch <-> mm)
- Type coercion
- Issue detection
- Strict mode validation
"""
from __future__ import annotations

import pytest

from app.rmos.cam import (
    CamIntentIssue,
    CamIntentV1,
    CamIntentValidationError,
    CamModeV1,
    CamUnitsV1,
    normalize_cam_intent_v1,
)


@pytest.mark.unit
def test_normalize_router_3axis_passthrough_mm() -> None:
    """No conversion when units match (mm -> mm)."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        units=CamUnitsV1.MM,
        design={
            "geometry": {"type": "polyline", "points": [[0, 0], [10, 0], [10, 10]]},
            "depth_mm": 5.0,
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent, normalize_to_units=CamUnitsV1.MM)

    assert normalized.units == CamUnitsV1.MM
    assert normalized.design["depth_mm"] == 5.0
    pts = normalized.design["geometry"]["points"]
    assert pts == [[0, 0], [10, 0], [10, 10]]
    assert len([i for i in issues if i.code == "missing_field"]) == 0


@pytest.mark.unit
def test_normalize_router_3axis_inch_to_mm() -> None:
    """Convert inch design to mm."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        units=CamUnitsV1.INCH,
        design={
            "geometry": {"type": "polyline", "points": [[0, 0], [1, 0], [1, 1]]},
            "depth_mm": 0.5,
            "safe_z_mm": 0.25,
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent, normalize_to_units=CamUnitsV1.MM)

    assert normalized.units == CamUnitsV1.MM
    assert normalized.design["depth_mm"] == pytest.approx(0.5 * 25.4)
    assert normalized.design["safe_z_mm"] == pytest.approx(0.25 * 25.4)

    pts = normalized.design["geometry"]["points"]
    assert pts[1] == [pytest.approx(25.4), pytest.approx(0)]
    assert pts[2] == [pytest.approx(25.4), pytest.approx(25.4)]


@pytest.mark.unit
def test_normalize_router_3axis_mm_to_inch() -> None:
    """Convert mm design to inch."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        units=CamUnitsV1.MM,
        design={
            "geometry": {"type": "polyline", "points": [[0, 0], [25.4, 0]]},
            "depth_mm": 25.4,
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent, normalize_to_units=CamUnitsV1.INCH)

    assert normalized.units == CamUnitsV1.INCH
    assert normalized.design["depth_mm"] == pytest.approx(1.0)

    pts = normalized.design["geometry"]["points"]
    assert pts[1] == [pytest.approx(1.0), pytest.approx(0)]


@pytest.mark.unit
def test_normalize_router_3axis_missing_geometry_issue() -> None:
    """Missing geometry emits an issue (non-fatal)."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={"operation": "pocket"},  # no geometry
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    missing = [i for i in issues if i.code == "missing_field" and "geometry" in i.path]
    assert len(missing) == 1
    assert "geometry" in missing[0].message


@pytest.mark.unit
def test_normalize_router_3axis_strict_mode_fails() -> None:
    """Strict mode raises for missing recommended fields."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={"operation": "pocket"},  # no geometry
    )
    with pytest.raises(CamIntentValidationError) as exc_info:
        normalize_cam_intent_v1(intent, strict=True)

    assert "strict validation" in str(exc_info.value).lower()
    assert len(exc_info.value.issues) > 0


@pytest.mark.unit
def test_normalize_saw_basic() -> None:
    """Basic saw intent normalization."""
    intent = CamIntentV1(
        mode=CamModeV1.SAW,
        units=CamUnitsV1.INCH,
        design={
            "kerf_width_mm": 0.1,
            "stock_thickness_mm": 0.5,
            "cuts": [{"length_mm": 10, "depth_mm": 0.5}],
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent, normalize_to_units=CamUnitsV1.MM)

    assert normalized.units == CamUnitsV1.MM
    assert normalized.design["kerf_width_mm"] == pytest.approx(0.1 * 25.4)
    assert normalized.design["stock_thickness_mm"] == pytest.approx(0.5 * 25.4)
    assert normalized.design["cuts"][0]["length_mm"] == pytest.approx(10 * 25.4)


@pytest.mark.unit
def test_normalize_saw_missing_kerf_issue() -> None:
    """Missing kerf_width_mm emits issue."""
    intent = CamIntentV1(
        mode=CamModeV1.SAW,
        design={"stock_thickness_mm": 10},
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    kerf_issues = [i for i in issues if "kerf" in i.path]
    assert len(kerf_issues) == 1


@pytest.mark.unit
def test_normalize_saw_missing_stock_issue() -> None:
    """Missing stock_thickness_mm emits issue."""
    intent = CamIntentV1(
        mode=CamModeV1.SAW,
        design={"kerf_width_mm": 2.0},
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    stock_issues = [i for i in issues if "stock_thickness" in i.path]
    assert len(stock_issues) == 1


@pytest.mark.unit
def test_normalize_type_coercion_string_to_float() -> None:
    """Numeric strings are coerced to float."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={
            "geometry": {"type": "polyline", "points": [["0", "0"], ["10", "5"]]},
            "depth_mm": "3.5",
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    # depth should be coerced
    assert normalized.design["depth_mm"] == 3.5
    # points should be coerced
    pts = normalized.design["geometry"]["points"]
    assert pts[0] == [0.0, 0.0]
    assert pts[1] == [10.0, 5.0]


@pytest.mark.unit
def test_normalize_invalid_point_shape_issue() -> None:
    """Points with wrong shape emit issues."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={
            "geometry": {"type": "polyline", "points": [[0, 0], [1, 2, 3], [4, 5]]},
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    shape_issues = [i for i in issues if i.code == "shape_error"]
    assert len(shape_issues) == 1
    assert "point 1" in shape_issues[0].message

    # Valid points should still be preserved
    pts = normalized.design["geometry"]["points"]
    assert len(pts) == 2  # Only 2 valid points


@pytest.mark.unit
def test_normalize_preserves_extra_fields() -> None:
    """Extra fields in design are preserved (non-breaking)."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={
            "geometry": {"type": "rect", "width": 10, "height": 5},
            "custom_field": "preserved",
            "depth_mm": 2.0,
        },
    )
    normalized, issues = normalize_cam_intent_v1(intent)

    assert normalized.design["custom_field"] == "preserved"
    assert normalized.design["geometry"]["type"] == "rect"


@pytest.mark.unit
def test_normalize_invalid_geometry_type_raises() -> None:
    """Non-dict geometry raises fatal error."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={"geometry": "invalid_string"},
    )
    with pytest.raises(CamIntentValidationError) as exc_info:
        normalize_cam_intent_v1(intent)

    assert "geometry must be" in str(exc_info.value).lower()


@pytest.mark.unit
def test_normalize_invalid_cuts_type_raises() -> None:
    """Non-list cuts raises fatal error."""
    intent = CamIntentV1(
        mode=CamModeV1.SAW,
        design={"kerf_width_mm": 2.0, "stock_thickness_mm": 10, "cuts": "invalid"},
    )
    with pytest.raises(CamIntentValidationError) as exc_info:
        normalize_cam_intent_v1(intent)

    assert "cuts must be" in str(exc_info.value).lower()


@pytest.mark.unit
def test_cam_intent_issue_dataclass() -> None:
    """CamIntentIssue is a proper frozen dataclass."""
    issue = CamIntentIssue(code="test_code", message="Test message", path="test.path")
    assert issue.code == "test_code"
    assert issue.message == "Test message"
    assert issue.path == "test.path"

    # Frozen
    with pytest.raises(Exception):
        issue.code = "modified"  # type: ignore


@pytest.mark.unit
def test_normalize_returns_new_intent() -> None:
    """Normalization returns a new intent, doesn't mutate original."""
    original_design = {
        "geometry": {"type": "polyline", "points": [[0, 0], [1, 0]]},
        "depth_mm": 1.0,
    }
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        units=CamUnitsV1.INCH,
        design=original_design.copy(),
    )
    original_depth = intent.design["depth_mm"]

    normalized, _ = normalize_cam_intent_v1(intent, normalize_to_units=CamUnitsV1.MM)

    # Original should be unchanged
    assert intent.design["depth_mm"] == original_depth
    # Normalized should be different
    assert normalized.design["depth_mm"] != original_depth
