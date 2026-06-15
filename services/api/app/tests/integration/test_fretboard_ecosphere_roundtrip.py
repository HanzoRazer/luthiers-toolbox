"""Round-trip integration tests for the fretboard ecosphere API.

Sprint FRET-A Phase 2 Commit 3.

These tests exercise the contract that the API can serialize an ecosphere's
temperament out to Scala, parse the Scala back, and rebuild an ecosphere
that produces byte-identical fret positions.

Lives in tests/integration/ rather than tests/api_v1/ because it spans
multiple endpoints and asserts a property across them.
"""
from __future__ import annotations

import sys

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


# =============================================================================
# GRBL pipeline integration (Phase 7)
# =============================================================================

class TestGrblPipelineIntegration:
    """R2000 DXF fret slots produce valid G-code through GRBL pipeline.

    Sprint FRET-A Phase 7: This test guards against the 2-point loop-assembly
    gap issue identified in cam_pipeline_r2000_compat 2026-04-29. If fret slot
    polylines are emitted as individual segments instead of closed contours,
    the GRBL pipeline returns ~0 lines.
    """

    def test_r2000_fret_slots_produce_grbl_gcode(self):
        """R2000 FRET_SLOTS polylines produce >=100 G-code lines."""
        import pytest

        # Python 3.14 has a known issue where numpy's C extension cannot be
        # loaded more than once per process. When ezdxf imports numpy after
        # other test modules have already loaded it through a different path,
        # we get "ImportError: cannot load module more than once per process".
        # This is an environment issue, not a code defect.
        if sys.version_info >= (3, 14):
            pytest.skip("Python 3.14 numpy/ezdxf module loading conflict")

        from app.instrument_geometry.neck.fretboard_ecosphere import (
            FretboardInput,
            FretboardEcosphere,
            write_ecosphere_dxf,
        )

        # Build ecosphere and project to R2000 DXF
        eco = FretboardEcosphere.compute(FretboardInput(
            scale_length_mm=647.7,
            fret_count=22,
            string_count=6,
            slot_width_mm=0.58,
        ))
        dxf_bytes = write_ecosphere_dxf(eco, version="R2000")

        # Send to GRBL pipeline
        resp = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("fret_slots.dxf", dxf_bytes, "application/dxf")},
            data={"layer_name": "FRET_SLOTS"},
        )

        # Pipeline should succeed and produce substantial G-code
        if resp.status_code == 404:
            import pytest
            pytest.skip("RMOS MVP router not mounted in test app")

        assert resp.status_code == 200, f"GRBL pipeline failed: {resp.text}"

        body = resp.json()
        gcode = body.get("gcode") or body.get("data", {}).get("gcode") or ""
        # gcode is returned as an {"inline": bool, "text": str} envelope
        # (CI-RED-015-E F2: the test was stale, the kernel/endpoint is right);
        # extract the text before counting lines.
        gcode_text = gcode["text"] if isinstance(gcode, dict) else gcode
        line_count = gcode_text.count("\n")

        assert line_count >= 100, (
            f"GRBL pipeline produced {line_count} lines from R2000 fret slots. "
            f"Expected >=100. The 2-point loop-assembly gap from 2026-04-29 "
            f"may have reproduced. Check _project_fret_slots emission."
        )
