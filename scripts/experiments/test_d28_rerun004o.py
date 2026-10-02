#!/usr/bin/env python3
"""Tests for D28 Run 004O — Corrected Curvature and Sensitivity Characterization.

Categories: 1. source-authority  2. mathematical (RL split, apex migration,
curvature controls)  3. regression/anti-drift (no 004J overstatements in new
artifacts)  4. provenance/reproducibility.
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004o_curvature_volume_sensitivity.py")
_PARENT = "069c96d7"


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("d28_004o", "d28_rerun004o_curvature_volume_sensitivity.py")
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


# --- 1. Source-authority / vocabulary ----------------------------------------

def test_01_disposition_vocabulary(R):
    assert R["disp"] == "CORRECTED_CONSTRUCTED_FAMILY_CURVATURE_CHARACTERIZED"
    assert R["disp"] != "BACK_CURVATURE_FIELD_ESTABLISHED"


def test_02_driven_from_corrected_family(R):
    assert len(R["members"]) == 5
    assert R["controls"]["all_pass"] is True


# --- 2. Mathematical ---------------------------------------------------------

def test_10_rl_sign_change_two_distinct_metrics(R):
    # the two metrics are reported separately and are genuinely different concepts
    assert "rl_any_station" in R and "rl_anywhere_in_field" in R
    assert isinstance(R["rl_any_station"], bool)
    assert isinstance(R["rl_anywhere_in_field"], bool)
    # on this corrected geometry the field-wise longitudinal curvature DOES change
    # sign along y, while no named station flips sign across the family
    assert R["rl_anywhere_in_field"] is True
    assert R["rl_any_station"] is False


def test_11_apex_migration_is_material_not_small(R):
    assert R["full_mig_pct"] > M.APEX_MIGRATION_MATERIAL_PCT
    assert R["full_mig_material"] is True
    # ~8.5 in over a ~20 in body is ~42% -> never "small"
    assert R["full_mig"] > 5.0


def test_12_bulged_only_migration_small_floor_distinct(R):
    assert R["bulged_mig"] < R["full_mig"]
    assert R["floor_distinct"] is True  # floor high point sits away from the bulged cluster


def test_13_apex_migration_pct_of_body(R):
    assert abs(R["full_mig_pct"] - 100.0 * R["full_mig"] / R["L"]) < 1e-6


def test_14_curvature_controls_pass(R):
    c = R["controls"]
    assert c["all_pass"] and c["flat_ok"] and c["sphere_ok"] and c["cyl_ok"] and c["saddle_ok"]


def test_15_centerline_sign_change_defined_per_member(R):
    for m in R["members"]:
        cl = m["centerline_signchange"]
        assert cl["sign_changes"] >= 0 and isinstance(cl["has_sign_change"], bool)


def test_16_equivalent_radius_is_diagnostic(R):
    assert np.isfinite(R["sphere_ft"])
    assert 5.0 < R["sphere_ft"] < 60.0  # plausible diagnostic radius range


# --- 3. Regression / anti-drift (new artifacts only) -------------------------

def test_20_saddle_family_only_framing(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_SADDLE_MAP_004O.csv")
    fam = next(r for r in rows if r["member"] == "FAMILY")
    assert "constructed family" in fam["interpretation"].lower()
    assert "historical" in fam["NOT_a_claim_about"].lower()


def test_21_no_overstatements_in_new_section(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    section = open(doc).read()
    section = section[section.index(M._S):section.index(M._E)]
    low = section.lower()
    assert "back_curvature_field_established" not in low
    # the apex migration must never be called "small"
    assert "migration is small" not in low
    assert "small (" not in low
    # historical saddle claim must be explicitly negated
    assert "not" in low and "historical #65260 back" in section


def test_22_apex_csv_reports_both_migrations(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_APEX_MIGRATION_004O.csv")
    f2c = next(r for r in rows if r["member"] == "FLOOR_TO_CEILING_MIGRATION")
    bulged = next(r for r in rows if r["member"] == "BULGED_MEMBERS_ONLY_MIGRATION")
    assert "MATERIAL" in f2c["classification"] or "modest" in f2c["classification"]
    assert float(f2c["apex_y_in"]) > float(bulged["apex_y_in"])


def test_23_prepost_comparison_columns_and_rows(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_PRE_POST_DATUM_RECONCILIATION.csv")
    for col in ("quantity", "old_run", "old_value", "new_run", "new_value", "delta",
                "delta_percent", "reason_changed"):
        assert col in rows[0]
    dev = next(r for r in rows if r["quantity"] == "developed_rim_length_in")
    assert abs(float(dev["old_value"]) - 30.4375) < 1e-3
    assert abs(float(dev["new_value"]) - 24.4847) < 1e-3


def test_24_authority_rl_not_conflated(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    with open(os.path.join(tmp_path, "D28_65260_CURVATURE_AUTHORITY_004O.json")) as fh:
        auth = json.load(fh)
    rl = auth["rl_sign_change"]
    assert "any_named_station_across_family" in rl and "anywhere_along_centerline_within_member" in rl
    assert auth["apex_migration"]["material_not_small"] is True
    assert auth["disposition_vocabulary"].startswith("CORRECTED_CONSTRUCTED_FAMILY")


# --- 4. Provenance / reproducibility -----------------------------------------

def test_30_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _PARENT, "HEAD"],
                          cwd=_REPO).returncode == 0


def test_31_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


def test_32_no_prior_result_modified(tmp_path):
    watched = ["D28_65260_CURVATURE_FIELD_004J.csv", "D28_65260_SADDLE_MAP_004J.csv",
               "D28_65260_BACK_SURFACE_FAMILY_004N.csv", "D28_65260_REGISTERED_RIM_004M.csv"]
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
    for n in ("D28_65260_CURVATURE_FIELD_004O.csv", "D28_65260_APEX_MIGRATION_004O.csv",
              "D28_65260_SADDLE_MAP_004O.csv", "D28_65260_PRE_POST_DATUM_RECONCILIATION.csv",
              "D28_65260_RERUN_004O_SUMMARY.csv"):
        assert _sha(os.path.join(d1, n)) == _sha(os.path.join(d2, n))


def test_35_hermetic_write_does_not_dirty_tree(tmp_path):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                            capture_output=True, text=True).stdout
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                           capture_output=True, text=True).stdout
    assert before == after
