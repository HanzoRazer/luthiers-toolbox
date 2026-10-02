#!/usr/bin/env python3
"""Tests for D28 Run 004M — Side-Height Station Registration.

Categories: 1. source-authority  2. mathematical (registration/identity controls)
3. regression/anti-drift (new artifacts only)  4. provenance/reproducibility,
plus a cross-run consumability check (the 004M rim loads via the 004E loader).
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import os
import json
import subprocess
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(__file__)
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO, "docs", "experiments", "results")
_SCRIPT = os.path.join(_HERE, "d28_rerun004m_side_profile_registration.py")
_PARENT = "069c96d7"


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("d28_004m", "d28_rerun004m_side_profile_registration.py")
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

def test_01_developed_rim_from_004L(R):
    assert abs(R["developed_rim"] - 24.4847) < 1e-3
    assert R["disp"] == "SIDE_HEIGHT_REGISTRATION_SUPPORTED"


def test_02_station_axis_is_internal_block_to_block(R):
    assert abs(R["s_axis_len"] - 30.4375) < 1e-9
    assert R["developed_arc_overflow"] is True  # 30.4375 > 24.485 rejects developed-arc


def test_03_waist_from_outline_not_radius(R):
    assert R["waist_from_outline"] is True
    # the waist arc equals the 004L outline half-width minimum, not anything from 4.4375
    assert abs(R["waist_arc"] - R["landmarks"]["waist"]["plan_arc_raw_in"]) < 1e-9
    assert R["waist_arc"] != M.WAIST_RADIUS_IN


def test_04_landmark_heights_exact(R):
    assert R["neck_exact"] and R["waist_exact"] and R["tail_exact"]


def test_05_side_heights_unchanged_from_004c(R):
    # the profile samples are the committed 004C measurements (read, not re-measured)
    with open(M.AUTH_004C_JSON) as fh:
        auth = json.load(fh)
    src = {float(d["station_in"]): float(d["height_in"]) for d in auth["stationed_side_heights"]}
    for st, h in zip(R["side"]["stations"], R["side"]["heights"]):
        if float(st) in src:
            assert abs(src[float(st)] - float(h)) < 1e-9


# --- 2. Mathematical (registration / identity controls) ----------------------

def test_10_registration_monotone(R):
    assert np.all(np.diff(R["anchor_station"]) > 0)
    assert np.all(np.diff(R["anchor_arc"]) > 0)
    assert R["station_mono"] and R["ymono"]


def test_11_identity_developed_arc_mapping(R):
    # XY at developed arc s* equals the outline sampled at plan-perimeter arc s*
    s_raw, outline = R["s_raw"], R["outline"]
    for r in R["rim"][::40]:
        a = r["s_star_in"]
        assert abs(r["x_in"] - float(np.interp(a, s_raw, outline["x"]))) < 1e-9
        assert abs(r["y_in"] - float(np.interp(a, s_raw, outline["y"]))) < 1e-9


def test_12_waist_station_solves_height(R):
    assert abs(float(R["side"]["H"](R["s_waist"])) - M.WAIST_H) < 1e-6
    assert 9.0 < R["s_waist"] < 12.0


def test_13_pchip_through_side_points(R):
    H = R["side"]["H"]
    for st, h in zip(R["side"]["stations"], R["side"]["heights"]):
        assert abs(float(H(st)) - h) < 1e-9


def test_14_ratio_is_internal_axis_over_developed_arc(R):
    assert abs(R["axis_to_arc_ratio"] - (R["s_axis_len"] / R["developed_rim"])) < 1e-9
    assert R["axis_to_arc_ratio"] > 1.0  # internal axis longer than the developed rim


def test_15_rim_continuous_finite(R):
    assert R["continuous"]
    assert all(np.isfinite([r["x_in"], r["y_in"], r["z_in"], r["station_in"]]).all()
               for r in R["rim"])


# --- cross-run consumability -------------------------------------------------

def test_18_rim_loads_via_004e_loader(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    E = _load("d28_004e_for_m", "d28_rerun004e_back_surface_reconstruction.py")
    E.RIM_CSV = os.path.join(tmp_path, "D28_65260_REGISTERED_RIM_004M.csv")
    rim = E.load_registered_rim()
    assert rim["y"][0] == 0.0 and rim["z"][0] > 0
    assert len(rim["x"]) >= 10
    assert abs(rim["L"] - 19.990) < 1e-2


def test_19_rim_close_to_004d(R):
    # the datum correction is semantic/methodological: geometry is stable (< 0.5 mm)
    dy, dz = [], []
    with open(os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv")) as fh:
        for r in csv.DictReader(fh):
            dy.append(float(r["y_in"])); dz.append(float(r["z_in"]))
    dy, dz = np.array(dy), np.array(dz)
    ym = np.array([r["y_in"] for r in R["rim"]])
    zm = np.array([r["z_in"] for r in R["rim"]])
    z004d = np.interp(ym, dy, dz)
    assert float(np.max(np.abs(z004d - zm))) * 25.4 < 0.5  # mm


# --- 3. Regression / anti-drift (new artifacts only) -------------------------

def test_20_rim_csv_coordinate_system_corrected(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_REGISTERED_RIM_004M.csv")
    assert rows and all("corrected_developed_arc" in r["coordinate_system"] for r in rows)


def test_21_authority_rejects_developed_arc_and_preserves_unresolved(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    with open(os.path.join(tmp_path, "D28_65260_SIDE_STATION_AUTHORITY_004M.json")) as fh:
        auth = json.load(fh)
    assert auth["station_axis"]["developed_arc_assumption"].startswith("REJECTED")
    assert "UNRESOLVED" in auth["station_axis"]["exact_endpoint_convention"]
    assert auth["stretch_ratio_narrative"].startswith("WITHDRAWN")
    assert auth["waist_placement"].startswith("OUTLINE")


def test_22_new_section_no_30_4375_as_developed(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    section = open(doc).read()
    section = section[section.index(M._S):section.index(M._E)]
    for ln in section.splitlines():
        low = ln.lower()
        if "30.4375" in ln and "developed" in low:
            assert any(t in low for t in ("not", "≠", "reject", "exceed", "internal")), ln


def test_23_summary_waist_from_outline(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    row = _rows(tmp_path, "D28_65260_RERUN_004M_SUMMARY.csv")[0]
    assert row["waist_placed_from_outline_not_radius"] == "True"
    assert row["exact_station_convention"].startswith("UNRESOLVED")


# --- 4. Provenance / reproducibility -----------------------------------------

def test_30_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _PARENT, "HEAD"],
                          cwd=_REPO).returncode == 0


def test_31_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


def test_32_no_prior_result_modified(tmp_path):
    watched = ["D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
               "D28_65260_REGISTERED_RIM_004D.csv",
               "D28_65260_DEVELOPED_RIM_004L.csv"]
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
    for n in ("D28_65260_SIDE_STATION_AUTHORITY_004M.json", "D28_65260_SIDE_PROFILE_004M.csv",
              "D28_65260_SIDE_PLAN_REGISTRATION_004M.csv", "D28_65260_REGISTERED_RIM_004M.csv",
              "D28_65260_RERUN_004M_SUMMARY.csv"):
        assert _sha(os.path.join(d1, n)) == _sha(os.path.join(d2, n))


def test_35_hermetic_write_does_not_dirty_tree(tmp_path):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                            capture_output=True, text=True).stdout
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                           capture_output=True, text=True).stdout
    assert before == after
