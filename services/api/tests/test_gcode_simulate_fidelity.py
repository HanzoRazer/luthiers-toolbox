"""
Regression tests for toolpath-simulation fidelity fixes.

Each test maps to a finding in TOOLPATH_ANIMATION_AUDIT (2026-05-30):

    X1  Z motion / 3D timing      X2  canned cycle expansion
    X3  multi-G per line          Y1  G90/G91 incremental
    Y2  non-XY (G18/G19) arcs     Y3  R-mode full-circle rejection
    Z1  unsupported-code warnings Z2  dwell time
    Z3  bounds exclude home       Z4  tools payload
    Z5  backend segment cap

Run:
    pytest services/api/tests/test_gcode_simulate_fidelity.py -v
"""
import math

import pytest

from app.util.gcode_parser import simulate, simulate_segments
from app.util.gcode.geometry import arc_center_from_r


def run(gcode: str, **kwargs):
    return simulate_segments(gcode, **kwargs)


def of_type(result, t):
    return [s for s in result["segments"] if s["type"] == t]


# ---------------------------------------------------------------------------
# X1 — vertical (Z) motion and 3D timing
# ---------------------------------------------------------------------------

def test_z_only_plunge_has_nonzero_duration():
    r = run("G1 Z-5 F300")
    assert len(r["segments"]) == 1
    seg = r["segments"][0]
    assert seg["type"] == "cut"
    assert seg["duration_ms"] == pytest.approx(1000.0, rel=1e-6)   # 5/300 min
    assert r["totals"]["time_min"] == pytest.approx(5.0 / 300.0, rel=1e-6)


def test_rapid_z_retract_has_nonzero_duration():
    r = run("G0 X10 Y10\nG0 Z5")
    retract = [s for s in r["segments"] if s["line_text"].strip() == "G0 Z5"]
    assert retract and retract[0]["duration_ms"] > 0.0


def test_duration_uses_full_3d_distance():
    # From origin to (3, 0, -4): planar distance 3, true distance 5.
    r = run("G1 X3 Z-4 F600")
    seg = r["segments"][0]
    assert seg["duration_ms"] == pytest.approx((5.0 / 600.0) * 60_000.0, rel=1e-6)


# ---------------------------------------------------------------------------
# X3 — multiple G-words on one line
# ---------------------------------------------------------------------------

def test_trailing_nonmotion_g_does_not_clobber_motion():
    r = run("G0 X10 Y0\nG1 G17 X40 Y0 F300")
    assert r["segments"][0]["type"] == "rapid"
    assert r["segments"][1]["type"] == "cut"      # G1 wins, not the trailing G17
    assert r["segments"][1]["feed"] == 300.0


# ---------------------------------------------------------------------------
# Y1 — G90 / G91 absolute vs incremental
# ---------------------------------------------------------------------------

def test_g91_incremental_accumulates():
    r = run("G91\nG1 X10 F600\nG1 X10\nG1 X10")
    assert len(r["segments"]) == 3
    assert r["segments"][-1]["to_pos"][0] == pytest.approx(30.0)


def test_g90_g91_roundtrip():
    r = run("G1 X10 F600\nG91\nG1 X5\nG90\nG1 X0")
    xs = [s["to_pos"][0] for s in r["segments"]]
    assert xs == pytest.approx([10.0, 15.0, 0.0])


# ---------------------------------------------------------------------------
# Y2 — arcs in the XZ (G18) / YZ (G19) planes
# ---------------------------------------------------------------------------

def test_g18_arc_is_simulated_not_dropped():
    r = run("G18\nG2 X10 Z0 I5 K0 F300")
    arcs = of_type(r, "arc_cw")
    assert len(arcs) > 1
    # Radius-5 arc in XZ → ~10mm of Z spread (direction-agnostic).
    assert r["bounds"]["z_max"] - r["bounds"]["z_min"] >= 4.9
    assert r["warnings"]["non_xy_arcs"] >= 1
    assert r["segments"][-1]["to_pos"][0] == pytest.approx(10.0, abs=0.05)


def test_non_xy_arc_does_not_desync_position():
    r = run("G18\nG2 X10 Z0 I5 K0 F300\nG1 X20 Y0")
    last = r["segments"][-1]
    assert last["type"] == "cut"
    assert last["from_pos"][0] == pytest.approx(10.0, abs=0.05)   # not stale 0
    assert last["to_pos"][0] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Y3 — R-mode cannot express a full circle
# ---------------------------------------------------------------------------

def test_arc_center_from_r_rejects_zero_chord():
    assert arc_center_from_r(0, 0, 0, 0, 5, True) is None
    assert arc_center_from_r(0, 0, 0, 0, 5, False) is None


def test_r_mode_full_circle_draws_no_fake_arc():
    r = run("G0 X10 Y0\nG2 X10 Y0 R5 F300")
    assert of_type(r, "arc_cw") == []
    assert r["warnings"]["degenerate_arcs"] >= 1


# ---------------------------------------------------------------------------
# Z1 — unsupported / acknowledged codes are surfaced, not silent
# ---------------------------------------------------------------------------

def test_unsupported_g_code_surfaced():
    r = run("G12 X5 Y5 F300")
    assert 12 in r["warnings"]["unsupported_g"]


def test_unknown_m_code_surfaced():
    r = run("M77\nG1 X5 F300")
    assert 77 in r["warnings"]["unsupported_m"]


def test_known_m_codes_not_flagged():
    r = run("M3 S1000\nG1 X5 F300\nM5")
    assert r["warnings"]["unsupported_m"] == []


def test_work_offset_acknowledged_not_silent():
    r = run("G54\nG1 X5 F300")
    assert 54 in r["warnings"]["ignored_offsets"]


# ---------------------------------------------------------------------------
# Z2 — dwell (G4) consumes time
# ---------------------------------------------------------------------------

def test_dwell_adds_time():
    r = run("G1 X10 F600\nG4 P2")
    dwell = of_type(r, "dwell")
    assert len(dwell) == 1
    assert dwell[0]["duration_ms"] == pytest.approx(2000.0)
    expected = (10.0 / 600.0) + (2.0 / 60.0)
    assert r["totals"]["time_min"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Z3 — bounds frame the work, not the synthetic home position
# ---------------------------------------------------------------------------

def test_bounds_exclude_synthetic_home_origin():
    r = run("G0 X100 Y100\nG1 X150 Y120 F600")
    bb = r["bounds"]
    assert bb["x_min"] == pytest.approx(100.0)
    assert bb["y_min"] == pytest.approx(100.0)
    assert bb["x_max"] == pytest.approx(150.0)
    assert bb["y_max"] == pytest.approx(120.0)


# ---------------------------------------------------------------------------
# Z4 — multi-tool payload reaches the caller
# ---------------------------------------------------------------------------

def test_tools_payload_present_and_tracks_changes():
    r = run("T1 M6\nG1 X10 F300\nT2 M6\nG1 X20")
    assert "tools" in r
    assert r["tools"]["count"] >= 2
    assert 2 in r["tools"]["used"]
    assert any(c["to_tool"] == 2 for c in r["tools"]["changes"])


# ---------------------------------------------------------------------------
# Z5 — backend cap truncates loudly
# ---------------------------------------------------------------------------

def test_max_segments_cap_truncates_loudly():
    # Full circle at 1° resolution → hundreds of sub-segments.
    r = run("G0 X10 Y0\nG2 X10 Y0 I-10 J0 F600", arc_resolution_deg=1, max_segments=5)
    assert len(r["segments"]) == 5
    assert r["warnings"]["truncated"] is True
    assert r["warnings"]["dropped_segments"] > 0


# ---------------------------------------------------------------------------
# X2 — canned drilling cycles expand into motion
# ---------------------------------------------------------------------------

def test_g83_peck_drill_expands():
    g = "G0 X10 Y10\nG0 Z2\nG83 Z-10 R2 Q3 F100\nG80"
    r = run(g)
    cyc = [s for s in r["segments"] if s["is_cycle"]]
    assert cyc, "G83 should expand into cycle segments"
    assert all(s["cycle_kind"] == "G83" for s in cyc)
    assert r["bounds"]["z_min"] <= -10 + 1e-6           # reaches drill depth
    assert any(s["type"] == "cut" for s in cyc)         # plunges
    assert any(s["type"] == "rapid" for s in cyc)       # retracts
    plunges = [s for s in cyc if s["type"] == "cut"]
    assert len(plunges) >= 4                            # depth 12 / peck 3


def test_g81_simple_drill_expands():
    g = "G0 Z5\nG81 X0 Y0 Z-3 R1 F120\nG80"
    r = run(g)
    cyc = [s for s in r["segments"] if s["is_cycle"]]
    assert cyc
    assert any(
        s["type"] == "cut" and s["to_pos"][2] == pytest.approx(-3.0) for s in cyc
    )


def test_g83_multi_hole_modal_repeats():
    # One G83 then bare X/Y lines: cycle repeats at each location.
    g = "G0 Z5\nG83 X0 Y0 Z-5 R1 Q2 F100\nX10 Y0\nX20 Y0\nG80"
    r = run(g)
    cyc = [s for s in r["segments"] if s["is_cycle"]]
    drilled_x = {round(s["to_pos"][0]) for s in cyc}
    assert {0, 10, 20}.issubset(drilled_x)


# ---------------------------------------------------------------------------
# Parity — the previously false-confidence check now reflects Z time
# ---------------------------------------------------------------------------

def test_z_plunge_increases_total_time():
    with_z = simulate("G1 X10 Z-10 F600")["t_total_min"]
    without_z = simulate("G1 X10 F600")["t_total_min"]
    assert with_z > without_z


def test_simulate_and_segments_agree_including_z():
    g = "G0 X0 Y0\nG1 Z-5 F300\nG1 X10 F600\nG0 Z5"
    agg = simulate(g)["t_total_min"]
    seg = simulate_segments(g, arc_resolution_deg=1)["totals"]["time_min"]
    assert agg == pytest.approx(seg, abs=1e-9)
    assert agg > 0.0


# ---------------------------------------------------------------------------
# Acceleration / deceleration model (opt-in trapezoidal timing)
# ---------------------------------------------------------------------------

def test_accel_disabled_is_constant_velocity():
    # 100mm at F6000 = 100 mm/s → 1.000 s with instantaneous accel.
    r = run("G1 X100 F6000")
    assert r["segments"][0]["duration_ms"] == pytest.approx(1000.0, rel=1e-6)


def test_accel_lengthens_a_long_move():
    base = run("G1 X100 F6000")["segments"][0]["duration_ms"]
    acc = run("G1 X100 F6000", accel_mm_s2=1000.0)["segments"][0]["duration_ms"]
    assert acc > base
    # accel 5mm + cruise 90mm + decel 5mm at 1000 mm/s^2 → 0.1 + 0.9 + 0.1 = 1.1 s
    assert acc == pytest.approx(1100.0, rel=1e-3)


def test_accel_dominates_short_move():
    # 2mm move never reaches nominal feed → triangular profile, much slower.
    base = run("G1 X2 F6000")["segments"][0]["duration_ms"]
    acc = run("G1 X2 F6000", accel_mm_s2=1000.0)["segments"][0]["duration_ms"]
    assert acc > base * 3


def test_accel_total_time_not_less_than_constant():
    g = "G0 X0 Y0\nG1 X50 Y0 F3000\nG1 X50 Y50\nG2 X0 Y50 I-25 J0\nG0 Z5"
    base = simulate_segments(g)["totals"]["time_min"]
    acc = simulate_segments(g, accel_mm_s2=800.0)["totals"]["time_min"]
    assert acc >= base
