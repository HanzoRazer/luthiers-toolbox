"""
CAM Intent Schema Freeze Tests

Contract freeze guard - ensures CamIntentV1 schema doesn't drift without
explicit version bump.
"""
from __future__ import annotations

import pytest

from app.rmos.cam.schemas_intent import (
    CamIntentV1,
    CamModeV1,
    CamUnitsV1,
    assert_cam_intent_schema_frozen_v1,
    cam_intent_schema_hash_v1,
)


@pytest.mark.unit
def test_cam_intent_schema_is_frozen_v1() -> None:
    """
    Contract freeze guard.

    This test fails if the JSON schema for CamIntentV1 changes without updating
    the pinned hash constant.
    """
    assert_cam_intent_schema_frozen_v1()


@pytest.mark.unit
def test_cam_intent_v1_minimal_valid() -> None:
    """Test that minimal valid intent can be constructed."""
    intent = CamIntentV1(
        mode=CamModeV1.ROUTER_3AXIS,
        design={"geometry": {"type": "rect", "width": 10, "height": 5}},
    )
    assert intent.schema_version == "cam_intent_v1"
    assert intent.mode == CamModeV1.ROUTER_3AXIS
    assert intent.units == CamUnitsV1.MM  # default
    assert intent.design == {"geometry": {"type": "rect", "width": 10, "height": 5}}
    assert intent.context == {}
    assert intent.options == {}


@pytest.mark.unit
def test_cam_intent_v1_full_valid() -> None:
    """Test that full intent with all fields can be constructed."""
    intent = CamIntentV1(
        intent_id="test_intent_001",
        mode=CamModeV1.SAW,
        units=CamUnitsV1.INCH,
        tool_id="blade_001",
        material_id="maple_hard",
        machine_id="saw_station_1",
        design={"kerf_width_mm": 2.0, "cuts": [{"type": "rip"}]},
        context={"max_feed_rate": 100},
        options={"preview": True},
        requested_by="test_user",
    )
    assert intent.intent_id == "test_intent_001"
    assert intent.mode == CamModeV1.SAW
    assert intent.units == CamUnitsV1.INCH
    assert intent.tool_id == "blade_001"


@pytest.mark.unit
def test_cam_intent_schema_hash_is_stable() -> None:
    """Test that schema hash is deterministic."""
    hash1 = cam_intent_schema_hash_v1()
    hash2 = cam_intent_schema_hash_v1()
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex
