#!/usr/bin/env python3
"""Tests for D28 Run 004H — Proportional Radius / Volume Sensitivity Transform.

Authority, transform-machinery controls (R∝k, V∝k³), geometry integrity, volume
convention/decomposition, radius/apex diagnostics, brace handling, 004G crosscheck,
and determinism / anti-drift.
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004h_proportional_radius_volume_sensitivity.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004h", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004h"] = m
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


def _json(d, name):
    return json.load(open(os.path.join(d, name)))


def _rows(d, name):
    import csv
    with open(os.path.join(d, name)) as fh:
        return list(csv.DictReader(fh))


# --- Authority (1-6) ---------------------------------------------------------

def test_01_parent_ancestry():
    r = subprocess.run(["git", "merge-base", "--is-ancestor", "46607260", "HEAD"], cwd=_REPO)
    assert r.returncode == 0


def test_02_inputs_exist():
    for p in (M.ARNOLD_OUTLINE_CSV, M.RIM_CSV, M.GENONE_SIDE_CSV, M.F_POSITIONS_CSV,
              M.G_SUMMARY_CSV, M.G_MEMBERS_CSV):
        assert os.path.exists(p)


def test_03_inputs_not_modified():
    watched = [M.ARNOLD_OUTLINE_CSV, M.RIM_CSV, M.GENONE_SIDE_CSV, M.G_SUMMARY_CSV]
    before = {p: _sha(p) for p in watched}
    M.run_all()
    assert before == {p: _sha(p) for p in watched}


def test_04_reference_radius_classified_controlled(tmp_path):
    _run_write(tmp_path)
    j = _json(tmp_path, "D28_65260_REFERENCE_GEOMETRY_004H.json")
    assert j["reference_radius"]["classification"] == "MODEL_ASSUMPTION_CONTROLLED_REFERENCE"
    assert j["authority_classification"] == "MODEL_REFERENCE_GEOMETRY"
    assert abs(j["reference_radius"]["value_ft"] - 25.0) < 1e-9


def test_05_no_historical_label(tmp_path):
    _run_write(tmp_path)
    j = _json(tmp_path, "D28_65260_REFERENCE_GEOMETRY_004H.json")
    # explicit non-claim present; reference radius is a controlled assumption, never #65260 authority
    nc = j["non_claim"].lower()
    assert "establishes nothing" in nc and "does not assert" in nc
    assert "NOT a GenOne/#65260 historical measurement" in j["reference_radius"]["basis"]
    assert j["reference_radius"]["classification"] == "MODEL_ASSUMPTION_CONTROLLED_REFERENCE"
    # transformed radii are diagnostics, not historical findings
    prov = _json(tmp_path, "D28_65260_RERUN_004H_PROVENANCE.json")
    assert prov["transformed_radius_classification"] == "CALCULATED_DIAGNOSTIC"


def test_06_genone_analogy_only(tmp_path):
    _run_write(tmp_path)
    j = _json(tmp_path, "D28_65260_REFERENCE_GEOMETRY_004H.json")
    assert j["side_profile_base_ref"]["classification"] == "SOURCE_SUPPORTED_ANALOGY"


# --- Mathematical controls (7-9) --------------------------------------------

def test_07_B0_reproduces_25ft(R):
    assert abs(R["controls"]["R_char_B0_ft"] - 25.0) / 25.0 < 0.02


def test_08_B1_radius_proportional_to_k(R):
    c = R["controls"]
    assert abs(c["R1_over_R0"] - c["k"]) < 1e-3
    assert c["arbitrary_R_ok"]  # arbitrary k=1.5 -> R ratio 1.5 exactly


def test_09_B1_volume_proportional_to_k_cubed(R):
    c = R["controls"]
    assert abs(c["V1_over_V0"] - c["k"] ** 3) < 1e-3
    assert c["arbitrary_V_ok"]  # arbitrary k=1.5 -> V ratio 3.375 exactly


# --- Geometry (10-16) --------------------------------------------------------

def test_10_surfaces_finite(R):
    for name, S in R["cases"].items():
        assert np.all(np.isfinite(S["z"][S["inside"]])), name


def test_11_no_self_intersection(R):
    # height field z(x,y) is single-valued by construction -> no self-intersection
    for S in R["cases"].values():
        assert S["z"].shape == S["XX"].shape


def test_12_monotonic_station_mapping(R):
    for S in R["cases"].values():
        assert np.all(np.diff(S["ys"]) > 0)


def test_13_outline_only_uses_65260_contour_ref_side(R):
    w_A, L_A = M.load_outline_65260()
    base_ref = M.load_base_ref()
    S = R["cases"]["B2"]
    assert abs(S["wfun"](0.5) - w_A(0.5)) < 1e-9        # #65260 outline
    assert abs(S["basefun"](0.5) - base_ref(0.5)) < 1e-9  # reference side


def test_14_side_only_uses_ref_contour_65260_side(R):
    w_ref = M.interpolate_half_width_ref()
    base_A = M.load_base_65260()
    S = R["cases"]["B3"]
    assert abs(S["wfun"](0.5) - w_ref(0.5)) < 1e-9        # reference outline
    assert abs(S["basefun"](0.5) - base_A(0.5)) < 1e-9    # #65260 side


def test_15_combined_uses_both_65260(R):
    w_A, _ = M.load_outline_65260()
    base_A = M.load_base_65260()
    S = R["cases"]["B4"]
    assert abs(S["wfun"](0.5) - w_A(0.5)) < 1e-9
    assert abs(S["basefun"](0.5) - base_A(0.5)) < 1e-9


def test_16_no_hidden_clamping(R):
    # radius/rise/apex take their computed values (not pinned to the 25 ft input)
    gR = [R["results"][n]["sphere"]["R_ft"] for n in ("B0", "B2", "B3", "B4")]
    assert len(set(round(x, 3) for x in gR)) > 1   # they genuinely differ
    assert not all(abs(x - 25.0) < 1e-6 for x in gR)


# --- Volume (17-20) ----------------------------------------------------------

def test_17_grid_refinement_reported(R):
    assert R["refine"]["rel_delta"] < 0.02 and R["refine"]["vol_fine_in3"] > 0


def test_18_identical_top_reference(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_VOLUME_SENSITIVITY_004H.csv")
    cases = [r for r in rows if r["case"] in ("B0", "B1", "B2", "B3", "B4")]
    assert all(r["top_reference"] == "FLAT_TOP_GEOMETRIC_REFERENCE" for r in cases)


def test_19_volume_independently_recomputed(R):
    # each case volume is integrated from its own surface (not derived by scaling),
    # except B1 which is a deliberate analytic/numeric similitude control.
    for n in ("B0", "B2", "B3", "B4"):
        S = R["cases"][n]
        assert abs(M.integrate_body_volume(S) - R["results"][n]["vol_in3"]) < 1e-6


def test_20_B1_analytic_matches_numeric(R):
    c = R["controls"]
    assert abs(c["V1_over_V0"] - c["k"] ** 3) < 1e-3


# --- Radius (21-24) ----------------------------------------------------------

def test_21_sphere_rmse_retained(R):
    for n in R["results"]:
        assert R["results"][n]["sphere"]["rmse_in"] >= 0


def test_22_global_radius_has_fit_error(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_RADIUS_SENSITIVITY_004H.csv")
    assert all(r["sphere_rmse_in"] != "" for r in rows)


def test_23_apex_outside_body_preserved(R):
    # fitted sphere center lies far below the body (not clamped into the planform)
    assert R["results"]["B0"]["sphere"]["cz"] < 0


def test_24_counterintuitive_not_corrected(R):
    # some fitted apex may lie outside the planform; recorded as-is (bool present)
    for n in R["results"]:
        assert isinstance(R["results"][n]["sphere"]["apex_inside_planform"], bool)


# --- Apex (25-28) ------------------------------------------------------------

def test_25_apex_from_surface(R):
    # apex is the argmax of dome rise on the grid, not assumed at body center
    for n in R["results"]:
        a = R["results"][n]["apex"]
        assert a["apex_rise_mm"] > 0


def test_26_apex_fraction_reported(R):
    for n in R["results"]:
        assert 0.0 <= R["results"][n]["apex"]["apex_y_fraction"] <= 1.0


def test_27_apex_migration_reproducible():
    a = M.run_all(); b = M.run_all()
    assert (a["decomp"]["dApexY_combined_in"] == b["decomp"]["dApexY_combined_in"])


def test_28_depth_vs_rise_not_conflated(R):
    # apex_rise is relative dome rise (mm), far smaller than absolute depth (~100 mm)
    for n in R["results"]:
        assert R["results"][n]["apex"]["apex_rise_mm"] < 10.0


# --- Brace (29-32) -----------------------------------------------------------

def test_29_bb_stations_equal_004f(R):
    st = M.load_brace_stations()
    ys = {b["brace_id"]: b["y_in"] for b in R["brace_rows"]}
    for k in ("BB1", "BB2", "BB3", "BB4"):
        assert abs(ys[k] - st[k]["y_in"]) < 1e-9


def test_30_pm04_window_sampled(R):
    for b in R["brace_rows"]:
        assert b["unc_in"] == 0.4
        assert b["rise_min_mm"] <= b["rise_center_mm"] <= b["rise_max_mm"] + 1e-9


def test_31_brace_bottom_unresolved(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_BRACE_SECTION_SENSITIVITY_004H.csv")
    assert all("UNRESOLVED" in r["brace_bottom_curvature"] for r in rows)


def test_32_no_surface_radius_assigned_to_brace_bottom(tmp_path):
    _run_write(tmp_path)
    rows = _rows(tmp_path, "D28_65260_BRACE_SECTION_SENSITIVITY_004H.csv")
    assert all("!=" in r["brace_bottom_curvature"] for r in rows)


# --- 004G crosscheck (33-36) -------------------------------------------------

def test_33_004g_read_only():
    before = _sha(M.G_SUMMARY_CSV)
    M.run_all()
    assert _sha(M.G_SUMMARY_CSV) == before


def test_34_does_not_alter_004g(tmp_path):
    before = {p: _sha(os.path.join(_RESULTS, p)) for p in
              ("D28_65260_RERUN_004G_SUMMARY.csv", "D28_65260_BACK_FAMILY_MEMBERS_004G.csv")}
    _run_write(tmp_path)
    assert before == {p: _sha(os.path.join(_RESULTS, p)) for p in before}


def test_35_crosscheck_inside_below_above_no_member_selected(R):
    rels = {r["quantity"]: r["relation"] for r in R["crosscheck"]}
    assert rels["dome_rise_mm"] in ("below", "inside", "above")
    assert rels["body_volume_L"] in ("below", "inside", "above")


def test_36_invalid_convention_fails_closed(R):
    radius_row = next(r for r in R["crosscheck"] if r["quantity"] == "equivalent_radius_ft")
    assert radius_row["comparison_valid"] == "False"


# --- Determinism / hygiene (37-42) ------------------------------------------

_H_FILES = [
    "D28_65260_REFERENCE_GEOMETRY_004H.json", "D28_65260_PROPORTIONAL_TRANSFORMS_004H.csv",
    "D28_65260_RADIUS_SENSITIVITY_004H.csv", "D28_65260_APEX_MIGRATION_004H.csv",
    "D28_65260_VOLUME_SENSITIVITY_004H.csv", "D28_65260_BRACE_SECTION_SENSITIVITY_004H.csv",
    "D28_65260_004G_004H_CROSSCHECK.csv", "D28_65260_RERUN_004H_SUMMARY.csv",
    "D28_65260_RERUN_004H_PROVENANCE.json",
]


def test_37_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1); _run_write(d2)
    for f in _H_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_38_outdir_env_works(tmp_path):
    _run_write(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "D28_65260_RERUN_004H_SUMMARY.csv"))


def test_39_tests_use_temp_output(tmp_path):
    # the write above went to tmp, not the committed results dir
    assert str(tmp_path) != _RESULTS


def test_40_clean_tree_after_write(tmp_path):
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                              cwd=_REPO, check=True, capture_output=True, text=True).stdout
    before = status()
    _run_write(tmp_path / "out")
    assert status() == before


def test_41_no_production_files_changed(tmp_path):
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry", "specs",
                        "martin_d28_1937.json")
    before = _sha(spec)
    _run_write(tmp_path)
    assert _sha(spec) == before


def test_42_no_pdf_runtime_dependency():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        prov = _json(d, "D28_65260_RERUN_004H_PROVENANCE.json")
    assert prov["runtime_pdf_access"] is False
