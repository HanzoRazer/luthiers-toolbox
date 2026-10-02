#!/usr/bin/env python3
"""Tests for D28 Run 004L — Developed Rim Reconstruction.

Categories: 1. source-authority  2. mathematical (synthetic arc-length controls)
3. regression/anti-drift (new artifacts only)  4. provenance/reproducibility.
"""
from __future__ import annotations

import csv
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004l_developed_rim_reconstruction.py")
_PARENT = "069c96d7"


def _load():
    spec = importlib.util.spec_from_file_location("d28_004l", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004l"] = m
    spec.loader.exec_module(m)
    return m


M = _load()
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

def test_01_developed_rim_from_arclength_not_30_4375(R):
    assert abs(R["developed_rim_raw"] - 24.4847) < 1e-3
    assert R["developed_rim_raw"] != 30.4375
    assert R["developed_ne_internal"] is True


def test_02_developed_rim_distinct_from_cad_outside(R):
    assert R["developed_ne_outside"] is True
    assert R["developed_rim_raw"] != M.CAD_OUTSIDE_BODY_LENGTH_IN


def test_03_smoothed_is_diagnostic_only(R):
    # the legacy ~26.73 in value is reproduced only to be flagged, not used
    assert abs(R["developed_rim_sm"] - 26.7283) < 1e-3
    assert R["developed_rim_sm"] > R["developed_rim_raw"]
    assert R["smoothing_inflation"] > 0


def test_04_body_length_gate_passes(R):
    assert R["reconciled"] is True
    assert R["body_pct_err"] <= M.BODY_LENGTH_TOL_PCT
    assert R["disp"] == "DEVELOPED_RIM_RECONSTRUCTED"


def test_05_three_lengths_distinct(R):
    vals = {round(R["developed_rim_raw"], 4), round(M.CAD_OUTSIDE_BODY_LENGTH_IN, 4),
            round(M.INTERNAL_BLOCK_TO_BLOCK_IN, 4)}
    assert len(vals) == 3


def test_06_waist_landmark_uses_outline_not_radius(R):
    # waist detected as a half-width minimum between the bouts, not from 4.4375
    w = R["landmarks"]["waist"]
    ub = R["landmarks"]["upper_bout"]
    lb = R["landmarks"]["lower_bout"]
    assert w["half_width_in"] < ub["half_width_in"]
    assert w["half_width_in"] < lb["half_width_in"]
    assert w["half_width_in"] != 4.4375


# --- 2. Mathematical (synthetic arc-length controls) -------------------------

def test_10_arclength_straight_line():
    # vertical segment of length 3 (x constant): arc length == 3
    y = np.linspace(0, 3, 50)
    x = np.full_like(y, 2.0)
    s = GA.compute_polyline_arclength(y, x)
    assert abs(s[-1] - 3.0) < 1e-9


def test_11_arclength_45deg_line():
    # line y=x from 0..1 -> length sqrt(2)
    y = np.linspace(0, 1, 100)
    x = y.copy()
    s = GA.compute_polyline_arclength(y, x)
    assert abs(s[-1] - math.sqrt(2)) < 1e-6


def test_12_arclength_quarter_circle():
    # quarter circle radius R: arc length -> pi*R/2
    R0 = 5.0
    t = np.linspace(0, math.pi / 2, 20001)
    y = R0 * np.sin(t)
    x = R0 * np.cos(t)
    s = GA.compute_polyline_arclength(y, x)
    assert abs(s[-1] - (math.pi * R0 / 2)) < 1e-3


def test_13_arclength_half_circle():
    R0 = 3.0
    t = np.linspace(0, math.pi, 40001)
    y = R0 * np.sin(t)        # 0..R..0 (monotone-free in y is fine for arclength)
    x = R0 * np.cos(t)
    s = GA.compute_polyline_arclength(y, x)
    assert abs(s[-1] - (math.pi * R0)) < 1e-3


def test_14_arclength_monotone_nondecreasing(R):
    s = R["s_raw"]
    assert np.all(np.diff(s) >= -1e-12)
    assert s[0] == 0.0


def test_15_sample_curve_clips_endpoints():
    s = np.array([0.0, 1.0, 2.0, 3.0])
    v = np.array([0.0, 10.0, 20.0, 30.0])
    out = GA.sample_curve_by_arclength(s, v, [-5.0, 1.5, 99.0])
    assert out[0] == 0.0 and out[-1] == 30.0 and abs(out[1] - 15.0) < 1e-9


# --- 3. Regression / anti-drift (new artifacts only) -------------------------

def test_20_rim_csv_labels_internal_as_reference_only(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_DEVELOPED_RIM_004L.csv")
    internal = next(r for r in rows if r["quantity"] == "internal_block_to_block")
    assert "REFERENCE" in internal["classification"].upper() or "REFERENCE" in internal["note"].upper()
    assert "NOT the developed rim" in internal["note"]
    dev = next(r for r in rows if r["quantity"] == "developed_rim_length_raw")
    assert abs(float(dev["value_in"]) - 24.4847) < 1e-3


def test_21_new_section_no_30_4375_as_developed(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    text = open(doc).read()
    section = text[text.index(M._S):text.index(M._E)]
    for ln in section.splitlines():
        low = ln.lower()
        if "30.4375" in ln and "developed" in low:
            # allowed only when framed as NOT / distinct-from the developed rim
            framed = any(tok in low for tok in ("not", "≠", "distinct", "no equality"))
            assert framed, ln


def test_22_summary_reports_independent_derivation(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    row = _rows(tmp_path, "D28_65260_RERUN_004L_SUMMARY.csv")[0]
    assert row["disposition"] == "DEVELOPED_RIM_RECONSTRUCTED"
    assert row["developed_rim_ne_internal"] == "True"
    assert row["body_length_reconciled"] == "True"


# --- 4. Provenance / reproducibility -----------------------------------------

def test_30_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _PARENT, "HEAD"],
                          cwd=_REPO).returncode == 0


def test_31_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


def test_32_outline_input_not_modified(tmp_path):
    before = _sha(M.OUTLINE_CSV)
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert _sha(M.OUTLINE_CSV) == before


def test_33_no_production_modified(tmp_path):
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry", "specs",
                        "martin_d28_1937.json")
    before = _sha(spec)
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert _sha(spec) == before


def test_34_no_prior_result_modified(tmp_path):
    watched = ["D28_65260_REGISTERED_RIM_004D.csv", "D28_65260_SOURCE_DATUM_AUTHORITY_004K.json"]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert before == {f: _sha(os.path.join(_RESULTS, f)) for f in watched}


def test_35_deterministic_regeneration(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    os.makedirs(d1); os.makedirs(d2)
    _run_write(d1, doc=os.path.join(d1, "REPORT.md"))
    _run_write(d2, doc=os.path.join(d2, "REPORT.md"))
    for n in ("D28_65260_DEVELOPED_RIM_004L.csv", "D28_65260_RIM_ARCLENGTH_004L.csv",
              "D28_65260_RIM_LANDMARKS_004L.csv", "D28_65260_RERUN_004L_SUMMARY.csv"):
        assert _sha(os.path.join(d1, n)) == _sha(os.path.join(d2, n))


def test_36_hermetic_write_does_not_dirty_tree(tmp_path):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                            capture_output=True, text=True).stdout
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                           capture_output=True, text=True).stdout
    assert before == after
