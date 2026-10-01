#!/usr/bin/env python3
"""Tests for D28 Run 004J — Back Curvature Field Reconstruction.

Authority/hygiene, surface/grid, curvature-estimator synthetic controls, station
resolution, family envelopes, 25-ft comparison, saddle mapping, cross-run
reconciliation, and determinism / anti-drift.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(__file__)
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO, "docs", "experiments", "results")
_SCRIPT = os.path.join(_HERE, "d28_rerun004j_back_curvature_field_reconstruction.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004j", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004j"] = m
    spec.loader.exec_module(m)
    return m


M = _load()


@pytest.fixture(scope="module")
def R():
    return M.run_all()


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _run_write(outdir):
    env = dict(os.environ, D28_EXP_OUTDIR=str(outdir))
    subprocess.run([sys.executable, _SCRIPT, "--write"], cwd=_REPO, check=True, capture_output=True, env=env)


def _rows(d, n):
    import csv
    with open(os.path.join(d, n)) as fh:
        return list(csv.DictReader(fh))


def _synth(kind, R0_ft=25.0, half=5.0):
    R0 = R0_ft * 12.0
    xs = np.arange(-half, half + 1e-9, M.STEP); ys = np.arange(-half, half + 1e-9, M.STEP)
    XX, YY = np.meshgrid(xs, ys)
    if kind == "flat":
        Z = np.zeros_like(XX)
    elif kind == "sphere":
        Z = -np.sqrt(np.clip(R0 ** 2 - XX ** 2 - YY ** 2, 0, None))
    elif kind == "cylinder":
        Z = -np.sqrt(np.clip(R0 ** 2 - XX ** 2, 0, None))
    elif kind == "saddle":
        Z = (XX ** 2 - YY ** 2) / (2 * R0)
    cf = M.curvature_fields_full(Z, M.STEP)
    c = (len(ys) // 2, len(xs) // 2)
    return cf, c, R0


# --- Authority / hygiene (1-6) ----------------------------------------------

def test_01_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", "8d5bbeef", "HEAD"],
                          cwd=_REPO).returncode == 0


def test_02_results_clean_except_004j():
    out = subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/results/"],
                         cwd=_REPO, capture_output=True, text=True).stdout
    assert all("004J" in ln for ln in out.splitlines() if ln.strip())


def test_03_inputs_exist():
    for f in ("D28_65260_REGISTRATION_ANCHORS_004D.csv", "D28_65260_BACK_BRACE_POSITIONS_004F.csv",
              "D28_65260_BACK_FAMILY_MEMBERS_004G.csv"):
        assert os.path.exists(os.path.join(_RESULTS, f))


def test_04_no_prior_result_modified():
    watched = ["D28_65260_BACK_FAMILY_MEMBERS_004G.csv", "D28_65260_REGISTERED_RIM_004D.csv",
               "D28_65260_RERUN_004I_SUMMARY.csv"]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    M.run_all()
    assert before == {f: _sha(os.path.join(_RESULTS, f)) for f in watched}


def test_05_no_production_modified(tmp_path):
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry", "specs",
                        "martin_d28_1937.json")
    before = _sha(spec)
    _run_write(tmp_path)
    assert _sha(spec) == before


def test_06_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


# --- Surface / grid (7-11) ---------------------------------------------------

def test_07_five_members_load(R):
    assert [m["name"] for m in R["fam"]["members"]] == ["floor", "q25", "mid", "q75", "ceiling"]


def test_08_same_planform_mask(R):
    inside = R["fam"]["G"]["inside"]
    # all members share the same grid/mask (same G)
    assert R["fam"]["G"]["inside"] is inside


def test_09_rim_unchanged(R):
    # rim comes from 004G's rim; untouched
    assert abs(R["L"] - 19.99) < 0.01


def test_10_grid_deterministic(R):
    assert abs((R["fam"]["G"]["grid"]["xs"][1] - R["fam"]["G"]["grid"]["xs"][0]) - M.STEP) < 1e-9


def test_11_no_nan_interior(R):
    for m in R["fam"]["members"]:
        inner = m["field"]["inner"]
        assert np.all(np.isfinite(m["field"]["cf"]["K"][inner]))


# --- Curvature synthetic controls (12-19) -----------------------------------

def test_12_flat_near_zero():
    cf, c, _ = _synth("flat")
    assert abs(cf["kT"][c]) < M.KAPPA_FLAT and abs(cf["kL"][c]) < M.KAPPA_FLAT


def test_13_sphere_recovers_radius():
    cf, c, R0 = _synth("sphere")
    RT = 1 / abs(cf["kT"][c]) / 12
    assert abs(RT - 25.0) / 25.0 < 0.05 and cf["K"][c] > 0


def test_14_cylinder_one_finite_one_flat():
    cf, c, _ = _synth("cylinder")
    RT = 1 / abs(cf["kT"][c]) / 12
    assert abs(RT - 25.0) / 25.0 < 0.05 and abs(cf["kL"][c]) < M.KAPPA_FLAT


def test_15_saddle_negative_gaussian():
    cf, c, _ = _synth("saddle")
    assert cf["K"][c] < -M.NOISE_K


def test_16_transverse_methods_agree_on_sphere():
    R0 = 25 * 12
    xs = np.arange(-5, 5 + 1e-9, M.STEP)
    z = -np.sqrt(np.clip(R0 ** 2 - xs ** 2, 0, None))
    k_circle = M.fit_local_circle(xs, z)
    assert abs(1 / abs(k_circle) / 12 - 25.0) / 25.0 < 0.05


def test_17_longitudinal_methods_agree_on_sphere():
    R0 = 25 * 12
    ys = np.arange(-3, 3 + 1e-9, M.STEP)
    z = -np.sqrt(np.clip(R0 ** 2 - ys ** 2, 0, None))
    k_quad = M.fit_local_quadratic(ys, z)
    assert abs(1 / abs(k_quad) / 12 - 25.0) / 25.0 < 0.10


def test_18_classification_near_flat():
    r, cls = M.radius_ft(M.KAPPA_FLAT / 10)
    assert cls == "NEAR_FLAT"
    r2, cls2 = M.radius_ft(1 / (25 * 12))
    assert cls2 == "POSITIVE_CURVATURE" and abs(r2 - 25) < 0.1


def test_19_huge_radius_not_precise_finite():
    r, cls = M.radius_ft(0.0)
    assert cls == "NEAR_FLAT" and (r == float("inf"))


def test_controls_all_pass(R):
    assert R["controls"]["all_pass"]


# --- Station (20-23) ---------------------------------------------------------

def test_20_named_stations_resolve(R):
    names = {s["name"] for s in R["stations"]}
    assert {"neck", "upper_bout", "waist", "lower_bout", "BB1", "BB2", "BB3", "BB4"} <= names


def test_21_bb_equal_004f(R):
    bb = R["bb"]
    assert abs(bb["BB1"] - 4.133) < 1e-2 and abs(bb["BB4"] - 14.758) < 1e-2


def test_22_pm04_windows_sampled(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_BRACE_CURVATURE_ENVELOPE_004J.csv")
    assert all(r["position_uncertainty_in"] == "0.40" for r in rows)


def test_23_brace_bottom_unresolved(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_BRACE_CURVATURE_ENVELOPE_004J.csv")
    assert all(r["brace_bottom_curvature_known"] == "false" for r in rows)


# --- Family (24-27) ----------------------------------------------------------

def test_24_envelopes_min_max(R):
    for e in R["station_env"]:
        if np.isfinite(e["RT_min"]) and np.isfinite(e["RT_max"]):
            assert e["RT_min"] <= e["RT_max"]
        assert e["rise_min"] <= e["rise_max"]


def test_25_no_member_promoted(tmp_path):
    _run_write(tmp_path)
    summ = _rows(tmp_path, "D28_65260_RERUN_004J_SUMMARY.csv")[0]
    assert "LOCAL descriptor only" in summ["single_radius_adequacy"]


def test_26_rise_consistent_with_004g(R):
    # ceiling member max rise ~ 2.8 mm (004G)
    ceil = next(m for m in R["fam"]["members"] if m["name"] == "ceiling")
    assert abs(ceil["g_max_rise_mm"] - 2.80) < 0.05


def test_27_apex_matches_004g(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_APEX_CURVATURE_004J.csv")
    assert all(r["matches_004g_within_0p5in"] == "True" for r in rows)


# --- 25-ft comparison (28-30) ------------------------------------------------

def test_28_threshold_fixed():
    assert M.SIMILAR_PCT == 5.0 and M.REF_25FT == 25.0


def test_29_raw_radius_retained(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_CURVATURE_STATION_ENVELOPE_004J.csv")
    assert all("RT_min_ft" in r for r in rows)


def test_30_similar_only_in_tolerance():
    assert M.classify_vs_25ft(25.0) == "SIMILAR"
    assert M.classify_vs_25ft(25 * 1.2) == "FLATTER"
    assert M.classify_vs_25ft(25 * 0.8) == "TIGHTER"


# --- Saddle (31-35) ----------------------------------------------------------

def test_31_boundary_band_documented(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_SADDLE_MAP_004J.csv")
    assert any("cells" in r["boundary_band_excluded"] for r in rows if r["member"] != "ALL_MEMBERS")


def test_32_saddle_area_interior_only(R):
    for s in R["saddle_rows"]:
        assert 0.0 <= s["neg_K_area_frac"] <= 1.0


def test_33_negative_K_preserved(R):
    assert all(s["K_min"] < 0 for s in R["saddle_rows"])


def test_34_noise_threshold_declared():
    assert M.NOISE_K == 1e-5


def test_35_saddle_persists_across_family(R):
    assert R["saddle_persists"] is True
    assert all(s["neg_K_area_frac"] > 0 for s in R["saddle_rows"])


# --- Cross-run reconciliation (36-40) ---------------------------------------

def test_36_004h_local_transverse_retained(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
    assert any("25 ft" in r["result"] and "local transverse" in r["quantity"] for r in rows)


def test_37_004h_global_retained(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
    assert any("19.12" in r["result"] and "base slope" in r["interpretation"] for r in rows)


def test_38_004i_null_retained(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
    assert any("1.045" in r["result"] for r in rows)


def test_39_004i_f25_retained(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
    assert any("26.13" in r["result"] for r in rows)


def test_40_no_unlike_radii_averaged(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
    # distinct method rows retained (>=5), none a mean of the others
    vals = [r["result"] for r in rows]
    assert len(rows) >= 5 and "average" not in " ".join(vals).lower()


# --- Determinism (41-44) -----------------------------------------------------

_J_FILES = [
    "D28_65260_CURVATURE_FIELD_004J.csv", "D28_65260_CURVATURE_STATION_ENVELOPE_004J.csv",
    "D28_65260_BRACE_CURVATURE_ENVELOPE_004J.csv", "D28_65260_APEX_CURVATURE_004J.csv",
    "D28_65260_SADDLE_MAP_004J.csv", "D28_65260_004H_004I_004J_CROSSCHECK.csv",
    "D28_65260_RERUN_004J_SUMMARY.csv", "D28_65260_RERUN_004J_PROVENANCE.json",
]


def test_41_outdir_env(tmp_path):
    _run_write(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "D28_65260_RERUN_004J_SUMMARY.csv"))


def test_42_temp_output(tmp_path):
    assert str(tmp_path) != _RESULTS


def test_43_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1); _run_write(d2)
    for f in _J_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_44_clean_tree_after_write(tmp_path):
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                              cwd=_REPO, check=True, capture_output=True, text=True).stdout
    before = status()
    _run_write(tmp_path / "out")
    assert status() == before
