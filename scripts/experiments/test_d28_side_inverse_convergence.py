"""
Focused, hardware-free regression tests for the D-28 side-profile inverse
convergence experiment. These do not touch production code or specs; they guard
the experiment's own invariants:

* it reuses the production Sevy/Doolin equations unchanged (Mottola ground truth);
* it never equates the developed side-strip station with the Euclidean D;
* the profile endpoints act as the B/S boundary conditions;
* the waist hard constraint is actually reproduced by the nested solve;
* a missing declared experimental input stops the run (no repo-default fallback).
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


def test_reuses_production_sevy_equations_mottola_groundtruth():
    """The experiment must reuse the repo equations unchanged. Reproduce the
    verification baked into body_contour_solver (inches; Mottola sidecalc)."""
    R, L, B, S, M, N, D = 180.0, 19.25, 4.0, 3.3, 0.11, 0.09, 1.0
    P = exp.solve_high_point(L, B, S, R)
    H = exp.solve_side_height(B, R, P, D, M, N)
    assert abs(P - 3.093) < 0.01
    assert abs(H - 3.824) < 0.01


def test_station_is_not_equated_with_D():
    """Core geometry rule: D is the in-plane distance from the high point to the
    mapped perimeter point, never the developed station itself."""
    L, R = 20.0, 180.0
    for station in (3.0, 6.0, 9.0, 12.0, 21.0, 27.0):
        _, D, _ = exp.predict_height(L, R, station)
        assert abs(D - station) > 0.5, f"D collapsed onto station at s={station}"


def test_endpoints_map_to_centerline():
    """Station 0 -> neck (0, L); station max -> tail (0, 0): x ~ 0 at both."""
    L = 20.0
    x0, y0, _ = exp._perimeter_point(L, exp.S_NECK)
    xm, ym, _ = exp._perimeter_point(L, exp.S_MAX)
    assert abs(x0) < 1e-6 and abs(y0 - L) < 1e-6
    assert abs(xm) < 1e-6 and abs(ym) < 1e-6


def test_endpoints_are_the_B_and_S_boundary_conditions():
    """With M=N=0 the model returns B at the tail and S at the neck."""
    L, R = 20.0, 180.0
    H_neck, _, _ = exp.predict_height(L, R, exp.S_NECK)
    H_tail, _, _ = exp.predict_height(L, R, exp.S_MAX)
    assert abs(H_neck - exp.S_SHOULDER) < 1e-6
    assert abs(H_tail - exp.B_BUTT) < 1e-6


def test_waist_constraint_is_reproduced_by_nested_solve():
    """solve_L_for_waist(R, W) must return an L that reproduces W at the waist."""
    R = 120.0
    L = exp.solve_L_for_waist(R, exp.WAIST_H_AUTHORITATIVE)
    assert L is not None
    H_waist, _, _ = exp.predict_height(L, R, exp.S_WAIST)
    assert abs(H_waist - exp.WAIST_H_AUTHORITATIVE) < 1e-4


def test_authoritative_waist_overrides_legacy_value():
    """The declared waist input governs, not the repo's legacy 4.220."""
    assert exp.EXPERIMENTAL_INPUTS["waist_depth_in"] == 4.4375
    assert exp.WAIST_H_LEGACY == pytest.approx(4.220)
    assert exp.EXPERIMENTAL_INPUTS["waist_depth_in"] != exp.WAIST_H_LEGACY


def test_missing_required_input_stops_run():
    """A missing declared input must STOP rather than fall back to a repo value."""
    saved = exp.EXPERIMENTAL_INPUTS["waist_depth_in"]
    exp.EXPERIMENTAL_INPUTS["waist_depth_in"] = None
    try:
        with pytest.raises(SystemExit):
            exp.check_required_inputs()
    finally:
        exp.EXPERIMENTAL_INPUTS["waist_depth_in"] = saved


def test_inconsistency_register_flags_the_waist_override():
    """The audit must record the 4.4375-vs-4.220 override explicitly."""
    reg = exp.build_inconsistency_register(
        bestA=None, bestA_legacy=None, fitB=[], mc={"P": 0.0, "on_bound": False},
        hp_20=31.28)
    classes = {r["class"] for r in reg}
    assert "EXPERIMENTAL_OVERRIDE" in classes
    assert "UNIT_OR_DATUM_AMBIGUITY" in classes
    waist_rows = [r for r in reg if "waist side depth" in r["field"]]
    assert waist_rows and "4.4375" in waist_rows[0]["experimental"]
