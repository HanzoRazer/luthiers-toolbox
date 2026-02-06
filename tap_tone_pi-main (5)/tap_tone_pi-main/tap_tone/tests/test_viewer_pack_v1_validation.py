"""Regression tests for viewer_pack_v1 validation.

These tests use fixture directories with known-good and known-bad packs
to ensure specific validation rules fire correctly.

Rule ID Reference:
    M-001  Manifest existence (viewer_pack.json)
    S-006  Frequency grid mismatch between points
    P-003  Peak frequency not aligned to spectrum grid
    W-001  WSI curve missing required columns
    W-003  WSI frequency grid mismatch vs spectrum
"""
from __future__ import annotations

from pathlib import Path

from tap_tone.validate.viewer_pack_v1 import validate_pack


FIXTURES = Path(__file__).parent / "fixtures" / "viewer_pack_v1"


def _fixture(name: str) -> Path:
    p = FIXTURES / name
    assert p.exists(), f"Missing fixture directory: {p}"
    return p


def _error_rules(report) -> set[str]:
    return {
        e.get("rule")
        for e in (report.errors or [])
        if isinstance(e, dict) and isinstance(e.get("rule"), str)
    }


def test_good_minimal_passes():
    report = validate_pack(_fixture("good_minimal"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is True
    assert len(report.errors) == 0


def test_missing_manifest_fails():
    report = validate_pack(_fixture("bad_missing_manifest"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is False
    assert "M-001" in _error_rules(report)


def test_freq_grid_mismatch_fails():
    report = validate_pack(_fixture("bad_freq_grid_mismatch"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is False
    assert "S-006" in _error_rules(report)


def test_peak_off_grid_fails():
    report = validate_pack(_fixture("bad_peak_off_grid"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is False
    assert "P-003" in _error_rules(report)


def test_bad_wsi_header_fails():
    report = validate_pack(_fixture("bad_wsi_header"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is False
    assert "W-001" in _error_rules(report)


def test_wsi_freq_grid_mismatch_fails():
    report = validate_pack(_fixture("bad_wsi_freq_grid_mismatch"), peak_tolerance_hz=0.0, audio_required=False)
    assert report.passed is False
    assert "W-003" in _error_rules(report)
