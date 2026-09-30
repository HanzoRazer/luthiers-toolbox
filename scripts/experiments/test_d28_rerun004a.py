"""
Focused, hardware-free tests for Run 004A (original side-measurement authority
cleanup). Consumes the committed Rerun 003 outline artifact; touches no PDF,
production code, or historical value.
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


a4 = _load("d28_004a", "d28_rerun004a_source_authority_cleanup.py")


def test_active_station_list_exact():
    assert a4.ACTIVE_STATIONS == [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0]


def test_10p5_absent_from_active_stations():
    assert 10.5 not in a4.ACTIVE_STATIONS
    assert a4.LEGACY_WAIST_STATION == 10.5          # retained only as legacy evidence


def test_30p4375_absent_from_active_stations():
    assert 30.4375 not in a4.ACTIVE_STATIONS
    assert a4.LEGACY_BOTTOM_STATION == 30.4375      # retained only as legacy evidence


def test_waist_height_preserved():
    assert a4.WAIST_HEIGHT == 4.220


def test_waist_position_is_geometric():
    # predict_waist uses the geometric minimum-width point from the Rerun 003 outline.
    gw = a4.r3.geometric_waist(a4.L_CAL)
    P = a4.r3.solve_high_point(a4.L_CAL, a4.B_BUTT, a4.S_SHOULDER, 180.0)
    D = math.hypot(gw["x"], gw["y"] - (a4.L_CAL - P))
    expected = a4.r3.solve_side_height(a4.B_BUTT, 180.0, P, D, 0.0, 0.0)
    got, _ = a4.predict_waist(a4.L_CAL, 180.0)
    assert abs(got - expected) < 1e-9


def test_bottom_height_preserved():
    assert a4.BOTTOM_HEIGHT == 4.720


def test_bottom_location_is_geometric_tail():
    y, x, s = a4.r3.developed_arclen(a4.L_CAL)
    # predict_bottom evaluates at the last outline point (geometric tail).
    assert y[-1] == pytest.approx(a4.L_CAL, abs=1e-6)
    assert isinstance(a4.predict_bottom(a4.L_CAL, 180.0), float)


def test_no_normalized_30p4375_mapping_used():
    # Mapping is LITERAL: station 12 maps to developed arc ~12 (not 12/30.4375*26.73=10.5).
    x, y, status = a4.map_station(a4.L_CAL, 12.0)
    yy, xx, s = a4.r3.developed_arclen(a4.L_CAL)
    arc_at_point = float(np.interp(y, yy, s))   # arc length at mapped y
    assert abs(arc_at_point - 12.0) < 0.2       # literal
    assert abs(arc_at_point - (12.0 / 30.4375) * a4.S_CAD_TOTAL) > 1.0   # not normalized
    import json
    rec = json.loads(open(_json_after_write()).read()) if os.path.exists(_json_after_write()) else None
    # authority record (if written) declares no normalized mapping
    if rec is not None:
        assert rec["normalized_30p4375_mapping_used"] is False


def _json_after_write():
    return a4.AUTH_JSON


def test_deep_comparison_only():
    assert a4.DRAWING_DEEP == 4.4375
    assert 4.4375 not in set(a4.ANCHORS.values())
    assert 4.4375 not in set(a4.STATIONED.values())


def test_anchors_9_12_15():
    assert set(a4.ANCHORS) == {9.0, 12.0, 15.0}


def test_historical_heights_not_altered():
    assert a4.STATIONED == {0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240,
                            15.0: 4.350, 18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670}


def test_prior_run_result_files_untouched():
    r = a4._RESULTS
    for f in ("D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv",
              "D28_65260_STATION_DATUM_AUDIT_003A_SUMMARY.csv",
              "D28_65260_ARNOLD_OUTLINE.csv"):
        assert os.path.exists(os.path.join(r, f))
    assert "004A" in a4.CONV_CSV and "004A" in a4.SUM_CSV


def test_invalid_geometry_fails_closed():
    assert a4.admissible(20.0, 500.0) is False
    H, D, status = a4.predict_station(20.0, 500.0, 12.0)   # must not raise
    assert isinstance(H, float)


def test_station_27_is_out_of_domain():
    _, _, status = a4.map_station(a4.L_CAL, 27.0)
    assert status == "OUT_OF_DOMAIN"
    _, _, s24 = a4.map_station(a4.L_CAL, 24.0)
    assert s24 == "OK"


def test_convergence_log_is_deterministic():
    l1 = a4.Logger(); l2 = a4.Logger()
    a4.inverse(l1, 12.0); a4.inverse(l2, 12.0)
    assert l1.rows == l2.rows and len(l1.rows) > 0


def test_writes_only_under_results():
    for p in (a4.AUTH_JSON, a4.CROSSWALK_CSV, a4.CONV_CSV, a4.SUM_CSV):
        assert os.path.join("docs", "experiments", "results") in os.path.normpath(p)


def test_conclusion_and_gate_vocabulary():
    logger, anch, gls, conclusion, authorize, notes = a4.run_all()
    assert conclusion in {"SINGLE_RADIUS_MODEL_MISMATCH_PERSISTS",
                          "LEGACY_STATION_ASSIGNMENTS_CAUSED_PRIOR_FAILURE",
                          "SOURCE_CLEANUP_INCONCLUSIVE"}
    assert isinstance(authorize, bool)
