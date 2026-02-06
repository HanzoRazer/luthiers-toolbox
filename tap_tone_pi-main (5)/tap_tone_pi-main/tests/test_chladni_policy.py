"""Tests for Chladni frequency mismatch policy (G.2)."""
from __future__ import annotations
import pytest

from modes.chladni.index_patterns import attach_pattern_record, finalize_run


def test_chladni_tolerance_warn_and_pass(monkeypatch):
    """Delta within tolerance: warn but pass."""
    monkeypatch.setenv("CHLADNI_FREQ_TOLERANCE_HZ", "5.0")
    peaks = [148.0, 226.0]
    rec = {"freq_hz": 148, "image_path": "F0148.png", "image_freq_tag_hz": 150.0}
    d = attach_pattern_record(rec, peaks)
    
    # Delta should be 2.0 (150 - 148)
    assert 0 < d <= 5.0
    assert rec["nearest_detected_hz"] == 148.0
    assert rec["delta_hz"] == 2.0
    
    run = {
        "schema_id": "chladni_run",
        "schema_version": "1.0",
        "artifact_type": "chladni_run",
        "created_utc": "2026-01-01T00:00:00Z",
        "plate_id": "X",
        "environment": {"temp_C": None, "rh_pct": None},
        "excitation": {"mode": "sine"},
        "peaks_hz": peaks,
        "patterns": [rec],
        "provenance": {"peaks_json_path": "p.json", "peaks_sha256": "a" * 64}
    }
    # Should not raise
    finalize_run(run, tolerance_hz=5.0)
    assert run["_policy"]["worst_delta_hz"] == 2.0


def test_chladni_tolerance_exceeds_and_fails(monkeypatch):
    """Delta exceeds tolerance: must fail with SystemExit(2)."""
    monkeypatch.setenv("CHLADNI_FREQ_TOLERANCE_HZ", "3.0")
    peaks = [148.0]
    rec = {"freq_hz": 148, "image_path": "F0148.png", "image_freq_tag_hz": 154.0}
    attach_pattern_record(rec, peaks)
    
    # Delta = 6.0 (154 - 148), exceeds tolerance of 3.0
    assert rec["delta_hz"] == 6.0
    
    run = {
        "schema_id": "chladni_run",
        "schema_version": "1.0",
        "artifact_type": "chladni_run",
        "created_utc": "2026-01-01T00:00:00Z",
        "plate_id": "X",
        "environment": {"temp_C": None, "rh_pct": None},
        "excitation": {"mode": "sine"},
        "peaks_hz": peaks,
        "patterns": [rec],
        "provenance": {"peaks_json_path": "p.json", "peaks_sha256": "a" * 64}
    }
    
    with pytest.raises(SystemExit) as exc_info:
        finalize_run(run, tolerance_hz=3.0)
    assert exc_info.value.code == 2


def test_chladni_no_peaks_detected():
    """When no peaks detected, nearest is None, delta based on image tag only."""
    rec = {"freq_hz": 200, "image_path": "F0200.png", "image_freq_tag_hz": 200.0}
    d = attach_pattern_record(rec, [])
    
    assert rec["nearest_detected_hz"] is None
    assert d == 0.0  # No reference to compare against


def test_chladni_exact_match():
    """Exact frequency match: delta should be 0."""
    peaks = [148.0, 226.0, 300.0]
    rec = {"freq_hz": 226, "image_path": "F0226.png", "image_freq_tag_hz": 226.0}
    d = attach_pattern_record(rec, peaks)
    
    assert d == 0.0
    assert rec["nearest_detected_hz"] == 226.0
    assert "_warnings" not in rec  # No warning for exact match
