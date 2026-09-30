"""
Focused, hardware-free regression tests for the D-28 side-height inverse
**Rerun 002** experiment. They touch no production code or specs; they guard the
rerun's governing invariants:

* the active hard waist constraint is the Arnold side height 4.220 in;
* the drawing "DEEP" value 4.4375 in is NOT used as a side height;
* the waist station is geometrically derived from the outline, not hardcoded 10.5;
* D is the Euclidean in-plane distance to the high point, not the developed station;
* invalid geometry fails closed (flagged inadmissible; no crash);
* the convergence log is deterministic for identical inputs;
* it reuses the production Sevy/Doolin equations unchanged (Mottola ground truth);
* the experiment writes only to docs/experiments (no production/spec file).
"""
import importlib.util
import os
import sys

import pytest

_HERE = os.path.dirname(__file__)
_SPEC = importlib.util.spec_from_file_location(
    "d28_exp", os.path.join(_HERE, "d28_side_inverse_convergence.py"))
exp = importlib.util.module_from_spec(_SPEC)
sys.modules["d28_exp"] = exp   # required so @dataclass can resolve its module
_SPEC.loader.exec_module(exp)


def test_active_waist_constraint_is_4220_side_height():
    assert exp.WAIST_SIDE_HEIGHT == 4.220
    assert exp.EXPERIMENTAL_INPUTS["waist_side_height_in"] == 4.220


def test_drawing_deep_4p4375_is_not_used_as_side_height():
    assert exp.DRAWING_DEEP == 4.4375
    assert exp.WAIST_SIDE_HEIGHT != exp.DRAWING_DEEP
    # 4.4375 must not appear anywhere in the Arnold side-height observations.
    assert 4.4375 not in set(exp.ARNOLD_SIDE_HEIGHT_IN.values())
    # It is declared comparison-only.
    assert exp.DRAWING_DEEP == exp.COMPARISON_TARGETS["drawing_deep_in"]


def test_waist_station_is_geometrically_derived_not_hardcoded_10_5():
    gw20 = exp.geometric_waist(20.0)
    # The geometric waist is the narrowest point: half-width == waist_width/2.
    assert abs(gw20["x"] - exp.WAIST_W / 2.0) < 1e-6
    # Derived developed station is NOT the legacy 10.5 assumption.
    assert abs(gw20["s_waist"] - 10.5) > 1.0
    # It is genuinely derived: it moves when the body length changes.
    gw18 = exp.geometric_waist(18.0)
    assert abs(gw20["s_waist"] - gw18["s_waist"]) > 1e-3


def test_D_is_euclidean_not_developed_station():
    L, R = 20.0, 180.0
    for station in (3.0, 6.0, 9.0, 12.0, 21.0, 27.0):
        _, D, _ = exp.predict_station_height(L, R, station)
        assert abs(D - station) > 0.5, f"D collapsed onto the station at s={station}"


def test_reuses_production_sevy_equations_mottola_groundtruth():
    R, L, B, S, M, N, D = 180.0, 19.25, 4.0, 3.3, 0.11, 0.09, 1.0
    P = exp.solve_high_point(L, B, S, R)
    H = exp.solve_side_height(B, R, P, D, M, N)
    assert abs(P - 3.093) < 0.01
    assert abs(H - 3.824) < 0.01


def test_endpoints_are_the_B_and_S_boundary_conditions():
    L, R = 20.0, 180.0
    H_neck, _, _ = exp.predict_station_height(L, R, exp.S_NECK_STATION)
    H_tail, _, _ = exp.predict_station_height(L, R, exp.S_TAIL_STATION)
    assert abs(H_neck - exp.S_SHOULDER) < 1e-3
    # Tail maps at absolute arc length 30.4375 (short of the outline tail), so it
    # is close to B but not exact; boundary depth B is honoured at the geometric tail.
    assert abs(H_tail - exp.B_BUTT) < 0.2


def test_invalid_geometry_fails_closed():
    # A large radius drives the high point outside the body (P < 0): inadmissible,
    # and the prediction must not raise (it clamps / fails closed).
    adm, reasons = exp.is_admissible(20.0, 300.0)
    assert adm is False
    assert any("P<0" in r for r in reasons)
    H, D, _ = exp.predict_station_height(20.0, 300.0, 12.0)  # must not raise
    assert isinstance(H, float)


def test_missing_required_input_stops_run():
    saved = exp.WAIST_SIDE_HEIGHT
    exp.WAIST_SIDE_HEIGHT = None
    try:
        with pytest.raises(SystemExit):
            exp.check_required_inputs()
    finally:
        exp.WAIST_SIDE_HEIGHT = saved


def test_convergence_log_is_deterministic():
    log1 = exp.ConvergenceLogger()
    log2 = exp.ConvergenceLogger()
    exp.analysis_A(log1, n_R=3)
    exp.analysis_A(log2, n_R=3)
    assert log1.rows == log2.rows
    assert len(log1.rows) > 0


def test_experiment_writes_only_under_docs_experiments():
    for p in (exp._DOC, exp._CONV_CSV, exp._SUM_CSV):
        norm = os.path.normpath(p)
        assert os.path.join("docs", "experiments") in norm
    # The spec/authority files are not write targets of this experiment.
    assert "specs" not in os.path.normpath(exp._CONV_CSV)
    assert exp._SPEC_JSON not in (exp._DOC, exp._CONV_CSV, exp._SUM_CSV)


def test_disposition_is_from_the_allowed_vocabulary():
    allowed = {"CONVERGES_AND_SUPPORTS_20IN", "CONVERGES_BUT_NOT_20IN",
               "UNDERDETERMINED", "SPHERICAL_MODEL_MISMATCH",
               "INSUFFICIENT_GEOMETRY_AUTHORITY"}
    disp, _ = exp.classify(None, [], [], floor_H=4.30)
    assert disp in allowed
