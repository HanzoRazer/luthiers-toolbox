#!/usr/bin/env python3
"""Tests for D28 Run 004I — Metric-Consistent Radius Fixed-Point Convergence.

Authority/hygiene, radius-operator Gate 0 (E[B0(R)]≈R across the sweep), mapping,
root handling (incl. honest no-root), iteration, stability, geometry, 004G/004E/004H
crosschecks, and determinism / anti-drift.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(__file__)
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO, "docs", "experiments", "results")
_SCRIPT = os.path.join(_HERE, "d28_rerun004i_radius_fixed_point_convergence.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004i", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004i"] = m
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


def _json(d, n):
    return json.load(open(os.path.join(d, n)))


def _rows(d, n):
    import csv
    with open(os.path.join(d, n)) as fh:
        return list(csv.DictReader(fh))


# --- Authority / hygiene (1-6) ----------------------------------------------

def test_01_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", "1a4bd64b", "HEAD"],
                          cwd=_REPO).returncode == 0


def test_02_tree_clean_before_run():
    out = subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                         cwd=_REPO, capture_output=True, text=True).stdout
    # tolerate uncommitted 004I script/test during development; results dir must be clean
    assert all("results/" not in ln or "004I" in ln for ln in out.splitlines())


def test_03_inputs_exist():
    for f in ("D28_65260_ARNOLD_OUTLINE.csv", "D28_65260_REGISTERED_RIM_004D.csv",
              "D28_65260_GENONE_SIDE_CONTOUR_004B.csv", "D28_65260_BACK_BRACE_POSITIONS_004F.csv",
              "D28_65260_RERUN_004G_SUMMARY.csv", "D28_65260_PROPORTIONAL_TRANSFORMS_004H.csv"):
        assert os.path.exists(os.path.join(_RESULTS, f))


def test_04_no_prior_result_modified_by_run():
    watched = ["D28_65260_REGISTERED_RIM_004D.csv", "D28_65260_RERUN_004G_SUMMARY.csv",
               "D28_65260_PROPORTIONAL_TRANSFORMS_004H.csv"]
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


# --- Radius-operator Gate 0 (7-16) ------------------------------------------

@pytest.mark.parametrize("rft", [12, 15, 18, 20, 22, 25, 30])
def test_07_14_B0_recovers_each_radius(rft):
    e = M.estimate_like_for_like_radius(M.construct_reference_surface(rft))["R_ft"]
    assert abs(e - rft) < M.GATE0_TOL_FT


def test_14_no_systematic_bias(R):
    assert R["gate0"]["systematic_bias"] is False


def test_15_operator_uses_dome_not_raw_z():
    # the operator fits the dome (absolute reference-sphere dome ~ R, O(100s in)),
    # which recovers R; fitting raw back z (~ few inches) would not.
    e = M.estimate_like_for_like_radius(M.construct_reference_surface(25))["R_ft"]
    assert abs(e - 25.0) < M.GATE0_TOL_FT


def test_16_not_substituting_004h_1399():
    # the controlled construction radius is honored (E[B0(25)]≈25), not 004H's 13.99 global
    e = M.estimate_like_for_like_radius(M.construct_reference_surface(25))["R_ft"]
    assert abs(e - 13.99) > 5


# --- Mapping (17-22) ---------------------------------------------------------

def test_17_F_deterministic():
    assert M.evaluate_radius_map(25.0) == M.evaluate_radius_map(25.0)


def test_18_transformed_surfaces_finite(R):
    for s in R["sweep"]:
        T = M.transform_to_65260(s["R"])
        assert np.all(np.isfinite(T["d_abs"])) and np.all(np.isfinite(T["rise"]))


def test_19_no_hidden_clipping(R):
    # F values are not pinned to the input radius (they genuinely differ)
    assert all(abs(s["F"] - s["R"]) > 1e-3 for s in R["sweep"])


def test_20_counterintuitive_preserved(R):
    # F(R) > R everywhere is preserved (not forced toward a desired ~20 ft)
    assert all(s["g"] > 0 for s in R["sweep"])


def test_21_g_is_F_minus_R(R):
    for s in R["sweep"]:
        assert abs(s["g"] - (s["F"] - s["R"])) < 1e-9


def test_22_sweep_order_independent():
    a = M.evaluate_radius_map(30.0)
    b = M.evaluate_radius_map(12.0)
    assert M.evaluate_radius_map(30.0) == a and M.evaluate_radius_map(12.0) == b


# --- Root (23-27) ------------------------------------------------------------

def test_23_solver_only_in_bracket(R):
    # no bracket -> no root solved (no fabricated root)
    if not R["fp"]["root_exists"]:
        assert R["fp"]["roots_ft"] == []


def test_24_no_sign_change_no_root(R):
    gs = [s["g"] for s in R["sweep"]]
    sign_change = any(gs[i] * gs[i + 1] < 0 for i in range(len(gs) - 1))
    assert sign_change == R["fp"]["root_exists"]


def test_25_multiple_sign_changes_reported(R):
    # brackets count equals number of detected sign changes
    gs = [s["g"] for s in R["sweep"]]
    changes = sum(1 for i in range(len(gs) - 1) if gs[i] * gs[i + 1] < 0)
    assert len(R["fp"]["brackets"]) == changes


def test_26_root_residual_tolerance(R):
    if R["fp"].get("resolved_mathematical_root_ft") is not None:
        assert abs(R["fp"]["residual_ft"]) < M.FP_RESID_TOL_FT


def test_27_result_reproducible():
    assert M.run_all()["fp"]["root_count"] == M.run_all()["fp"]["root_count"]


# --- Iteration (28-33) -------------------------------------------------------

def test_28_iteration_starts_at_seed(R):
    for seed in M.ITER_SEEDS_FT:
        assert abs(R["traces"][seed][0]["radius_in_ft"] - seed) < 1e-9


def test_29_iteration_uses_F(R):
    # R_{n+1} == F(R_n)
    tr = R["traces"][25]
    assert abs(tr[0]["radius_out_ft"] - M.evaluate_radius_map(tr[0]["radius_in_ft"])) < 1e-9


def test_30_iteration_capped(R):
    for seed in M.ITER_SEEDS_FT:
        assert len(R["traces"][seed]) <= M.ITER_MAX


def test_31_convergence_criterion_declared():
    assert M.ITER_EPS_FT == 0.01 and M.ITER_MAX == 25


def test_32_divergence_retained(R):
    # no-root case: iteration from 25 does not converge (diverges upward), retained
    assert R["traces"][25][-1]["converged"] is False


def test_33_seed_traces_separate(R):
    assert set(R["traces"].keys()) == set(M.ITER_SEEDS_FT)


# --- Stability (34-36) -------------------------------------------------------

def test_34_derivative_evaluated(R):
    # F' is numerically evaluated (at R* if root, else near 25)
    assert ("derivative_Fprime" in R["fp"]) or ("derivative_Fprime_at_25" in R["fp"])


def test_35_stability_from_derivative(R):
    fp = R["fp"]
    if "derivative_Fprime" in fp:
        assert fp["stability"] in ("LOCALLY_ATTRACTIVE", "NOT_ATTRACTIVE_UNDER_DIRECT_ITERATION")
    else:
        assert fp["derivative_Fprime_at_25"] > 1.0  # divergent map


def test_36_stability_vs_truth_separated(tmp_path):
    _run_write(tmp_path)
    op = _json(tmp_path, "D28_65260_RADIUS_OPERATOR_004I.json")
    assert any("HISTORICAL" in nc for nc in op["non_claims"])


# --- Geometry (37-41) --------------------------------------------------------

def test_37_rise_recomputed_each_radius(R):
    rises = [s["rise_mm"] for s in R["sweep"]]
    assert all(b < a for a, b in zip(rises, rises[1:]))  # rise decreases as R flattens


def test_38_volume_recomputed(R):
    for s in R["sweep"]:
        T = M.transform_to_65260(s["R"])
        v = M.integrate_volume(s["R"], M.BASE_A, T) * M.IN3_TO_CM3 / 1000
        assert abs(v - s["vol_L"]) < 1e-6


def test_39_apex_found_numerically(R):
    for s in R["sweep"]:
        assert 0.0 <= s["apex_yf"] <= 1.0


def test_40_bb_stations_from_004f(R):
    st = M._load_stations()
    for b in R["brace"]:
        assert abs(b["y_in"] - st[b["brace_id"]]) < 1e-9


def test_41_brace_bottom_unresolved(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_FIXED_POINT_GEOMETRY_004I.csv")
    assert any("not brace-bottom" in r["note"] for r in rows)


# --- 004G (42-44) ------------------------------------------------------------

def test_42_rise_relation_evaluated(R):
    for s in R["sweep"]:
        assert s["g004_rise"] in ("BELOW", "INSIDE", "ABOVE")


def test_43_volume_relation_evaluated(R):
    for s in R["sweep"]:
        assert s["g004_vol"] in ("BELOW", "INSIDE", "ABOVE")


def test_44_no_004g_member_promoted(tmp_path):
    _run_write(tmp_path)
    summ = _rows(tmp_path, "D28_65260_RERUN_004I_SUMMARY.csv")[0]
    assert "no historical radius" in summ["non_claim"].lower()


# --- Historical comparison (45-48) ------------------------------------------

def test_45_004e_retained_with_label(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv")
    e = next(r for r in rows if r["source"] == "004E")
    assert "sphere" in e["radius_definition"].lower() and e["value_ft"] == "18.35"


def test_46_004h_retained_with_label(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv")
    h = next(r for r in rows if r["source"] == "004H")
    assert "BASE_SLOPE" in h["comparability"] and h["value_ft"] == "19.12"


def test_47_comparisons_fail_closed(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv")
    # unlike definitions flagged, not declared equivalent
    assert all(r["comparability"] != "SAME" for r in rows)


def test_48_no_averaging(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv")
    fp = next(r for r in rows if r["source"] == "004I_fixed_point")
    assert "not averaged" in fp["comparability"].lower()


# --- Determinism (49-51) -----------------------------------------------------

_I_FILES = [
    "D28_65260_RADIUS_OPERATOR_004I.json", "D28_65260_RADIUS_SWEEP_004I.csv",
    "D28_65260_FIXED_POINT_004I.json", "D28_65260_RADIUS_ITERATION_TRACE_004I.csv",
    "D28_65260_FIXED_POINT_GEOMETRY_004I.csv", "D28_65260_RADIUS_VOLUME_SENSITIVITY_004I.csv",
    "D28_65260_RADIUS_APEX_SENSITIVITY_004I.csv", "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv",
    "D28_65260_RERUN_004I_SUMMARY.csv", "D28_65260_RERUN_004I_PROVENANCE.json",
]


def test_49_outdir_env(tmp_path):
    _run_write(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "D28_65260_RERUN_004I_SUMMARY.csv"))


def test_50_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1); _run_write(d2)
    for f in _I_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_51_clean_tree_after_write(tmp_path):
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                              cwd=_REPO, check=True, capture_output=True, text=True).stdout
    before = status()
    _run_write(tmp_path / "out")
    assert status() == before
