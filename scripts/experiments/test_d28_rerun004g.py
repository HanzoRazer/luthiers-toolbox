#!/usr/bin/env python3
"""Tests for D28 Run 004G — Bounded Back-Surface Family + Body-Volume Envelope.

Covers the rim-exact α-family, monotone body volume, flat-top labeling / unresolved
top dome, fixed soundhole area, unsolved Helmholtz bridge, equivalent-radius
diagnostics, the MB Torrefied Adirondack prior (pin-referenced, not duplicated,
ZERO geometry influence), determinism, and anti-drift.
"""
from __future__ import annotations

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
_SCRIPT = os.path.join(_HERE, "d28_rerun004g_bounded_back_surface_family.py")


def _load():
    spec = importlib.util.spec_from_file_location("d28_004g", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004g"] = m
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


# --- Disposition / family ----------------------------------------------------

def test_01_disposition(R):
    assert R["disp"] == "BOUNDED_BACK_SURFACE_FAMILY_ESTABLISHED"


def test_02_five_members(R):
    assert [m["name"] for m in R["members"]] == ["floor", "q25", "mid", "q75", "ceiling"]


def test_03_rise_envelope(R):
    ms = R["members"]
    assert abs(ms[0]["h_max_mm"] - 1.61) < 0.05
    assert abs(ms[-1]["h_max_mm"] - 2.80) < 0.05


def test_04_floor_alpha_zero(R):
    assert R["members"][0]["alpha"] == 0.0


# --- Volume tests (order spec 1-10) -----------------------------------------

def test_05_volume_monotonic_in_alpha(R):          # (1)
    vols = [m["volume_in3"] for m in R["members"]]
    assert all(b > a for a, b in zip(vols, vols[1:]))


def test_06_all_members_rim_exact(R):              # (2)
    # Construction guarantee: Phi is exactly 0 on the whole perimeter, so every
    # member z = z_TPS + alpha*Phi equals z_TPS (= the rim) on the rim boundary.
    G = R["G"]
    L = G["L"]
    for y in np.linspace(0.5, L - 0.5, 12):
        hw = M.E.half_width_at(G["outline"], float(y))
        assert abs(M.phi_analytic(+hw, float(y), hw, L)) < 1e-12   # right side curve
        assert abs(M.phi_analytic(-hw, float(y), hw, L)) < 1e-12   # left side curve
    # neck/tail end segments (y = 0 and y = L)
    for x in np.linspace(-3.0, 3.0, 7):
        assert abs(M.phi_analytic(float(x), 0.0, 3.0, L)) < 1e-12
        assert abs(M.phi_analytic(float(x), L, 4.0, L)) < 1e-12


def test_07_volume_deterministic():                # (3)
    a = M.run_all(); b = M.run_all()
    assert [m["volume_in3"] for m in a["members"]] == [m["volume_in3"] for m in b["members"]]


def test_08_grid_refinement_reported(R):           # (4)
    assert R["refine"]["rel_delta"] < 0.02 and R["refine"]["vol_fine_in3"] > 0


def test_09_flat_top_reference_labeled():          # (5) + (6)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        rows = list(_read_csv(os.path.join(d, "D28_65260_BODY_VOLUME_ENVELOPE_004G.csv")))
    body_rows = [r for r in rows if r["member"] in ("floor", "ceiling")]
    assert all(r["top_assumption_class"] == "GEOMETRIC_REFERENCE_ONLY" for r in body_rows)
    assert all("UNRESOLVED" in r["case_B_top_dome"] for r in body_rows)
    assert all(float(r["top_assumption_contribution_in3"]) == 0.0 for r in body_rows)


def test_10_soundhole_area_exact():                # (7)
    assert abs(M.SOUNDHOLE_AREA_IN2 - math.pi * 4.0) < 1e-9  # pi * r^2, r=2


def test_11_helmholtz_not_solved():                # (8)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        sh = json.load(open(os.path.join(d, "D28_65260_SOUNDHOLE_VOLUME_BRIDGE_004G.json")))
    assert sh["not_solved"] is True and sh["no_guessed_A0"] and sh["no_guessed_L_eff"]
    assert "f_H" in sh["helmholtz_bridge"]["forward_f_H"]


def test_12_no_radius_forced(R):                   # (9)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json")))
        summ = _read_csv(os.path.join(d, "D28_65260_RERUN_004G_SUMMARY.csv"))[0]
    assert auth["no_member_promoted_to_the_back"] is True
    assert summ["member_promoted"].startswith("none")


def test_13_equivalent_radii_are_per_member_diagnostics():   # (10)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        rows = list(_read_csv(os.path.join(d, "D28_65260_BACK_FAMILY_BRACE_SAMPLING_004G.csv")))
    # each brace has a radius per member (diagnostic), not a single claimed value
    members_per_brace = {}
    for r in rows:
        members_per_brace.setdefault(r["brace_id"], set()).add(r["member"])
    assert all(len(v) == 5 for v in members_per_brace.values())


# --- MB prior tests ----------------------------------------------------------

def test_14_mb_subset_n_21(R):
    assert M.MB_SUBSET_N == 21 and M.MB_SUBSET == "Torrefied Adirondack"


def test_15_mb_envelope_matches_committed_values():
    env = {m[0]: (m[1], m[2], m[3]) for m in M.MB_ENVELOPE}
    assert env["density"] == (398.4, 438.38, 494.2)
    assert env["resonance_frequency"] == (74.5, 81.20, 90.3)
    assert env["youngs_modulus_stiffness"] == (10.8, 13.03, 15.8)
    assert env["quality_factor_Q"] == (158.7, 185.26, 212.0)
    assert env["time_constant"] == (635.3, 726.92, 817.7)
    assert env["radiation_coefficient"] == (10.5, 12.47, 13.6)
    assert env["thickness"] == (4.2, 4.43, 4.7)
    for _, mn, mean, mx, _u in M.MB_ENVELOPE:
        assert mn <= mean <= mx


def test_16_mb_torrefied_retained():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        rows = list(_read_csv(os.path.join(d, "D28_65260_MB_TORREFIED_ADIRONDACK_PRIOR_004G.csv")))
    assert rows and all(r["treatment"] == "torrefied" for r in rows)
    assert all(r["classification"] == "EXTERNAL_EMPIRICAL_PRIOR_TORREFIED_ADIRONDACK" for r in rows)


def test_17_mb_payload_not_duplicated_pin_referenced(R):
    # governance: no 21 per-specimen payload rows; carried by pin reference only
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        rows = list(_read_csv(os.path.join(d, "D28_65260_MB_TORREFIED_ADIRONDACK_PRIOR_004G.csv")))
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json")))
    assert len(rows) == len(M.MB_ENVELOPE)        # metric-envelope rows, NOT 21 specimen rows
    assert auth["mb_prior"]["payload_duplicated"] is False
    assert auth["mb_prior"]["corpus_pin"] == "mb-sound/v1.0.0"
    assert auth["mb_prior"]["provenance_class"] == "EXTERNAL_REFERENCE"


def test_18_mb_pin_sourced_from_committed_pin(R):
    assert R["mb_pin"]["release_tag"] == "mb-sound/v1.0.0"
    assert R["mb_pin"]["canonical_repository"] == "HanzoRazer/luthier-acoustics-data"


def test_19_mb_zero_influence_on_geometry():
    # The MB prior must NOT shape geometry. Mutating MB_ENVELOPE/subset must leave the
    # family + volumes byte-identical (geometry never reads MB).
    base = [(m["name"], m["alpha"], m["volume_in3"], m["h_max_mm"]) for m in M.run_all()["members"]]
    saved_env, saved_n = M.MB_ENVELOPE, M.MB_SUBSET_N
    try:
        M.MB_ENVELOPE = [("density", 1.0, 2.0, 3.0, "kg/m3")]
        M.MB_SUBSET_N = 999
        after = [(m["name"], m["alpha"], m["volume_in3"], m["h_max_mm"]) for m in M.run_all()["members"]]
    finally:
        M.MB_ENVELOPE, M.MB_SUBSET_N = saved_env, saved_n
    assert base == after


def test_20_no_single_species_constant():
    # distribution (min/mean/max), not one folded canonical value
    for _, mn, mean, mx, _u in M.MB_ENVELOPE:
        assert not (mn == mean == mx)


# --- Family geometry integrity ----------------------------------------------

def test_21_lower_bout_reflex_preserved(R):
    # floor member rise at lower bout dips <=0 (reflex), not clamped
    bb4 = next(b for b in R["brace_rows"] if b["brace_id"] == "BB4")
    assert bb4["rise_min_mm"] < 0.0


def test_22_genone_reference_only(R):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _run_write(d)
        auth = json.load(open(os.path.join(d, "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json")))
    assert auth["genone_reference_mm"]["range"] == [4.0, 6.0]
    assert "REFERENCE_ONLY" in auth["genone_reference_mm"]["role"]
    # family ceiling stays below GenOne range
    assert R["members"][-1]["h_max_mm"] < 4.0


def test_23_prior_runs_untouched_by_run():
    watched = ["D28_65260_REGISTERED_RIM_004D.csv", "D28_65260_RERUN_004E_SUMMARY.csv",
               "D28_65260_BACK_BRACE_POSITIONS_004F.csv"]
    before = {f: _sha(os.path.join(_RESULTS, f)) for f in watched}
    M.run_all()
    assert before == {f: _sha(os.path.join(_RESULTS, f)) for f in watched}


# --- Determinism / anti-drift ------------------------------------------------

_G_FILES = [
    "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json",
    "D28_65260_BACK_SURFACE_FAMILY_ENVELOPE_004G.csv",
    "D28_65260_BACK_FAMILY_MEMBERS_004G.csv",
    "D28_65260_BACK_FAMILY_BRACE_SAMPLING_004G.csv",
    "D28_65260_BODY_VOLUME_ENVELOPE_004G.csv",
    "D28_65260_SOUNDHOLE_VOLUME_BRIDGE_004G.json",
    "D28_65260_MB_TORREFIED_ADIRONDACK_PRIOR_004G.csv",
    "D28_65260_RERUN_004G_SUMMARY.csv",
    "D28_65260_RERUN_004G_PROVENANCE.json",
]


def test_24_write_byte_identical(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    _run_write(d1)
    _run_write(d2)
    for f in _G_FILES:
        assert _sha(os.path.join(d1, f)) == _sha(os.path.join(d2, f))


def test_25_write_does_not_dirty_committed_tree(tmp_path):
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--", "docs/experiments/"],
                              cwd=_REPO, check=True, capture_output=True, text=True).stdout
    before = status()
    _run_write(tmp_path / "out")
    assert status() == before


def test_26_report_section_survives_regen(tmp_path):
    d1, d2 = tmp_path / "a", tmp_path / "b"

    def section(d):
        with open(os.path.join(d, "REPORT.md")) as fh:
            t = fh.read()
        return t[t.index(M._S):t.index(M._E) + len(M._E)]
    _run_write(d1)
    _run_write(d2)
    assert section(d1) == section(d2) and "RERUN004G" in section(d1)


# --- helpers -----------------------------------------------------------------

def _read_csv(path):
    import csv
    with open(path) as fh:
        return list(csv.DictReader(fh))
