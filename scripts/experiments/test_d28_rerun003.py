"""
Focused, hardware-free tests for D28 SIDE INVERSE RERUN 003 (Arnold outline
authority). They consume the committed extracted outline artifact (no PDF, no
production code) and guard the rerun's governing invariants (Step 13).
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


exp = _load("d28_r3", "d28_side_inverse_rerun003.py")
ext = _load("d28_r3x", "d28_rerun003_extract.py")


def test_no_generic_waist_y_norm_044_as_authority():
    """The parametric waist_y_norm must not be an authority constant; the waist
    is derived from the outline (its y/L is ~0.33, not the parametric 0.44)."""
    src = open(os.path.join(_HERE, "d28_side_inverse_rerun003.py")).read()
    assert "WAIST_Y_NORM" not in src              # no parametric waist-position constant
    gw = exp.geometric_waist(exp._L_CAL)
    assert abs(gw["y_norm"] - 0.44) > 0.05         # derived (~0.326), not 0.44


def test_waist_from_arnold_outline_minimum():
    """Waist is the derived interior minimum of the extracted outline, narrower
    than both bouts, and agrees with the committed extraction landmarks."""
    gw = exp.geometric_waist(exp._L_CAL)
    lm = exp._META["landmarks"]
    assert gw["x"] * 2 == pytest.approx(lm["waist"]["full_width_in"], abs=0.05)
    assert gw["x"] * 2 < lm["upper_bout"]["full_width_in"]     # narrower than upper bout
    assert gw["x"] * 2 < lm["lower_bout"]["full_width_in"]     # narrower than lower bout
    assert 8.0 < gw["s_waist"] < 12.0                          # derived developed station


def test_4220_is_waist_side_height_validation():
    assert exp.WAIST_SIDE_HEIGHT == 4.220


def test_4p4375_is_comparison_only_not_a_side_height_or_anchor():
    assert exp.DRAWING_DEEP == 4.4375
    assert 4.4375 not in set(exp.ARNOLD_SIDE_HEIGHT_IN.values())
    assert 4.4375 not in set(exp.HARD_ANCHORS.values())      # anchors are 4.240/4.085/4.350
    assert exp.HARD_ANCHORS[exp.PRIMARY_ANCHOR] == 4.240


def test_developed_station_distinct_from_euclidean_D():
    L, R = exp._L_CAL, 180.0
    for s in (3.0, 9.0, 15.0, 21.0):
        _, D, _ = exp.predict_at(L, R, s)
        assert abs(D - s) > 0.5


def test_arclength_integration_converges_with_resolution():
    _, _, s1 = exp.developed_arclen(exp._L_CAL, resolution=len(exp._Y))
    _, _, s2 = exp.developed_arclen(exp._L_CAL, resolution=2 * len(exp._Y))
    _, _, s4 = exp.developed_arclen(exp._L_CAL, resolution=4 * len(exp._Y))
    assert abs(s2[-1] - s1[-1]) < 0.01
    assert abs(s4[-1] - s2[-1]) < 0.01


def test_symmetry_zero_by_construction_and_raw_outline_preserved():
    cal = exp._META["calibration"]
    assert cal["symmetry_mode"] == "symmetric_by_construction"
    assert cal["symmetry_discrepancy_in"] == 0.0
    # raw extracted outline is the committed artifact (monotone y from neck=0).
    assert exp._Y[0] == 0.0 and exp._Y[-1] == pytest.approx(exp._L_CAL)


def test_fixedL_and_normalized_variants_are_separate():
    # A1 fixes L to the extracted body length; A2 floats L. Distinct by design.
    logger = exp.Logger()
    a1 = exp.analysis_A1(logger, exp.PRIMARY_ANCHOR)
    assert a1.variant == "A1_fixedL" and abs(a1.L - exp._L_CAL) < 1e-9
    a2 = exp.analysis_A2(logger, exp.PRIMARY_ANCHOR, n_R=6)
    assert a2.variant == "A2_floatL"


def test_invalid_geometry_fails_closed():
    adm, reasons = exp.is_admissible(exp._L_CAL, 500.0)   # large R -> P<0
    assert adm is False and any("P<0" in r for r in reasons)
    H, D, _ = exp.predict_at(exp._L_CAL, 500.0, 12.0)     # must not raise
    assert isinstance(H, float)


def test_convergence_log_is_deterministic():
    l1 = exp.Logger(); l2 = exp.Logger()
    exp.integration_convergence(l1, exp._L_CAL); exp.analysis_A1(l1, exp.PRIMARY_ANCHOR)
    exp.integration_convergence(l2, exp._L_CAL); exp.analysis_A1(l2, exp.PRIMARY_ANCHOR)
    assert l1.rows == l2.rows and len(l1.rows) > 0


def test_writes_only_under_docs_experiments_results():
    for p in (exp.CONV_CSV, exp.SUM_CSV, exp.OUTLINE_CSV, ext.PROVENANCE_JSON):
        assert os.path.join("docs", "experiments", "results") in os.path.normpath(p)
    # source PDFs are NOT vendored into the repo
    manifest = __import__("json").load(open(ext.PROVENANCE_JSON))
    for srcrec in manifest["sources"]:
        assert srcrec["repository_copy"] is False


def test_rerun002_results_preserved_and_separate_filenames():
    r = exp._RESULTS
    assert os.path.exists(os.path.join(r, "D28_65260_SIDE_INVERSE_RERUN_002_CONVERGENCE.csv"))
    assert os.path.exists(os.path.join(r, "D28_65260_SIDE_INVERSE_RERUN_002_SUMMARY.csv"))
    assert "RERUN_003" in exp.CONV_CSV and "RERUN_002" not in exp.CONV_CSV


def test_disposition_from_allowed_vocabulary():
    allowed = {"CONVERGES_AND_SUPPORTS_20IN", "CONVERGES_BUT_NOT_20IN",
               "UNDERDETERMINED", "SPHERICAL_MODEL_MISMATCH",
               "INSUFFICIENT_GEOMETRY_AUTHORITY"}
    d, _ = exp.classify({}, {}, [], floorH=4.30)
    assert d in allowed
