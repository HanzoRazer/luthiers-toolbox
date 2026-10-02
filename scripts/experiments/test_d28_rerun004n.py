#!/usr/bin/env python3
"""Tests for D28 Run 004N — Corrected Back Surface Family.

Categories: 1. source-authority  2. mathematical (REAL boundary residual, no
forced zero; synthetic residual controls)  3. regression/anti-drift (new
artifacts only; constructed-not-measured)  4. provenance/reproducibility.
"""
from __future__ import annotations

import csv
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004n_corrected_back_surface_family.py")
_PARENT = "069c96d7"


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("d28_004n", "d28_rerun004n_corrected_back_surface_family.py")
GA = M.GA


@pytest.fixture(scope="module")
def R():
    return M.run_all()


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _run_write(outdir, doc=None):
    env = dict(os.environ, D28_EXP_OUTDIR=str(outdir))
    if doc is not None:
        env["D28_EXP_DOC"] = str(doc)
    subprocess.run([sys.executable, _SCRIPT, "--write"], cwd=_REPO, check=True,
                   capture_output=True, env=env)


def _rows(d, n):
    with open(os.path.join(d, n)) as fh:
        return list(csv.DictReader(fh))


# --- 1. Source-authority -----------------------------------------------------

def test_01_driven_from_004m_rim(R):
    assert M.E.RIM_CSV == M.M_RIM_CSV
    assert "004M" in os.path.basename(M.M_RIM_CSV)
    assert R["disp"] == "CORRECTED_BOUNDED_BACK_SURFACE_FAMILY_CONSTRUCTED"


def test_02_every_member_constructed(R):
    assert all(m["classification"] == "CONSTRUCTED_ADMISSIBLE_SURFACE" for m in R["members"])


def test_03_five_members(R):
    assert [m["name"] for m in R["members"]] == ["floor", "q25", "mid", "q75", "ceiling"]


def test_04_no_member_promoted(R):
    # family remains bounded/non-unique; dispositions carry no "the back" promotion
    assert len(R["members"]) == 5
    assert R["disp"].endswith("CONSTRUCTED")


# --- 2. Mathematical (REAL boundary residual + synthetic controls) -----------

def test_10_boundary_residual_is_real_not_forced_zero(R):
    # The 004G placeholder forced e==0 for all members. A real evaluation gives a
    # member-dependent residual: the alpha>0 members must differ from the floor.
    resids = [m["resid"]["max_abs"] for m in R["members"]]
    assert len(set(round(r, 15) for r in resids)) > 1, "residuals identical -> looks forced"
    floor = R["members"][0]["resid"]["max_abs"]
    ceiling = R["members"][-1]["resid"]["max_abs"]
    assert ceiling >= floor  # larger alpha -> larger (still tiny) phi-on-rim contribution


def test_11_boundary_residual_within_tolerance(R):
    assert R["boundary_all_pass"] is True
    assert all(m["resid"]["max_abs"] <= M.BOUNDARY_TOL_IN for m in R["members"])
    assert R["max_boundary_abs"] < M.BOUNDARY_TOL_IN


def test_12_boundary_residual_reports_required_fields(R):
    r = R["members"][0]["resid"]
    for k in ("max_abs", "rmse", "n_samples", "tolerance_in", "pass"):
        assert k in r
    assert r["n_samples"] > 50


def test_13_no_forced_zero_in_source():
    src = open(_SCRIPT).read()
    # the 004G forced-zero idiom (multiplying the residual by 0.0) must not reappear
    assert "* 0.0" not in src and "*0.0" not in src


def test_14_residual_helper_synthetic_controls():
    # exact match -> 0; constant offset c -> max_abs == c, rmse == c
    zb = np.linspace(0, 5, 100)
    r0 = GA.boundary_residuals(zb, zb)
    assert r0["max_abs"] == 0.0 and r0["rmse"] == 0.0 and r0["n_samples"] == 100
    rc = GA.boundary_residuals(zb + 0.3, zb)
    assert abs(rc["max_abs"] - 0.3) < 1e-12 and abs(rc["rmse"] - 0.3) < 1e-12


def test_15_tps_boundary_exact(R):
    # floor member (alpha=0) == pure TPS: boundary residual at machine precision
    assert R["members"][0]["resid"]["max_abs"] < 1e-9


def test_16_volume_monotone_in_alpha(R):
    vols = [m["volume_in3"] for m in R["members"]]
    assert all(b >= a for a, b in zip(vols, vols[1:]))


def test_17_geometry_stable_vs_004g(R):
    # corrected rim moved < 0.05 mm, so the volume envelope matches 004G (~18.44-18.60 L)
    vfloor_L = R["members"][0]["volume_in3"] * M.IN3_TO_CM3 / 1000
    assert 18.3 < vfloor_L < 18.7


# --- 3. Regression / anti-drift (new artifacts only) -------------------------

def test_20_family_csv_constructed_not_measured(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_BACK_SURFACE_FAMILY_004N.csv")
    assert rows and all(r["classification"] == "CONSTRUCTED_ADMISSIBLE_SURFACE" for r in rows)
    assert all(r["boundary_pass"] == "True" for r in rows)


def test_21_authority_replaces_forced_zero(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    with open(os.path.join(tmp_path, "D28_65260_BACK_SURFACE_AUTHORITY_004N.json")) as fh:
        auth = json.load(fh)
    assert "forced-zero" in auth["boundary_residual"]["replaces"]
    assert auth["interior_classification"].startswith("CONSTRUCTED_ADMISSIBLE_SURFACE")
    assert auth["no_member_promoted_to_the_back"] and auth["no_historical_radius_claimed"]


def test_22_new_section_no_overstated_claims(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    section = open(doc).read()
    section = section[section.index(M._S):section.index(M._E)]
    low = section.lower()
    assert "back_curvature_field_established" not in low
    assert "measured back surface" not in low
    assert "historical back" in low  # only in the NOT-a-recovered-historical-back framing
    assert "constructed" in low


def test_23_residual_csv_method_documented(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_BACK_BOUNDARY_RESIDUAL_004N.csv")
    assert rows and all("z_member" in r["method"] and "forced-zero" in r["method"] for r in rows)
    for r in rows:
        assert float(r["max_abs_boundary_error_in"]) <= float(r["tolerance_in"])


# --- 4. Provenance / reproducibility -----------------------------------------

def test_30_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _PARENT, "HEAD"],
                          cwd=_REPO).returncode == 0


def test_31_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


def test_32_no_prior_result_modified(tmp_path):
    watched = ["D28_65260_BACK_FAMILY_MEMBERS_004G.csv",
               "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json",
               "D28_65260_REGISTERED_RIM_004M.csv",
               "D28_65260_REGISTERED_RIM_004D.csv"]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert before == {f: _sha(os.path.join(_RESULTS, f)) for f in watched}


def test_33_no_production_modified(tmp_path):
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry", "specs",
                        "martin_d28_1937.json")
    before = _sha(spec)
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert _sha(spec) == before


def test_34_deterministic_regeneration(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    os.makedirs(d1); os.makedirs(d2)
    _run_write(d1, doc=os.path.join(d1, "REPORT.md"))
    _run_write(d2, doc=os.path.join(d2, "REPORT.md"))
    for n in ("D28_65260_BACK_SURFACE_FAMILY_004N.csv", "D28_65260_BACK_BOUNDARY_RESIDUAL_004N.csv",
              "D28_65260_BODY_VOLUME_ENVELOPE_004N.csv", "D28_65260_RERUN_004N_SUMMARY.csv"):
        assert _sha(os.path.join(d1, n)) == _sha(os.path.join(d2, n))


def test_35_hermetic_write_does_not_dirty_tree(tmp_path):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                            capture_output=True, text=True).stdout
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                           capture_output=True, text=True).stdout
    assert before == after
