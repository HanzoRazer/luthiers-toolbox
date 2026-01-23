"""
Unit tests for PATCH-001: Fret Math Intonation Model

Tests verify:
1. Default behavior (12-TET) is unchanged
2. custom_ratios path uses per-fret ratios
3. Named ratio sets are rejected for CAM export (must be expanded to per-fret first)
"""

import pytest
from unittest.mock import patch, MagicMock
from app.schemas.cam_fret_slots import FretSlotExportRequest
from app.calculators.fret_slots_export import export_fret_slots


def _base_req_kwargs():
    """Base kwargs for FretSlotExportRequest tests."""
    return {
        "scale_length_mm": 648.0,
        "fret_count": 22,
        "nut_width_mm": 42.0,
        "heel_width_mm": 56.0,
        "slot_depth_mm": 2.0,
        "slot_width_mm": 0.6,
    }


def test_fret_slots_default_12tet_calls_compute_fret_positions_mm():
    """Verifies default behavior is unchanged: equal_temperament_12 uses compute_fret_positions_mm()."""
    with patch("app.calculators.fret_slots_export.compute_fret_positions_mm") as mock_12tet:
        mock_12tet.return_value = [36.0, 70.0, 102.0]  # Stub positions for 3 frets

        request = FretSlotExportRequest(
            scale_length_mm=648.0,
            fret_count=3,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_depth_mm=2.0,
            slot_width_mm=0.6,
            # intonation_model defaults to "equal_temperament_12"
        )

        try:
            export_fret_slots(request)
        except Exception:
            pass  # We only care that the right function was called

        mock_12tet.assert_called_once()
        call_args = mock_12tet.call_args
        assert call_args[1]["scale_length_mm"] == 648.0
        assert call_args[1]["fret_count"] == 3


def test_fret_slots_custom_ratios_uses_per_fret_ratios():
    """Verifies opt-in custom_ratios path uses compute_fret_positions_from_ratios_mm()."""
    with patch("app.calculators.fret_slots_export.compute_fret_positions_from_ratios_mm") as mock_ratios:
        mock_ratios.return_value = [36.0, 70.0, 102.0]  # Stub positions for 3 frets

        per_fret_ratios = [1.0594630943592953, 1.122462048309373, 1.189207115002721]

        request = FretSlotExportRequest(
            scale_length_mm=648.0,
            fret_count=3,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_depth_mm=2.0,
            slot_width_mm=0.6,
            intonation_model="custom_ratios",
            ratios=per_fret_ratios,
        )

        try:
            export_fret_slots(request)
        except Exception:
            pass  # We only care that the right function was called

        mock_ratios.assert_called_once()
        call_args = mock_ratios.call_args
        assert call_args.kwargs["scale_length_mm"] == 648.0
        assert call_args.kwargs["ratios"] == per_fret_ratios


def test_fret_slots_custom_ratios_requires_ratios_or_ratio_set_id():
    """Verifies custom_ratios requires either ratios[] or ratio_set_id."""
    with pytest.raises(ValueError, match="custom_ratios requires ratio_set_id or ratios"):
        FretSlotExportRequest(
            scale_length_mm=648.0,
            fret_count=3,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_depth_mm=2.0,
            slot_width_mm=0.6,
            intonation_model="custom_ratios",
            # Neither ratios nor ratio_set_id provided
        )


def test_fret_slots_ratios_length_must_match_fret_count():
    """Verifies ratios[] length validation."""
    with pytest.raises(ValueError, match="ratios.*must have len == fret_count"):
        FretSlotExportRequest(
            scale_length_mm=648.0,
            fret_count=3,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_depth_mm=2.0,
            slot_width_mm=0.6,
            intonation_model="custom_ratios",
            ratios=[1.05, 1.12],  # Only 2 ratios for 3 frets
        )


def test_fret_slots_ratios_must_be_greater_than_one():
    """Verifies all ratios must be > 1.0 for fretted notes."""
    with pytest.raises(ValueError, match="must be > 1.0"):
        FretSlotExportRequest(
            scale_length_mm=648.0,
            fret_count=3,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_depth_mm=2.0,
            slot_width_mm=0.6,
            intonation_model="custom_ratios",
            ratios=[1.0, 1.12, 1.19],  # First ratio is exactly 1.0 (invalid)
        )


def test_fret_slots_ratio_set_rejected_when_not_per_fret_list():
    """Verifies ratio_set_id is rejected at CAM export - must provide explicit ratios[].

    Named ratio sets (JUST_MAJOR, PYTHAGOREAN, MEANTONE) are scale-degree-based
    and require musical context. CAM export requires explicit per-fret ratios
    to prevent accidental key-locked fretboards.
    """
    # Schema allows ratio_set_id, but export rejects it
    request = FretSlotExportRequest(
        scale_length_mm=648.0,
        fret_count=22,
        nut_width_mm=42.0,
        heel_width_mm=56.0,
        slot_depth_mm=2.0,
        slot_width_mm=0.6,
        intonation_model="custom_ratios",
        ratio_set_id="JUST_MAJOR",  # Named set, not per-fret list
        # ratios not provided
    )

    with pytest.raises(ValueError) as ei:
        export_fret_slots(request)

    msg = str(ei.value)
    # Assert the error message is explicit and actionable
    assert "ratio_set_id='JUST_MAJOR'" in msg
    assert "does not provide per-fret ratios" in msg
    assert "observed length=0" in msg
    assert "length == fret_count (22)" in msg


def test_ratio_set_rejection_includes_template_hint_in_dev_mode(monkeypatch):
    """In dev/test mode, error message should suggest the ratios_template.json path.

    Keep this out of production unless explicitly in dev/test/DEBUG.
    """
    monkeypatch.setenv("APP_ENV", "test")

    request = FretSlotExportRequest(
        **_base_req_kwargs(),
        intonation_model="custom_ratios",
        ratio_set_id="JUST_MAJOR",
    )

    with pytest.raises(ValueError) as ei:
        export_fret_slots(request)

    msg = str(ei.value)
    assert "docs/tests/ratios_template.json" in msg
