#!/usr/bin/env python3
"""Tests for D28 Run 004K — Source Datum Reconciliation.

Four categories (per the 004K–004O handoff test plan):
  1. Source-authority    2. Mathematical/invariant
  3. Regression/anti-drift (NEW governing sections/artifacts only)
  4. Provenance/reproducibility
"""
from __future__ import annotations

import csv
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
_SCRIPT = os.path.join(_HERE, "d28_rerun004k_source_datum_reconciliation.py")
_PARENT = "069c96d7"  # PR #421 head before the corrective increment


def _load():
    spec = importlib.util.spec_from_file_location("d28_004k", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004k"] = m
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

def test_01_outside_body_length_value(R):
    d = {x.name: x for x in R["datums"]}
    assert d["outside_body_profile_length"].value_in == 20.21875


def test_02_internal_block_to_block_value(R):
    d = {x.name: x for x in R["datums"]}
    x = d["internal_headblock_tailblock_length"]
    assert x.value_in == 30.4375
    assert "developed" not in x.meaning.lower().split("not the developed")[0]


def test_03_waist_radius_value_and_axis(R):
    d = {x.name: x for x in R["datums"]}
    x = d["waist_radius"]
    assert x.value_in == 4.4375
    assert x.axis == "plan_radius"


def test_04_waist_side_height_value_and_axis(R):
    d = {x.name: x for x in R["datums"]}
    x = d["waist_side_height"]
    assert x.value_in == 4.220
    assert x.axis == "side_depth"


def test_05_developed_rim_not_hardcoded_to_30_4375(R):
    d = {x.name: x for x in R["datums"]}
    dev = d["developed_rim_length"]
    assert dev.value_in is None  # deferred to 004L, never proxied by 30.4375
    assert dev.axis == "developed_arc"


def test_06_no_datum_classifies_4_4375_as_depth(R):
    d = {x.name: x for x in R["datums"]}
    wr = d["waist_radius"]
    assert "depth" not in wr.meaning.lower()
    assert wr.classification != "DEEP"
    # the only datum on the side_depth axis is the 4.220 side height, not 4.4375
    side = [x for x in R["datums"] if x.axis == "side_depth"]
    assert all(x.value_in != 4.4375 for x in side)


def test_07_30_4375_relabelled_from_developed(R):
    x = {d.name: d for d in R["datums"]}["internal_headblock_tailblock_length"]
    assert x.prior_interpretation is not None
    assert "developed" in x.prior_interpretation.lower()


# --- 2. Mathematical / invariant ---------------------------------------------

def test_10_invariant_outside_ne_internal(R):
    assert R["invariants"]["outside_ne_internal"] is True


def test_11_invariant_internal_ne_developed_semantic(R):
    assert R["invariants"]["internal_ne_developed_semantic"] is True
    assert R["invariants"]["developed_value_deferred"] is True


def test_12_invariant_radius_ne_sideheight_semantic(R):
    inv = R["invariants"]
    assert inv["radius_ne_sideheight_semantic"] is True
    assert inv["radius_axis"] != inv["sideheight_axis"]


def test_13_all_invariants_hold(R):
    assert R["all_invariants_hold"] is True
    assert R["disp"] == "SOURCE_DATUM_RECONCILED"


def test_14_three_lengths_mutually_distinct(R):
    d = {x.name: x for x in R["datums"]}
    outside = d["outside_body_profile_length"].value_in
    internal = d["internal_headblock_tailblock_length"].value_in
    # developed is NULL here; distinctness of its axis is the semantic guarantee
    assert outside != internal
    assert d["developed_rim_length"].axis not in (
        d["outside_body_profile_length"].axis, d["internal_headblock_tailblock_length"].axis)


def test_15_superseded_records_present(R):
    loci = [s["locus"] for s in R["superseded"]]
    assert loci.count("004C") >= 3
    assert loci.count("004D") >= 2
    joined = json.dumps(R["superseded"])
    assert "s / 30.4375" in joined or "s/30.4375" in joined.replace(" ", "")
    assert "plate" in joined.lower()


# --- 3. Regression / anti-drift (NEW governing artifacts only) ---------------

def test_20_reconciliation_csv_has_no_depth_for_radius(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_DIMENSION_RECONCILIATION_004K.csv")
    wr = next(r for r in rows if r["name"] == "waist_radius")
    assert wr["axis"] == "plan_radius"
    assert "assembled depth" not in wr["meaning"].lower()


def test_21_new_section_frames_30_4375_as_superseded_not_current(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    text = open(doc).read()
    section = text[text.index(M._S):text.index(M._E)]
    # Any mention of "30.4375 ... developed" must appear ONLY inside the superseded
    # table (prior column), each on a row that also carries the corrected "internal"
    # label and the 004K supersession marker. A bare current-tense assertion fails.
    _frames = ("004k", "004c/004d:", "prior", "superseded", "relabel", "withdrawn",
               "dev_side_len", "internal")
    for ln in section.splitlines():
        if "30.4375" in ln and "developed" in ln.lower():
            low = ln.lower()
            assert any(f in low for f in _frames), (
                f"unframed developed/30.4375 claim: {ln}")
    # the correction itself is present
    assert "internal head-block/tail-block length" in section


def test_22_governing_state_banner_corrected(tmp_path):
    doc = os.path.join(tmp_path, "REPORT.md")
    _run_write(tmp_path, doc=doc)
    text = open(doc).read()
    assert M._GS in text and M._GE in text
    banner = text[text.index(M._GS):text.index(M._GE)]
    assert "004K" in banner
    assert "20.21875" in banner and "30.4375" in banner and "4.4375" in banner
    assert "unresolved" in banner.lower()


def test_23_superseded_csv_disposition(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    rows = _rows(tmp_path, "D28_65260_SUPERSEDED_INTERPRETATIONS_004K.csv")
    assert rows and all(r["disposition"] == "SUPERSEDED_BY_DATUM_RECONCILIATION" for r in rows)


def test_24_committed_report_header_has_no_stale_current_status():
    report = os.path.join(_REPO, "docs", "experiments",
                          "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
    text = open(report, encoding="utf-8").read()
    header = text[:text.index("## Failure / Pivot Ledger")]
    low = header.lower()
    assert "> **status.**" not in low
    assert "corrected rerun 002" not in low
    assert "30.4375 in is the active developed coordinate" not in low
    assert "back_curvature_field_established" not in low
    assert "constructed admissible back family" in low
    assert "exact physical endpoints and measurement path remain **unresolved**" in low


# --- 4. Provenance / reproducibility -----------------------------------------

def test_30_parent_ancestry():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _PARENT, "HEAD"],
                          cwd=_REPO).returncode == 0


def test_31_no_pdf_runtime():
    txt = open(_SCRIPT).read()
    assert "pymupdf" not in txt and "fitz" not in txt and ".pdf" not in txt.lower()


def test_32_no_production_modified(tmp_path):
    spec = os.path.join(_REPO, "services", "api", "app", "instrument_geometry", "specs",
                        "martin_d28_1937.json")
    before = _sha(spec)
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert _sha(spec) == before


def test_33_no_prior_result_modified(tmp_path):
    watched = ["D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
               "D28_65260_REGISTERED_RIM_004D.csv",
               "D28_65260_BACK_FAMILY_MEMBERS_004G.csv",
               "D28_65260_CURVATURE_FIELD_004J.csv"]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    assert before == {f: _sha(os.path.join(_RESULTS, f)) for f in watched}


def test_34_deterministic_regeneration(tmp_path):
    d1 = tmp_path / "a"
    d2 = tmp_path / "b"
    os.makedirs(d1); os.makedirs(d2)
    _run_write(d1, doc=os.path.join(d1, "REPORT.md"))
    _run_write(d2, doc=os.path.join(d2, "REPORT.md"))
    for n in ("D28_65260_SOURCE_DATUM_AUTHORITY_004K.json",
              "D28_65260_DIMENSION_RECONCILIATION_004K.csv",
              "D28_65260_SUPERSEDED_INTERPRETATIONS_004K.csv",
              "D28_65260_RERUN_004K_SUMMARY.csv"):
        assert _sha(os.path.join(d1, n)) == _sha(os.path.join(d2, n))


def test_35_authority_json_schema(tmp_path):
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    with open(os.path.join(tmp_path, "D28_65260_SOURCE_DATUM_AUTHORITY_004K.json")) as fh:
        auth = json.load(fh)
    assert auth["outside_body_profile_length_in"] == 20.21875
    assert auth["internal_headblock_tailblock_length_in"] == 30.4375
    assert auth["waist_radius_in"] == 4.4375
    assert auth["waist_side_height_in"] == 4.220
    assert auth["developed_rim_length_in"] is None
    assert auth["no_production_changes"] and auth["no_prior_run_alteration"]
    assert auth["pdf_vendored"] is False


def test_36_hermetic_write_touches_only_outdir(tmp_path):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                            capture_output=True, text=True).stdout
    _run_write(tmp_path, doc=os.path.join(tmp_path, "REPORT.md"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=_REPO,
                           capture_output=True, text=True).stdout
    assert before == after  # writing into tmp must not dirty the tree
