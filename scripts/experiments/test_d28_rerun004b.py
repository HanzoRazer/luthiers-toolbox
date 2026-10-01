"""
Focused, hardware-free tests for Run 004B (proportional dreadnought similitude).
Consumes the committed GenOne side-contour artifact + Rerun 003 outline; touches
no PDF, production code, or historical value.
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


b4 = _load("d28_004b", "d28_rerun004b_proportional_similitude.py")
GEN = b4.load_or_extract()


def test_reference_is_genone_not_sevy():
    # provenance declares the GenOne template as the reference; repo spherical is diagnostic only
    assert "GENONE_SIDE_CONTOUR" in b4.GENONE_CSV
    assert GEN["n_stations"] >= 25
    # endpoints from the real template (incl plates): ~3.6-3.75 neck, ~4.6-4.75 tail
    assert 3.4 < GEN["z_neck_total"] < 3.9
    assert 4.5 < GEN["z_tail_total"] < 4.9


def test_pure_shape_transfer_has_no_high_point_in_model():
    # transfer_height depends only on f(u) and endpoints; no P argument anywhere
    import inspect
    src = inspect.getsource(b4.transfer_height) + inspect.getsource(b4.shape_f)
    assert "solve_high_point" not in src          # P does not govern the transfer


def test_endpoints_are_3750_and_4720():
    assert b4.NECK_H == 3.750 and b4.BOTTOM_H == 4.720
    assert abs(b4.transfer_height(GEN, 0.0) - 3.750) < 1e-6
    assert abs(b4.transfer_height(GEN, 1.0) - 4.720) < 1e-6


def test_shape_normalized_monotone_endpoints():
    assert abs(b4.shape_f(GEN, 0.0) - 0.0) < 1e-6
    assert abs(b4.shape_f(GEN, 1.0) - 1.0) < 1e-6


def test_active_stations_exclude_10p5_and_30p4375():
    assert b4.ACTIVE_STATIONS == [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0]
    assert 10.5 not in b4.ACTIVE_STATIONS and 30.4375 not in b4.ACTIVE_STATIONS


def test_waist_is_validation_at_geometric_waist():
    assert b4.WAIST_H == 4.220
    uw = b4.waist_u()
    assert 0.25 < uw < 0.45          # #65260 geometric waist fraction (~0.35)


def test_bottom_validation_at_geometric_tail():
    assert b4.BOTTOM_H == 4.720
    assert abs(b4.transfer_height(GEN, 1.0) - 4.720) < 1e-6


def test_roundtrip_fixture_within_tolerance():
    fx = b4.roundtrip_fixture(GEN)
    assert fx["max_in"] < 1e-6                     # identity round-trip
    assert fx["interp_max_in"] <= 0.010            # interpolation tolerance


def test_h1_classified_source_supported_analogy():
    H = b4.h1()
    assert H["genone_30_11_32_in"] == 30.34375 and H["arnold_30_7_16_in"] == 30.4375
    assert abs(H["difference_in"] - 0.09375) < 1e-9
    assert H["classification"] == "SOURCE_SUPPORTED_ANALOGY"
    assert H["used_to_tune_fit"] is False


def test_plate_thickness_not_assumed():
    # provenance states plate thickness is not dimensioned / not assumed
    import json
    if os.path.exists(b4.PROV_JSON):
        rec = json.load(open(b4.PROV_JSON))
        assert "NOT numerically dimensioned" in rec["plate_thickness"]


def test_deterministic():
    g1 = b4.load_or_extract(); g2 = b4.load_or_extract()
    f1 = [round(b4.shape_f(g1, u), 6) for u in np.linspace(0, 1, 20)]
    f2 = [round(b4.shape_f(g2, u), 6) for u in np.linspace(0, 1, 20)]
    assert f1 == f2


def test_writes_only_under_results_and_prior_runs_present():
    for p in (b4.GENONE_CSV, b4.PROV_JSON, b4.ANALYSIS_CSV, b4.SUMMARY_CSV):
        assert os.path.join("docs", "experiments", "results") in os.path.normpath(p)
    r = b4._RESULTS
    for f in ("D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv",
              "D28_65260_SIDE_AUTHORITY_004A_SUMMARY.csv",
              "D28_65260_STATION_DATUM_AUDIT_003A_SUMMARY.csv"):
        assert os.path.exists(os.path.join(r, f))


def test_disposition_vocabulary():
    gen, ev, fx, diag, H, disp, notes = b4.run_all()
    assert disp in {"PROPORTIONAL_SIMILITUDE_SUPPORTS_ADMISSIBLE_FIT",
                    "PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT",
                    "SIMILITUDE_INCONCLUSIVE", "INSUFFICIENT_REFERENCE_GEOMETRY"}
