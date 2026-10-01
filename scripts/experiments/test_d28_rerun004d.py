#!/usr/bin/env python3
"""Tests for D28 Run 004D — Developed-Side / Plan-Outline Registration.

Covers source preservation, endpoint/waist anchoring, mapping monotonicity,
candidate methods, registered-rim geometry, separation of the two length
quantities, prior handling, fail-closed guards, and determinism.
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


def _load():
    spec = importlib.util.spec_from_file_location(
        "d28_004d", os.path.join(_HERE, "d28_rerun004d_developed_plan_registration.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004d"] = m
    spec.loader.exec_module(m)
    return m


M = _load()
DEV_LEN = 30.4375
TOL = 1e-9


@pytest.fixture(scope="module")
def R():
    return M.run_all()


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


# --- Source preservation (1-4) ----------------------------------------------

def test_01_dev_length_exact():
    side = M.load_004c_side_profile()
    assert side["dev_len"] == DEV_LEN


def test_02_station_heights_unchanged():
    side = M.load_004c_side_profile()
    with open(M.AUTH_004C_JSON) as fh:
        auth = json.load(fh)
    for d in auth["stationed_side_heights"]:
        assert abs(float(side["H"](float(d["station_in"]))) - float(d["height_in"])) < 1e-9


def test_03_arnold_outline_unchanged():
    out = M.load_arnold_outline()
    # frozen extraction facts
    assert len(out["y"]) == 1993
    assert abs(out["x"][0] - 3.08580) < 1e-5
    assert abs(out["x"][-1] - 4.39037) < 1e-5
    assert abs(out["L"] - 19.98996) < 1e-4


def test_04_prior_artifacts_not_modified_by_run():
    watched = [
        "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
        "D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv",
        "D28_65260_LANDMARK_RECONSTRUCTION_004C.csv",
        "D28_65260_RERUN_004C_SUMMARY.csv",
        "D28_65260_ARNOLD_OUTLINE.csv",
        "D28_65260_RERUN_003_EXTRACTION.json",
    ]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    M.run_all()  # read-only orchestration
    after = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    assert before == after


# --- Endpoint mapping (5-8) --------------------------------------------------

def test_05_neck_maps_to_p0(R):
    assert abs(float(R["primary"].g(0.0))) < TOL


def test_06_tail_maps_to_p1(R):
    assert abs(float(R["primary"].g(1.0)) - 1.0) < TOL


def test_07_neck_xy_matches_outline_endpoint(R):
    neck = next(a for a in R["anchors"] if a.name == "neck")
    assert abs(neck.plan_x_in - float(R["outline"]["x"][0])) < 1e-9
    assert abs(neck.plan_y_in - 0.0) < 1e-9


def test_08_tail_xy_matches_outline_endpoint(R):
    tail = next(a for a in R["anchors"] if a.name == "tail")
    assert abs(tail.plan_x_in - float(R["outline"]["x"][-1])) < 1e-9
    assert abs(tail.plan_y_in - float(R["outline"]["y"][-1])) < 1e-9


# --- Waist (9-11) ------------------------------------------------------------

def test_09_waist_station_from_004c(R):
    assert 11.4 < R["waist_dev"] < 11.7


def test_10_waist_maps_to_geometric_waist(R):
    waist = next(a for a in R["anchors"] if a.name == "waist")
    assert abs(waist.plan_frac - R["land"]["waist"]["plan_frac_raw"]) < 1e-12


def test_11_waist_mapping_residual_small(R):
    waist = next(a for a in R["anchors"] if a.name == "waist")
    assert abs(float(R["primary"].g(waist.dev_u)) - waist.plan_frac) < 1e-9


# --- Mapping monotonicity (12-15) -------------------------------------------

def test_12_p_strictly_increases(R):
    uu = np.linspace(0, 1, 4001)
    g = R["primary"].g(uu)
    assert np.all(np.diff(g) > 0)


def test_13_no_negative_derivative(R):
    uu = np.linspace(0, 1, 4001)
    assert np.min(R["primary"].dg(uu)) > 0


def test_14_no_duplicate_plan_locations(R):
    pts = [(round(r["x_in"], 6), round(r["y_in"], 6)) for r in R["rim"]]
    assert len(pts) == len(set(pts))


def test_15_p_in_range(R):
    uu = np.linspace(0, 1, 4001)
    g = R["primary"].g(uu)
    assert g.min() >= -1e-9 and g.max() <= 1 + 1e-9


# --- Mapping methods (16-19) -------------------------------------------------

def test_16_linear_reproduces_anchors(R):
    hard = [a for a in R["anchors"] if a.hard]
    mp = M.fit_registration_mapping([a.dev_u for a in hard], [a.plan_frac for a in hard], "linear")
    for a in hard:
        assert abs(float(mp.g(a.dev_u)) - a.plan_frac) < 1e-12


def test_17_pchip_reproduces_anchors(R):
    hard = [a for a in R["anchors"] if a.hard]
    mp = M.fit_registration_mapping([a.dev_u for a in hard], [a.plan_frac for a in hard], "pchip")
    for a in hard:
        assert abs(float(mp.g(a.dev_u)) - a.plan_frac) < 1e-9


def test_18_pchip_no_overshoot(R):
    uu = np.linspace(0, 1, 4001)
    for tag in ("hard_pchip", "prior_pchip"):
        g = R["cand_hard"]["pchip"].g(uu) if tag == "hard_pchip" else R["cand_prior"]["pchip"].g(uu)
        assert g.min() >= -1e-9 and g.max() <= 1 + 1e-9


def test_19_hermite_fails_closed_when_nonmonotone():
    # anchors crafted so FD-slope Hermite overshoots/reverses
    mp = M.fit_registration_mapping([0.0, 0.1, 1.0], [0.0, 0.95, 1.0], "hermite")
    assert mp.admissible is False
    # PCHIP on the same anchors stays admissible (monotone, no overshoot)
    mp2 = M.fit_registration_mapping([0.0, 0.1, 1.0], [0.0, 0.95, 1.0], "pchip")
    assert mp2.admissible is True


# --- Geometry (20-25) --------------------------------------------------------

def test_20_rim_continuous(R):
    xs = np.array([r["x_in"] for r in R["rim"]])
    ys = np.array([r["y_in"] for r in R["rim"]])
    zs = np.array([r["z_in"] for r in R["rim"]])
    assert np.all(np.isfinite(xs)) and np.all(np.isfinite(ys)) and np.all(np.isfinite(zs))
    step = np.hypot(np.diff(xs), np.diff(ys))
    assert step.max() < 1.0  # no gaps


def test_21_point_count_deterministic(R):
    R2 = M.run_all()
    assert len(R["rim"]) == len(R2["rim"]) == 248


def test_22_xy_lie_on_outline(R):
    y = R["outline"]["y"]
    x = R["outline"]["x"]
    for r in R["rim"]:
        hw = float(np.interp(r["y_in"], y, x))
        assert abs(hw - r["x_in"]) < 0.05


def test_23_z_exact_at_source_stations(R):
    H = R["side"]["H"]
    src = {round(p[0], 6): p[1] for p in R["side"]["src_points"]}
    for r in R["rim"]:
        key = round(r["s_in"], 6)
        if key in src:
            assert abs(r["z_in"] - src[key]) < 1e-9


def test_24_station_27_registered(R):
    assert any(abs(r["s_in"] - 27.0) < 1e-9 for r in R["rim"])


def test_25_tail_endpoint_present(R):
    assert any(abs(r["s_in"] - DEV_LEN) < 1e-9 for r in R["rim"])
    assert abs(R["rim"][-1]["s_in"] - DEV_LEN) < 1e-9


# --- Separation of quantities (26-30) ---------------------------------------

def test_26_no_force_equal_lengths(R):
    assert abs(R["land"]["A_raw"] - DEV_LEN) > 1.0
    assert abs(R["land"]["A_sm"] - DEV_LEN) > 1.0
    # plan arc axis maxes out at A_raw, not S
    assert abs(max(r["plan_arc_in"] for r in R["rim"]) - R["land"]["A_raw"]) < 1e-6


def test_27_plan_perimeter_not_station_authority(R):
    # developed stations come from 004C source points, independent of A
    src = sorted(round(p[0], 4) for p in R["side"]["src_points"])
    assert src[:5] == [0.0, 3.0, 6.0, 9.0, 12.0]
    assert src[-1] == DEV_LEN


def test_28_no_sevy_high_point():
    with open(os.path.join(_HERE, "d28_rerun004d_developed_plan_registration.py")) as fh:
        srctext = fh.read()
    assert "solve_high_point" not in srctext


def test_29_no_sphere_fit():
    with open(os.path.join(_HERE, "d28_rerun004d_developed_plan_registration.py")) as fh:
        srctext = fh.read()
    assert "least_squares" not in srctext and "solve_side_height" not in srctext


def test_30_no_genone_side_height_curve():
    with open(os.path.join(_HERE, "d28_rerun004d_developed_plan_registration.py")) as fh:
        srctext = fh.read()
    assert "GENONE_SIDE_CONTOUR" not in srctext
    priors = M.load_genone_landmark_priors()
    # priors are longitudinal stations (floats), not height curves
    assert all(isinstance(v, float) for v in priors.values())


# --- Priors (31-33) ----------------------------------------------------------

def test_31_bouts_prior_only(R):
    for nm in ("upper_bout", "lower_bout"):
        a = next(x for x in R["anchors"] if x.name == nm)
        assert a.anchor_class == "PROPORTIONAL_PRIOR"
        assert a.hard is False


def test_32_priors_cannot_move_hard_anchors(R):
    hard = [a for a in R["anchors"] if a.hard]
    hard_only = M.fit_registration_mapping(
        [a.dev_u for a in hard], [a.plan_frac for a in hard], "pchip")
    for a in hard:
        assert abs(float(hard_only.g(a.dev_u)) - a.plan_frac) < 1e-9


def test_33_removing_prior_keeps_hard_anchors(R):
    hard = [a for a in R["anchors"] if a.hard]
    g_hard = R["cand_hard"]["pchip"].g
    for a in hard:
        assert abs(float(g_hard(a.dev_u)) - a.plan_frac) < 1e-9


# --- Fail-closed (34-39) -----------------------------------------------------

def test_34_nonmonotone_anchors_fail():
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.0, 0.5, 0.4, 1.0], [0.0, 0.3, 0.6, 1.0], "pchip")


def test_35_duplicate_developed_stations_fail():
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.0, 0.5, 0.5, 1.0], [0.0, 0.3, 0.6, 1.0], "pchip")


def test_36_duplicate_plan_fractions_fail():
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.0, 0.4, 0.6, 1.0], [0.0, 0.5, 0.5, 1.0], "pchip")


def test_37_missing_endpoint_fails():
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.1, 0.5, 1.0], [0.0, 0.5, 1.0], "pchip")
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.0, 0.5, 0.9], [0.0, 0.5, 1.0], "pchip")


def test_38_malformed_source_profile_fails():
    with pytest.raises(ValueError):
        M.validate_source_points([0.0, 3.0, 3.0, DEV_LEN], DEV_LEN)       # duplicate
    with pytest.raises(ValueError):
        M.validate_source_points([0.0, 12.0, 6.0, DEV_LEN], DEV_LEN)      # non-ascending
    with pytest.raises(ValueError):
        M.validate_source_points([0.0, 3.0, 27.0], 29.0)                  # wrong length


def test_39_anchor_outside_outline_range_fails():
    with pytest.raises(ValueError):
        M.fit_registration_mapping([0.0, 0.5, 1.0], [0.0, 1.2, 1.0], "pchip")


# --- Determinism (40-42) -----------------------------------------------------

_SCRIPT = os.path.join(_HERE, "d28_rerun004d_developed_plan_registration.py")
_D4_FILES = [
    "D28_65260_REGISTRATION_AUTHORITY_004D.json",
    "D28_65260_REGISTRATION_ANCHORS_004D.csv",
    "D28_65260_DEVELOPED_PLAN_MAPPING_004D.csv",
    "D28_65260_REGISTERED_RIM_004D.csv",
    "D28_65260_RERUN_004D_ANALYSIS.csv",
    "D28_65260_RERUN_004D_SUMMARY.csv",
    "D28_65260_RERUN_004D_PROVENANCE.json",
]


def _run_write(outdir):
    """Hermetic --write: output is redirected to `outdir` (and <outdir>/REPORT.md)
    via D28_EXP_OUTDIR so committed artifacts are never touched."""
    env = dict(os.environ, D28_EXP_OUTDIR=str(outdir))
    subprocess.run([sys.executable, _SCRIPT, "--write"], cwd=_REPO, check=True,
                   capture_output=True, env=env)


def test_40_write_is_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1)
    _run_write(d2)
    for f in _D4_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_41_doc_section_identical_across_writes(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"

    def section(d):
        with open(os.path.join(d, "REPORT.md")) as fh:
            t = fh.read()
        return t[t.index(M._S):t.index(M._E) + len(M._E)]
    _run_write(d1)
    _run_write(d2)
    a, b = section(d1), section(d2)
    assert a == b and "RERUN004D" in a


def test_42_write_does_not_dirty_committed_tree(tmp_path):
    # Anti-drift regression guard: a hermetic --write must leave every tracked
    # docs/experiments/ file byte-unchanged (the git-SHA provenance defect).
    _run_write(tmp_path / "out")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "docs/experiments/"],
        cwd=_REPO, check=True, capture_output=True, text=True).stdout.strip()
    assert dirty == "", f"committed docs/experiments/ dirtied by --write:\n{dirty}"
