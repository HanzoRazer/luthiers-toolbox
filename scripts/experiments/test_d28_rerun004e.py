#!/usr/bin/env python3
"""Tests for D28 Run 004E — Back Surface Reconstruction from Registered Rim.

Covers source preservation, boundary exactness, sphere/fixed/compound/constrained
candidates, centerline & sections, brace QUALITATIVE_ONLY handling, GenOne
reference-only usage, the record-before-judge principle, and determinism.
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004e_back_surface_reconstruction.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004e", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004e"] = m
    spec.loader.exec_module(m)
    return m


M = _load()


@pytest.fixture(scope="module")
def R():
    return M.run_all()


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _run_write(outdir):
    """Hermetic --write: output is redirected to `outdir` (and <outdir>/REPORT.md)
    via D28_EXP_OUTDIR so committed artifacts are never touched."""
    env = dict(os.environ, D28_EXP_OUTDIR=str(outdir))
    subprocess.run([sys.executable, _SCRIPT, "--write"], cwd=_REPO, check=True,
                   capture_output=True, env=env)


# --- Source preservation (1-4) ----------------------------------------------

def test_01_rim_loads_unchanged(R):
    rim = R["rim"]
    assert len(rim["x"]) == 248
    assert abs(rim["x"][0] - 3.0858) < 1e-4
    assert abs(rim["y"][-1] - 19.9900) < 1e-4


def test_02_004c_heights_unchanged(R):
    rim = R["rim"]
    assert abs(rim["z"][0] - 3.7500) < 1e-9    # neck side height
    assert abs(rim["z"][-1] - 4.7200) < 1e-9   # tail side height


def test_03_004d_xy_unchanged(R):
    rim = R["rim"]
    assert abs(rim["x"][-1] - 4.3904) < 1e-4
    assert abs(rim["y"][0] - 0.0) < 1e-12


def test_04_prior_artifacts_untouched_by_run():
    watched = [
        "D28_65260_REGISTERED_RIM_004D.csv",
        "D28_65260_REGISTRATION_AUTHORITY_004D.json",
        "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
        "D28_65260_ARNOLD_OUTLINE.csv",
    ]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    M.run_all()
    after = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    assert before == after


# --- Boundary (5-9) ----------------------------------------------------------

def test_05_meets_neck_boundary(R):
    bnd, tps = R["bnd"], R["tps"]
    z = float(tps.zf(np.array([[bnd["side_x"][0], 0.0]]))[0])
    assert abs(z - bnd["z_neck"]) < 1e-6


def test_06_meets_waist_boundary(R):
    rim, tps, outline = R["rim"], R["tps"], R["outline"]
    yw = R["landmarks"]["waist"]
    hw = M.half_width_at(outline, yw)
    z = float(tps.zf(np.array([[hw, yw]]))[0])
    rz = float(M.rim_z_at_y(rim, np.array([yw]))[0])
    assert abs(z - rz) < 0.02


def test_07_meets_tail_boundary(R):
    bnd, tps = R["bnd"], R["tps"]
    z = float(tps.zf(np.array([[bnd["side_x"][-1], bnd["L"]]]))[0])
    assert abs(z - bnd["z_tail"]) < 1e-6


def test_08_all_rim_points_within_tol(R):
    assert R["tps"].rim_max <= M.RIM_EXACT_TOL_IN


def test_09_no_boundary_point_altered(R):
    bnd, rim = R["bnd"], R["rim"]
    # side boundary z equals the input rim z exactly
    assert np.allclose(bnd["side_z"], rim["z"])


# --- Sphere diagnostics (10-14) ---------------------------------------------

def test_10_sphere_deterministic(R):
    s2 = M.fit_single_sphere(R["bnd"])
    assert abs(s2.radius_ft - R["sphere"].radius_ft) < 1e-6


def test_11_radius_recorded_even_if_inadmissible(R):
    assert R["sphere"].radius_ft is not None and R["sphere"].radius_ft > 0


def test_12_center_recorded_outside_body(R):
    # center z is far below body (outside), recorded verbatim, not clamped
    assert R["sphere"].center[2] < 0


def test_13_no_radius_clamping(R):
    r = R["sphere"].radius_ft
    assert r not in (12, 15, 18, 20, 25, 30)  # not pinned to a sweep value


def test_14_fixed_sweep_deterministic(R):
    s2 = M.sweep_fixed_radii(R["bnd"])
    for a, b in zip(R["sweep"], s2):
        assert abs(a.rim_rmse - b.rim_rmse) < 1e-9


# --- Compound model (15-17) --------------------------------------------------

def test_15_long_trans_radii_independent(R):
    c = R["compound"]
    assert abs(c.radius_long_ft - c.radius_trans_ft) > 1.0


def test_16_exactness_only_claimed_by_tps(R):
    assert R["tps"].rim_max <= 1e-6              # TPS claims & achieves exactness
    assert R["compound"].rim_max > 1e-3          # compound is approximate (no false claim)


def test_17_no_param_replaced_by_reference(R):
    params = R["compound"].params
    # fitted radii are not the GenOne 4-6 mm numbers in disguise
    assert "inv_Rt_perin" in params and "inv_Rl_perin" in params
    assert R["compound"].radius_trans_ft not in (4.0, 6.0)


# --- Constrained surface (18-23) --------------------------------------------

def test_18_tps_deterministic(R):
    t2 = M.fit_constrained_surface(R["bnd"])
    q = np.array([[0.0, 10.0], [2.0, 5.0]])
    assert np.allclose(R["tps"].zf(q), t2.zf(q))


def test_19_no_nan_inf_interior(R):
    grid = R["grid"]
    Z = M._surface_on_grid(R["tps"].zf, grid)
    assert np.all(np.isfinite(Z[grid["inside"]]))


def test_20_tps_boundary_exact(R):
    assert R["tps"].rim_max <= 1e-6


def test_21_centerline_finite(R):
    assert all(np.isfinite(r["z_back_in"]) for r in R["centerline"])


def test_22_curvature_finite(R):
    grid = R["grid"]
    Z = M._surface_on_grid(R["tps"].zf, grid)
    cf = M.curvature_fields(Z, M.GRID_STEP_IN)
    inner = M.eroded_mask(grid["inside"], iters=2)
    assert inner.any()
    assert np.all(np.isfinite(cf["gauss"][inner]))


def test_23_no_foldover(R):
    # height field is single-valued by construction; verify evaluation is 1:1
    q = np.array([[0.0, 10.0]])
    z = R["tps"].zf(q)
    assert z.shape == (1,) and np.isfinite(z[0])


# --- Sections (24-28) --------------------------------------------------------

def test_24_upper_bout_section(R):
    assert any(s["section_name"] == "upper_bout" for s in R["sections"])


def test_25_waist_section(R):
    assert any(s["section_name"] == "waist" for s in R["sections"])


def test_26_lower_bout_section(R):
    assert any(s["section_name"] == "lower_bout" for s in R["sections"])


def test_27_symmetry_reported(R):
    assert all("symmetric" in s["section_status"] for s in R["sections"])


def test_28_circle_residual_reported(R):
    s = R["sections"][0]
    assert "fitted_local_radius_in" in s and "residual_in" in s


# --- Braces (29-32) ----------------------------------------------------------

def test_29_brace_dims_preserved(R):
    byid = {b["brace_id"]: b for b in R["braces"]}
    assert byid["BB1"]["width_in"] == "0.3200" and byid["BB1"]["depth_in"] == "0.4500"
    assert byid["BB4"]["width_in"] == "0.7600" and byid["BB4"]["depth_in"] == "0.3750"


def test_30_depth_not_dome_rise(R):
    for b in R["braces"]:
        assert b["common_radius_compatible"] == "QUALITATIVE_ONLY"
        assert "NOT dome rise" in b["note"]


def test_31_missing_position_qualitative(R):
    assert all(b["status"] == "QUALITATIVE_ONLY" for b in R["braces"])


def test_32_no_invented_location(R):
    assert all(b["y_in"] == "" for b in R["braces"])


# --- GenOne comparison (33-35) ----------------------------------------------

def test_33_genone_reference_only(R):
    ev = M.load_reference_arch_evidence()
    assert ev["arch_mm_range"] == [4.0, 6.0]
    assert "REFERENCE" in ev["role"].upper()


def test_34_reference_does_not_alter_fit(R):
    # fit functions take only the boundary; GenOne is not an input to them
    import inspect
    for fn in (M.fit_single_sphere, M.fit_compound_surface, M.fit_constrained_surface):
        src = inspect.getsource(fn)
        assert "GENONE" not in src
    assert R["genone_cmp"] in ("below", "within", "above")


def test_35_no_genone_surface_transferred():
    with open(_SCRIPT) as fh:
        text = fh.read()
    assert "GENONE_SIDE_CONTOUR" not in text


# --- Engineering principle (36-38) ------------------------------------------

def test_36_surprising_results_retained(R):
    # inadmissible sphere (per tol) is still present with its recorded radius
    names = [c.name for c in R["candidates"]]
    assert "single_sphere" in names
    assert R["sphere"].radius_ft is not None


def test_37_inadmissible_candidates_retained(R):
    assert any(c.admissible is False for c in R["candidates"])


def test_38_report_distinguishes_math_vs_physical(R):
    sec = M.build_section(R)
    assert "Mathematical result vs physical interpretation" in sec


# --- Determinism (39-42) -----------------------------------------------------

_E4_FILES = [
    "D28_65260_BACK_SURFACE_AUTHORITY_004E.json",
    "D28_65260_BACK_SURFACE_CANDIDATES_004E.csv",
    "D28_65260_BACK_SURFACE_004E.csv",
    "D28_65260_BACK_CENTERLINE_004E.csv",
    "D28_65260_BACK_SECTIONS_004E.csv",
    "D28_65260_BACK_BRACE_COMPATIBILITY_004E.csv",
    "D28_65260_RERUN_004E_SUMMARY.csv",
    "D28_65260_RERUN_004E_PROVENANCE.json",
]


def test_39_write_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1)
    _run_write(d2)
    for f in _E4_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_40_write_does_not_dirty_committed_tree(tmp_path):
    # Anti-drift regression guard: a hermetic --write must leave every tracked
    # docs/experiments/ file byte-unchanged (the git-SHA provenance defect).
    _run_write(tmp_path / "out")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "docs/experiments/"],
        cwd=_REPO, check=True, capture_output=True, text=True).stdout.strip()
    assert dirty == "", f"committed docs/experiments/ dirtied by --write:\n{dirty}"


def test_41_selected_candidate_reproducible():
    a = M.run_all()
    b = M.run_all()
    assert a["primary"].name == b["primary"].name == "constrained_tps"
    assert a["disp"] == b["disp"]


def test_42_report_section_survives_regen(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"

    def section(d):
        with open(os.path.join(d, "REPORT.md")) as fh:
            t = fh.read()
        return t[t.index(M._S):t.index(M._E) + len(M._E)]
    _run_write(d1)
    _run_write(d2)
    a, b = section(d1), section(d2)
    assert a == b and "RERUN004E" in a
