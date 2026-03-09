"""
Tests for simulate_segments() — per-segment toolpath simulation.

Validates:
- Correct segment types for G0/G1/G2/G3
- Arc interpolation (IJ and R modes)
- Duration parity against simulate() aggregate
- Bounding box correctness
- Unit switching (G20/G21)
- Edge cases (empty G-code, full circle, degenerate arcs)

Run:
    pytest services/api/tests/test_gcode_simulate.py -v
"""
import math
import pytest

from app.util.gcode_parser import simulate, simulate_segments


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def run(gcode: str, **kwargs):
    return simulate_segments(gcode, **kwargs)

def segs_of_type(result, t):
    return [s for s in result["segments"] if s["type"] == t]


# ---------------------------------------------------------------------------
# Empty G-code
# ---------------------------------------------------------------------------

def test_empty_gcode_returns_empty():
    r = run("")
    assert r["segments"] == []
    assert r["totals"]["segment_count"] == 0
    assert r["totals"]["time_min"] == 0.0


def test_whitespace_only_returns_empty():
    r = run("   \n\n  ")
    assert r["segments"] == []


def test_comment_only_returns_empty():
    r = run("; This is just a comment\n(another comment)")
    assert r["segments"] == []


# ---------------------------------------------------------------------------
# Rapid moves (G0)
# ---------------------------------------------------------------------------

def test_g0_produces_rapid_segments():
    r = run("G0 X10 Y0\nG0 X20 Y0")
    rapids = segs_of_type(r, "rapid")
    assert len(rapids) == 2
    assert segs_of_type(r, "cut") == []

def test_g0_from_to_coordinates():
    r = run("G0 X10 Y5")
    seg = r["segments"][0]
    assert seg["type"] == "rapid"
    assert seg["from_pos"] == [0.0, 0.0, 0.0]
    assert pytest.approx(seg["to_pos"][0], abs=1e-6) == 10.0
    assert pytest.approx(seg["to_pos"][1], abs=1e-6) == 5.0

def test_g0_uses_rapid_feed_rate():
    r = run("G0 X100 Y0", rapid_mm_min=3000.0)
    seg = r["segments"][0]
    assert seg["feed"] == 3000.0
    expected_ms = (100.0 / 3000.0) * 60_000.0
    assert pytest.approx(seg["duration_ms"], rel=1e-5) == expected_ms


# ---------------------------------------------------------------------------
# Cut moves (G1)
# ---------------------------------------------------------------------------

def test_g1_produces_cut_segments():
    r = run("G1 X10 F600")
    cuts = segs_of_type(r, "cut")
    assert len(cuts) == 1
    assert segs_of_type(r, "rapid") == []

def test_g1_modal_feed_persists():
    r = run("G1 X10 F800\nG1 X20")
    for seg in r["segments"]:
        assert seg["feed"] == 800.0

def test_g1_duration_correct():
    r = run("G1 X50 F1500")
    seg = r["segments"][0]
    expected_ms = (50.0 / 1500.0) * 60_000.0
    assert pytest.approx(seg["duration_ms"], rel=1e-5) == expected_ms


# ---------------------------------------------------------------------------
# Arc moves (G2/G3) — IJ mode
# ---------------------------------------------------------------------------

def test_g2_produces_arc_cw_segments():
    r = run("G1 X10 Y0 F800\nG2 X-10 Y0 I-10 J0")
    arcs = segs_of_type(r, "arc_cw")
    assert len(arcs) > 1, "semicircle should produce multiple sub-segments"

def test_g3_produces_arc_ccw_segments():
    r = run("G1 X10 Y0 F800\nG3 X-10 Y0 I-10 J0")
    arcs = segs_of_type(r, "arc_ccw")
    assert len(arcs) > 1

def test_arc_ij_resolution_affects_segment_count():
    gcode = "G1 X10 Y0 F800\nG2 X-10 Y0 I-10 J0"
    r5  = run(gcode, arc_resolution_deg=5)
    r10 = run(gcode, arc_resolution_deg=10)
    assert len(segs_of_type(r5, "arc_cw")) > len(segs_of_type(r10, "arc_cw"))

def test_arc_ij_total_length_consistent():
    """Sum of arc sub-segment XY distances should equal semicircle circumference."""
    r = run("G1 X10 Y0 F800\nG2 X-10 Y0 I-10 J0", arc_resolution_deg=1)
    arcs = segs_of_type(r, "arc_cw")
    total_len = sum(
        math.hypot(s["to_pos"][0] - s["from_pos"][0], s["to_pos"][1] - s["from_pos"][1])
        for s in arcs
    )
    expected = math.pi * 10.0  # semicircle of radius 10
    assert pytest.approx(total_len, rel=0.01) == expected  # within 1%

def test_arc_ends_at_correct_position():
    """Final arc sub-segment must end at the commanded endpoint."""
    r = run("G1 X10 Y0 F800\nG2 X0 Y0 I-5 J0", arc_resolution_deg=2)
    arcs = segs_of_type(r, "arc_cw")
    last = arcs[-1]
    assert last["to_pos"][0] == pytest.approx(0.0, abs=0.01)
    assert last["to_pos"][1] == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# Arc moves — R mode
# ---------------------------------------------------------------------------

def test_g2_r_mode_produces_arc_cw():
    r = run("G1 X10 Y0 F600\nG2 X0 Y10 R10")
    arcs = segs_of_type(r, "arc_cw")
    assert len(arcs) > 1

def test_g3_r_mode_produces_arc_ccw():
    r = run("G1 X10 Y0 F600\nG3 X0 Y10 R10")
    arcs = segs_of_type(r, "arc_ccw")
    assert len(arcs) > 1


# ---------------------------------------------------------------------------
# Full circle (start == end)
# ---------------------------------------------------------------------------

def test_full_circle_ij_produces_segments():
    r = run("G0 X10 Y0\nG2 X10 Y0 I-10 J0 F600")
    arcs = segs_of_type(r, "arc_cw")
    assert len(arcs) > 10, "full circle should have many sub-segments"


# ---------------------------------------------------------------------------
# Mixed program
# ---------------------------------------------------------------------------

def test_mixed_program_all_types_present():
    gcode = """
G21
G0 X0 Y0
G1 Z-3 F300
G1 X50 Y0 F1200
G1 X50 Y50
G2 X0 Y50 I-25 J0
G3 X10 Y30 I5 J-10
G0 Z5
"""
    r = run(gcode)
    types = {s["type"] for s in r["segments"]}
    assert "rapid" in types
    assert "cut" in types
    assert "arc_cw" in types
    assert "arc_ccw" in types

def test_mixed_program_order_preserved():
    gcode = "G0 X10 Y0\nG1 X20 F600\nG2 X30 Y10 I5 J5"
    r = run(gcode)
    assert r["segments"][0]["type"] == "rapid"
    assert r["segments"][1]["type"] == "cut"
    arc_types = {s["type"] for s in r["segments"][2:]}
    assert "arc_cw" in arc_types


# ---------------------------------------------------------------------------
# Line number tracking
# ---------------------------------------------------------------------------

def test_line_numbers_are_1_based_and_sequential():
    gcode = "G0 X10\nG1 X20 F600\nG0 X0"
    r = run(gcode)
    for seg in r["segments"]:
        assert seg["line_number"] >= 1

def test_line_text_matches_source():
    gcode = "G0 X10 Y0\nG1 X20 F600"
    r = run(gcode)
    rapid = segs_of_type(r, "rapid")[0]
    assert "G0" in rapid["line_text"] or "X10" in rapid["line_text"]


# ---------------------------------------------------------------------------
# Bounding box
# ---------------------------------------------------------------------------

def test_bounds_contains_all_endpoints():
    gcode = "G0 X-5 Y-3\nG1 X30 Y20 F600\nG0 Z-8"
    r = run(gcode)
    bb = r["bounds"]
    for seg in r["segments"]:
        for pos in (seg["from_pos"], seg["to_pos"]):
            assert pos[0] >= bb["x_min"] - 1e-6
            assert pos[0] <= bb["x_max"] + 1e-6
            assert pos[1] >= bb["y_min"] - 1e-6
            assert pos[1] <= bb["y_max"] + 1e-6
            assert pos[2] >= bb["z_min"] - 1e-6
            assert pos[2] <= bb["z_max"] + 1e-6

def test_bounds_negative_coords():
    r = run("G0 X-20 Y-15\nG1 X5 Y5 F600")
    bb = r["bounds"]
    assert bb["x_min"] <= -20.0
    assert bb["y_min"] <= -15.0


# ---------------------------------------------------------------------------
# Unit switching
# ---------------------------------------------------------------------------

def test_g20_inch_converts_to_mm():
    """G20 sets inch mode: X1.0 should become 25.4 mm internally."""
    r = run("G20\nG1 X1.0 F10", rapid_mm_min=3000)
    seg = r["segments"][0]
    assert pytest.approx(seg["to_pos"][0], abs=0.1) == 25.4

def test_g21_mm_mode_default():
    r = run("G21\nG1 X10 F600")
    seg = r["segments"][0]
    assert pytest.approx(seg["to_pos"][0], abs=1e-6) == 10.0


# ---------------------------------------------------------------------------
# Duration parity with simulate()
# ---------------------------------------------------------------------------

PARITY_PROGRAMS = [
    "G0 X10 Y10\nG1 X50 F1200\nG0 Z5",
    "G21\nG0 X0 Y0\nG1 Z-3 F300\nG1 X50 Y0 F1200\nG1 X50 Y50\nG2 X0 Y50 I-25 J0\nG0 Z5",
    "G0 X0 Y0\nG3 X20 Y0 R10 F800",
]

@pytest.mark.parametrize("gcode", PARITY_PROGRAMS)
def test_duration_parity_with_simulate(gcode):
    """
    sum(segment.duration_ms) / 60000 must match simulate()['t_total_min']
    within 0.001 minute tolerance.
    """
    old = simulate(gcode)
    new = run(gcode, arc_resolution_deg=1)
    total_from_segs = new["totals"]["time_min"]
    delta = abs(old["t_total_min"] - total_from_segs)
    assert delta < 0.001, (
        f"Parity failure: simulate={old['t_total_min']:.6f}, "
        f"simulate_segments={total_from_segs:.6f}, delta={delta:.6f}"
    )


# ---------------------------------------------------------------------------
# Totals aggregation
# ---------------------------------------------------------------------------

def test_totals_segment_count_matches_segments_length():
    r = run("G0 X10\nG1 X20 F600\nG0 X0")
    assert r["totals"]["segment_count"] == len(r["segments"])

def test_totals_time_matches_sum_of_duration_ms():
    r = run("G0 X10 Y0\nG1 X30 F800")
    expected_min = sum(s["duration_ms"] for s in r["segments"]) / 60_000.0
    assert pytest.approx(r["totals"]["time_min"], rel=1e-9) == expected_min
