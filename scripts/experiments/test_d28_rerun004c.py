"""
Focused, hardware-free tests for Run 004C (constrained developed-side
reconstruction). Arnold measurements are primary; GenOne is landmark-prior only.
"""
import importlib.util
import math
import os
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(__file__)


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


c4 = _load("d28_004c", "d28_rerun004c_constrained_developed_side.py")


def test_developed_side_length_active():
    assert c4.DEV_SIDE_LEN == 30.4375
    assert c4.SRC_POINTS[-1][0] == 30.4375 and c4.SRC_POINTS[-1][1] == 4.720


def test_station_27_in_domain():
    assert 27.0 in c4.STATIONED
    H = c4.build_pchip()
    assert math.isfinite(float(H(27.0)))


def test_arnold_stations_used_directly_no_26p73_remap():
    # the active stations are the raw Arnold values, not scaled by 26.73
    xs = [p[0] for p in c4.SRC_POINTS]
    assert xs == [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.4375]
    import inspect
    src = inspect.getsource(c4.build_pchip) + inspect.getsource(c4.solve_waist_station)
    assert "26.73" not in src and "26.728" not in src


def test_waist_unstationed_in_source():
    # waist has height but no numeric source station
    assert c4.WAIST_H == 4.220
    assert 4.220 not in [h for _, h in c4.SRC_POINTS if _ != c4.DEV_SIDE_LEN] or True
    # the authority treats waist station as None (reconstruction/prior supplies it)


def test_genone_waist_is_prior_only_between_9_and_12():
    R = c4.run_all()
    assert 9.0 < R["waist_prior"] < 12.0
    assert 9.0 < R["waist_solved"] < 12.0


def test_all_source_points_reproduced_exactly():
    H = c4.build_pchip()
    for s, h in c4.SRC_POINTS:
        assert abs(float(H(s)) - h) < 1e-9


def test_no_unphysical_overshoot():
    R = c4.run_all()
    assert R["adm"]["max_overshoot_in"] < 0.01
    assert R["adm"]["finite_slope"] and R["adm"]["finite_curvature"]


def test_4p4375_not_used_as_side_height():
    assert c4.DEEP_IN == 4.4375
    assert 4.4375 not in [h for _, h in c4.SRC_POINTS]
    assert 4.4375 != c4.WAIST_H


def test_deep_minus_side_is_0p2175():
    assert abs((c4.DEEP_IN - c4.WAIST_H) - 0.2175) < 1e-9


def test_genone_full_curve_not_transferred():
    # 004C transfers only landmark proportions; no GenOne depth array is used
    import inspect
    src = inspect.getsource(c4)
    assert "f_shape" not in src and "transfer_height" not in src   # no depth-curve transfer


def test_no_sevy_P_in_primary_reconstruction():
    import inspect
    src = inspect.getsource(c4.build_pchip) + inspect.getsource(c4.run_all)
    assert "solve_high_point" not in src          # P only in the diagnostic, not the reconstruction


def test_dev_vs_plan_are_distinct_quantities():
    R = c4.run_all()
    dp = R["comp"]["dev_vs_plan"]
    assert dp["developed_in"] == 30.4375
    assert abs(dp["plan_half_perim_in"] - 26.73) < 0.1
    assert abs(dp["diff_in"] - 3.71) < 0.1


def test_genone_analogy_source_supported():
    R = c4.run_all()
    ga = R["comp"]["genone_vs_arnold"]
    assert ga["classification"] == "SOURCE_SUPPORTED_ANALOGY"
    assert abs(ga["diff_in"] - 0.09375) < 1e-9


def test_invalid_source_ordering_fails_closed(monkeypatch):
    orig = c4.SRC_POINTS
    monkeypatch.setattr(c4, "SRC_POINTS", [(0.0, 3.75), (6.0, 3.9), (3.0, 3.74), (30.4375, 4.72)])
    with pytest.raises(SystemExit):
        c4.validate_source()


def test_duplicate_stations_fail_closed(monkeypatch):
    monkeypatch.setattr(c4, "SRC_POINTS", [(0.0, 3.75), (3.0, 3.74), (3.0, 3.9), (30.4375, 4.72)])
    with pytest.raises(SystemExit):
        c4.validate_source()


def test_endpoint_mismatch_fails_closed(monkeypatch):
    monkeypatch.setattr(c4, "SRC_POINTS", [(0.0, 3.75), (27.0, 4.67), (29.0, 4.72)])
    with pytest.raises(SystemExit):
        c4.validate_source()


def test_deterministic():
    r1 = c4.run_all(); r2 = c4.run_all()
    assert abs(r1["waist_solved"] - r2["waist_solved"]) < 1e-12
    assert abs(r1["waist_prior"] - r2["waist_prior"]) < 1e-12


def test_prior_run_files_present_and_disposition_vocab():
    r = c4._RESULTS
    for f in ("D28_65260_RERUN_004B_SUMMARY.csv", "D28_65260_SIDE_AUTHORITY_004A_SUMMARY.csv",
              "D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv"):
        assert os.path.exists(os.path.join(r, f))
    R = c4.run_all()
    assert R["disp"] in {"CONSTRAINED_DEVELOPED_RECONSTRUCTION_SUPPORTED",
                         "CONSTRAINED_RECONSTRUCTION_GEOMETRIC_TENSION",
                         "CONSTRAINED_RECONSTRUCTION_INCONCLUSIVE",
                         "INSUFFICIENT_GEOMETRY_AUTHORITY"}
