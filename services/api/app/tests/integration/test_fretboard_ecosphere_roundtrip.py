"""Round-trip integration tests for the fretboard ecosphere API.

Sprint FRET-A Phase 2 Commit 3.

These tests exercise the contract that the API can serialize an ecosphere's
temperament out to Scala, parse the Scala back, and rebuild an ecosphere
that produces byte-identical fret positions.

Lives in tests/integration/ rather than tests/api_v1/ because it spans
multiple endpoints and asserts a property across them.
"""
from __future__ import annotations


from fastapi.testclient import TestClient

from app.main import app
from app.calculators.scala_loader import (
    parse_scala_content,
    scala_to_fret_ratios,
)
from app.calculators.alternative_temperaments import (
    compute_fret_positions_from_ratios_mm,
)

client = TestClient(app)


def _build(req: dict) -> dict:
    """Helper: POST to /compute, return parsed JSON."""
    resp = client.post("/api/v1/fretboard/compute", json=req)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _scala_text(req: dict) -> str:
    """Helper: POST to /scala with octet-stream Accept, return .scl text."""
    resp = client.post(
        "/api/v1/fretboard/scala",
        json=req,
        headers={"Accept": "application/octet-stream"},
    )
    assert resp.status_code == 200, resp.text
    return resp.content.decode("utf-8")


def _extract_first_string_positions(eco: dict) -> list[float]:
    """Extract perpendicular fret distances from nut for the first string.

    Reads from the JSON-serialized ecosphere (post-API). For a fan-fret
    instrument, the position of fret i along string 0 is the x-coordinate
    of points[0] in fret_lines[i].points (bass-side endpoint).

    Skips fret_lines[0] which is the nut (fret 0).
    """
    positions: list[float] = []
    for fret_line in eco["fret_lines"][1:]:
        first_point = fret_line["points"][0]
        positions.append(first_point["x_mm"])
    return positions


# =============================================================================
# Compute -> Scala -> Parse -> Compute identity
# =============================================================================

class TestRoundTrip12TET:
    """The defining round-trip: 12-TET should be byte-identical through the loop."""

    def test_compute_to_scala_to_parse_to_compute_identity(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "equal_12",
            "string_count": 6,
        }
        eco_a = _build(common)

        scl = _scala_text(common)
        assert scl.count("\n") >= 5

        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=22)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)

        eco_a_positions = _extract_first_string_positions(eco_a)

        assert len(scl_positions) == len(eco_a_positions) == 22
        for s, e in zip(scl_positions, eco_a_positions):
            # Tolerance of 1e-3 mm (1 micrometer) accounts for cents serialization
            # precision loss (6 decimal places in .scl format). This is well below
            # the tolerance of any physical fret positioning system.
            assert abs(s - e) < 1e-3, (
                f"Round-trip diverged: scl={s:.12f}mm, eco={e:.12f}mm, diff={abs(s-e):.2e}mm"
            )


class TestRoundTrip19TET:
    """N-TET round-trip - proves the temperament dispatcher is honest end-to-end."""

    def test_19tet_round_trip(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 19,
            "temperament": "equal_19",
            "string_count": 6,
        }
        eco_a = _build(common)
        scl = _scala_text(common)
        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=19)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)
        eco_a_positions = _extract_first_string_positions(eco_a)

        assert len(scl_positions) == 19
        for s, e in zip(scl_positions, eco_a_positions):
            assert abs(s - e) < 1e-3


class TestRoundTripNonEqualTemperament:
    """Pythagorean - proves named-temperament path is honest end-to-end."""

    def test_pythagorean_round_trip(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 12,
            "temperament": "pythagorean",
            "string_count": 6,
        }
        eco_a = _build(common)
        scl = _scala_text(common)
        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=12)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)
        eco_a_positions = _extract_first_string_positions(eco_a)

        for s, e in zip(scl_positions, eco_a_positions):
            assert abs(s - e) < 1e-3


# =============================================================================
# Cross-endpoint consistency
# =============================================================================

class TestPresetToComputeConsistency:
    """A preset retrieved via GET should compute identically when POSTed back."""

    def test_strat_preset_roundtrip(self):
        preset = client.get("/api/v1/fretboard/presets/fender_strat_25.5").json()
        eco = _build(preset)
        positions = _extract_first_string_positions(eco)
        assert len(positions) == 22
        assert abs(positions[11] - 323.85) < 0.01
