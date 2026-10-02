"""
Focused, hardware-free tests for the D28 station-datum audit (Rerun 003A).
Guards the audit invariants (Step 14). Consumes the committed Rerun 003 outline
artifact; touches no PDF, production code, or historical value.
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


aud = _load("d28_003a", "d28_rerun003a_station_datum_audit.py")


def test_literal_mapping_reports_out_of_domain_not_silent_clamp():
    # Stations beyond the plan-view half-perimeter (26.73) must flag OUT_OF_DOMAIN.
    _, _, _, st27 = aud.map_station(aud.L_CAL, 27.0, "A_literal")
    _, _, _, st30 = aud.map_station(aud.L_CAL, 30.4375, "A_literal")
    _, _, _, st12 = aud.map_station(aud.L_CAL, 12.0, "A_literal")
    assert st27 == "OUT_OF_DOMAIN" and st30 == "OUT_OF_DOMAIN"
    assert st12 == "OK"


def test_normalized_endpoints_map_exactly():
    _, _, s0, _ = aud.map_station(aud.L_CAL, 0.0, "C_normalized")
    _, _, sT, _ = aud.map_station(aud.L_CAL, 30.4375, "C_normalized")
    assert abs(s0 - 0.0) < 1e-9
    assert abs(sT - aud.S_CAD_TOTAL) < 1e-6      # 30.4375 -> CAD half-perimeter exactly


def test_normalized_mapping_deterministic():
    a = [aud.map_station(aud.L_CAL, s, "C_normalized") for s in aud.STATIONS]
    b = [aud.map_station(aud.L_CAL, s, "C_normalized") for s in aud.STATIONS]
    assert a == b


def test_waist_4220_is_validation_only():
    assert aud.WAIST_SIDE_HEIGHT == 4.220
    assert 4.220 not in set(aud.ANCHORS.values())


def test_deep_4p4375_is_comparison_only():
    assert aud.DRAWING_DEEP == 4.4375
    assert 4.4375 not in set(aud.ANCHORS.values())
    assert 4.4375 not in set(aud.ARNOLD.values())


def test_anchors_are_9_12_15():
    assert set(aud.ANCHORS) == {9.0, 12.0, 15.0}


def test_3d_arc_uses_euclidean_xyz():
    rim = aud.rim_3d_length(aud.L_CAL)
    assert rim["rim_3d"] >= rim["plan_arc"]                       # 3D >= plan
    assert 0.0 <= rim["increase"] < 0.5                           # small, side-height only
    # explains only a tiny fraction of the gap to Arnold's span
    assert rim["explains_pct"] < 5.0


def test_no_model_mutates_the_arnold_outline():
    y0 = aud.r3._Y.copy(); h0 = aud.r3._HW_S.copy()
    for model in ("A_literal", "C_normalized"):
        for s in aud.STATIONS:
            aud.map_station(aud.L_CAL, s, model)
        aud.inverse(model, 12.0)
    assert np.array_equal(aud.r3._Y, y0) and np.array_equal(aud.r3._HW_S, h0)


def test_no_model_changes_historical_side_heights():
    expected = {0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240, 15.0: 4.350,
                18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670, 30.4375: 4.720}
    assert aud.ARNOLD == expected


def test_invalid_inverse_geometry_fails_closed():
    assert aud.admissible(20.0, 500.0) is False        # large R -> P<0
    H, D, P = aud.predict(20.0, 500.0, 12.0, "A_literal")   # must not raise
    assert isinstance(H, float) and P < 0


def test_prior_run_result_files_untouched_and_distinct_names():
    r = aud._RESULTS
    for f in ("D28_65260_SIDE_INVERSE_RERUN_002_SUMMARY.csv",
              "D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv",
              "D28_65260_ARNOLD_OUTLINE.csv"):
        assert os.path.exists(os.path.join(r, f))
    assert "003A" in aud.AUDIT_CSV and "003A" in aud.SUM_CSV


def test_audit_writes_only_under_results():
    for p in (aud.AUDIT_CSV, aud.SUM_CSV):
        assert os.path.join("docs", "experiments", "results") in os.path.normpath(p)


def test_audit_and_parent_dispositions_from_allowed_vocab():
    res = aud.run_audit()
    audit_conc, parent, _ = aud.classify(res)
    assert audit_conc in {"LITERAL_PLAN_ARC_SUPPORTED", "NORMALIZED_STATION_SUPPORTED",
                          "THREE_DIMENSIONAL_RIM_SUPPORTED", "OTHER_SOURCE_SUPPORTED_DATUM",
                          "DATUM_DEFINITION_UNRESOLVED"}
    assert parent in {"CONFIRMED", "STRENGTHENED", "PROVISIONAL", "SUPERSEDED"}
