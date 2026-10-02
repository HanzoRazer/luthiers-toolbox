#!/usr/bin/env python3
"""Tests for D28 Run 004F — Back-Arch Authority Recovery.

Covers the authority classifications, recovered brace positions/dimensions with
uncertainty, explicit absence of a direct interior-arch datum, the preserved
(bounded) 004E family, the no-new-surface / no-prior-alteration constraints, the
report wording constraint, and determinism (hermetic --write, no tree drift).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import pytest

_HERE = os.path.dirname(__file__)
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO, "docs", "experiments", "results")
_SCRIPT = os.path.join(_HERE, "d28_rerun004f_back_arch_authority_recovery.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004f", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004f"] = m
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
    env = dict(os.environ, D28_EXP_OUTDIR=str(outdir))
    subprocess.run([sys.executable, _SCRIPT, "--write"], cwd=_REPO, check=True,
                   capture_output=True, env=env)


# --- Disposition & governing answer -----------------------------------------

def test_01_disposition_partial(R):
    assert R["disp"] == "BACK_ARCH_AUTHORITY_PARTIAL"


def test_02_vocabulary_only():
    assert set(["BACK_ARCH_AUTHORITY_RECOVERED", "BACK_ARCH_AUTHORITY_PARTIAL",
                "BACK_ARCH_AUTHORITY_ABSENT"]) >= {M.run_all()["disp"]}


# --- Recovered brace positions (DRAWING_DERIVED, with uncertainty) ----------

def test_03_four_brace_positions(R):
    assert [p["brace_id"] for p in R["positions"]] == ["BB1", "BB2", "BB3", "BB4"]


def test_04_positions_monotonic_neck_to_tail(R):
    ys = [p["y_from_neck_in"] for p in R["positions"]]
    assert ys == sorted(ys)  # BB1 nearest neck .. BB4 nearest tail


def test_05_positions_have_uncertainty(R):
    for p in R["positions"]:
        assert p["uncertainty_in"] == M.POSITION_UNCERTAINTY_IN > 0


def test_06_position_classified_drawing_derived(R):
    assert all(p["position_class"] == "DRAWING_DERIVED" for p in R["positions"])


def test_07_calibration_scale_from_soundhole(R):
    # Ø4.0 in soundhole -> 2 in radius; px_per_in = radius_px / 2
    assert abs(M.PX_PER_IN - M.SOUNDHOLE_RADIUS_PX / 2.0) < 1e-9
    # soundhole center maps to the datum-A longitudinal position
    assert abs(M.y_from_neck_in(M.SOUNDHOLE_CENTER_PX) - M.SOUNDHOLE_Y_FROM_NECK_IN) < 1e-9


def test_08_positions_plausible_vs_body(R):
    for p in R["positions"]:
        assert 0.0 < p["y_from_neck_in"] < M.BODY_LENGTH_IN


# --- Cross-section dims (SOURCE_MEASURED, Arnold drawing) --------------------

def test_09_cross_section_dims_source_measured(R):
    assert all(p["dims_class"] == "SOURCE_MEASURED" for p in R["positions"])


def test_10_arnold_dims_values(R):
    d = M.BRACE_DIMS
    assert d["BB1"] == {"width_in": 0.320, "depth_in": 0.615}
    assert d["BB2"] == {"width_in": 0.320, "depth_in": 0.615}
    assert d["BB3"] == {"width_in": 0.755, "depth_in": 0.385}
    assert d["BB4"] == {"width_in": 0.760, "depth_in": 0.375}


# --- Scallop/peak annotations (source values, NOT arch rise) ----------------

def test_11_scallop_preserved_not_arch(R):
    assert M.OBSERVED_PROFILE_ANNOTATIONS_IN  # preserved
    sec = M.build_section(R)
    assert "not" in sec.lower() and "arch rise" in sec.lower()


# --- Absence of direct interior-arch datum ----------------------------------

def test_12_absent_datums_recorded(R):
    txt = " ".join(M.ABSENT_INTERIOR_DATUMS).lower()
    assert "radius" in txt and "dome-rise" in txt and "brace-bottom curvature" in txt and "centerline" in txt


def test_13_no_direct_arch_datum_in_summary():
    # authority JSON records the absence explicitly
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_ARCH_AUTHORITY_004F.json")))
    assert len(auth["absent_interior_arch_datums"]) == 4


# --- Legacy-spec corrections (recorded, not applied) ------------------------

def test_14_spec_discrepancies_recorded(R):
    keys = {(d["brace_id"], d["field"]) for d in R["discreps"]}
    assert ("BB1", "depth_in") in keys and ("BB2", "depth_in") in keys and ("BB3", "width_in") in keys


def test_15_production_spec_not_edited():
    # the production spec file is unchanged by this run
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry",
                        "specs", "martin_d28_1937.json")
    before = _sha(spec)
    M.run_all()
    assert _sha(spec) == before


def test_16_discrepancy_action_is_record_only(R):
    for d in R["discreps"]:
        assert "NOT edited" in d["action"] and "004E NOT altered" in d["action"]


# --- 004E family preserved, no new surface ----------------------------------

def test_17_family_envelope_sourced_from_004e(R):
    env = R["env"]
    lo, hi = env["family_center_rise_mm_range"]
    assert lo < hi and 0 < hi < 10  # bounded, physical scale (mm)
    assert env["parent_disposition"] == "BACK_SURFACE_MODEL_NONUNIQUE"


def test_18_no_new_surface_generated():
    # 004F emits no surface grid artifact
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        files = set(os.listdir(d))
    assert not any("BACK_SURFACE_004" in f for f in files)
    assert "D28_65260_BACK_ARCH_AUTHORITY_004F.json" in files


def test_19_jd_trace_top_only(R):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_ARCH_AUTHORITY_004F.json")))
    assert "NO back-arch authority" in auth["sources"]["jd_acoustic_body_reconstruction"]["role"]


# --- Report wording constraint ----------------------------------------------

def test_20_report_wording_no_solve_or_determine(R):
    sec = M.build_section(R)
    assert 'do **not** "solve" or "determine"' in sec or "do **not** \"solve\"" in sec
    assert "increase interior structural authority but do not directly constrain" in sec.lower()


def test_21_report_distinguishes_math_vs_physical(R):
    assert "Mathematical result vs physical interpretation" in M.build_section(R)


# --- Provenance / no vendoring ----------------------------------------------

def test_22_provenance_no_pdf_vendored():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        prov = json.load(open(os.path.join(d, "D28_65260_RERUN_004F_PROVENANCE.json")))
    assert prov["pdf_vendored"] is False and prov["runtime_pdf_access"] is False
    assert prov["no_new_surface_generated"] is True


def test_23_arnold_sha_recorded(R):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_ARCH_AUTHORITY_004F.json")))
    assert len(auth["sources"]["arnold_drawing"]["sha256"]) == 64


# --- Determinism / anti-drift -----------------------------------------------

_F_FILES = [
    "D28_65260_BACK_ARCH_AUTHORITY_004F.json",
    "D28_65260_BACK_BRACE_POSITIONS_004F.csv",
    "D28_65260_RERUN_004F_SUMMARY.csv",
    "D28_65260_RERUN_004F_PROVENANCE.json",
]


def test_24_write_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1)
    _run_write(d2)
    for f in _F_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_25_write_does_not_dirty_committed_tree(tmp_path):
    # A hermetic --write must not CHANGE the tracked docs/experiments/ state
    # (order-independent: holds whether or not 004F is committed yet).
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                              cwd=_REPO, check=True, capture_output=True, text=True).stdout
    before = status()
    _run_write(tmp_path / "out")
    after = status()
    assert before == after, f"hermetic --write changed tracked tree:\n{before!r}\n-> {after!r}"


def test_26_report_section_survives_regen(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"

    def section(d):
        with open(os.path.join(d, "REPORT.md")) as fh:
            t = fh.read()
        return t[t.index(M._S):t.index(M._E) + len(M._E)]
    _run_write(d1)
    _run_write(d2)
    a, b = section(d1), section(d2)
    assert a == b and "RERUN004F" in a
