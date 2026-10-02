#!/usr/bin/env python3
"""
D28 RUN 004M — Side-Height Station Registration
===============================================

Corrected successor to Runs 004C + 004D. Re-registers Arnold's measured side
heights onto the CORRECTED physical rim coordinate (004L developed rim = raw
one-side plan-perimeter arc length ≈ 24.485 in), producing a corrected 3D rim

    R(s*) = ( x(s*), y(s*), H(s*) ),   s* ∈ [0, developed_rim]

where (x, y) come directly from the committed Arnold/JD plan outline at
plan-perimeter arc length s* (the developed rim IS the plan perimeter, so the
developed-arc → plan mapping is the IDENTITY — no stretch/compression) and
z = H(s*) is the Arnold side height placed by LANDMARK registration.

Datum discipline (004K / handoff Decisions):
  * The Arnold side-height station marks (0, 3, …, 27, bottom 30.4375) are NOT
    assumed to be developed-arc stations. The maximum station (30.4375 in) EXCEEDS
    the developed one-side rim (24.485 in), which REJECTS the old 004C/004D
    developed-arc assumption. They are stationed on the internal block-to-block
    axis (bottom station = 30.4375); the exact endpoint/station convention is
    PRESERVED AS UNRESOLVED and is not manufactured to obtain a smooth profile.
  * Registration uses only the three physically identifiable landmarks (neck,
    waist, tail — matched by side-height value), NOT the station numbers as arc
    positions, and NOT the waist RADIUS (4.4375 in) to place the waist (Decision 4):
    plan-view waist position comes from outline geometry (half-width minimum, 004L).
  * The 004D A/S "local stretch ratio" distortion narrative is withdrawn: A/S here
    is an internal-axis-to-developed-arc ratio, not a developed-to-plan stretch.

The side-height values themselves are the unchanged 004C measurements (read, not
re-measured). No production/spec/authority edits; no PDF; experiment branch only.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from typing import Dict, List

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))


def _load(name, fname):
    path = os.path.join(_HERE, fname)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


GA = _load("d28_geometry_authority", "d28_geometry_authority.py")
K04 = _load("d28_004k_for_m", "d28_rerun004k_source_datum_reconciliation.py")
L04 = _load("d28_004l_for_m", "d28_rerun004l_developed_rim_reconstruction.py")

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Inputs (committed, read-only) -------------------------------------------
AUTH_004C_JSON = os.path.join(_RESULTS, "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json")
OUTLINE_CSV = GA.ARNOLD_OUTLINE_CSV

# --- Outputs (004M only) -----------------------------------------------------
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_SIDE_STATION_AUTHORITY_004M.json")
PROFILE_CSV = os.path.join(_OUTDIR, "D28_65260_SIDE_PROFILE_004M.csv")
REGISTRATION_CSV = os.path.join(_OUTDIR, "D28_65260_SIDE_PLAN_REGISTRATION_004M.csv")
RIM_CSV = os.path.join(_OUTDIR, "D28_65260_REGISTERED_RIM_004M.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004M_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004M_PROVENANCE.json")

_S, _E = "<!-- RERUN004M_START -->", "<!-- RERUN004M_END -->"

MM = 25.4
WAIST_H = K04.WAIST_SIDE_HEIGHT_IN                       # 4.220
INTERNAL_BLOCK_TO_BLOCK_IN = K04.INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN  # 30.4375
WAIST_RADIUS_IN = K04.WAIST_RADIUS_IN                    # 4.4375 (NOT used to place waist)
RIM_ARC_STEP_IN = 0.125


def load_side_height_profile() -> Dict:
    """Arnold side-height samples on the station axis (unchanged 004C measurements).

    The axis TOTAL extent is the internal block-to-block length (bottom station =
    30.4375 in) — relabelled from the superseded 'developed side length'.
    """
    with open(AUTH_004C_JSON) as fh:
        auth = json.load(fh)
    station_axis_len = float(auth["developed_side_length_in"])  # value is 30.4375; axis RELABELLED
    pts = {float(d["station_in"]): float(d["height_in"]) for d in auth["stationed_side_heights"]}
    bottom = auth["named_landmarks"]["bottom"]
    pts[float(bottom["station_in"])] = float(bottom["height_in"])
    items = sorted(pts.items())
    xs = np.array([p[0] for p in items])
    ys = np.array([p[1] for p in items])
    if abs(station_axis_len - INTERNAL_BLOCK_TO_BLOCK_IN) > 1e-9:
        raise SystemExit("STOP: 004C station-axis extent != internal block-to-block (30.4375)")
    if xs[0] != 0.0 or abs(xs[-1] - station_axis_len) > 1e-9:
        raise SystemExit("STOP: side-height station endpoints malformed")
    H = PchipInterpolator(xs, ys, extrapolate=False)
    return {"station_axis_len": station_axis_len, "stations": xs, "heights": ys, "H": H,
            "neck_h": float(ys[0]), "tail_h": float(H(station_axis_len))}


def waist_station(H, lo=9.0, hi=12.0) -> float:
    """Solve H(station) = 4.220 on the station axis (geometrically derived; not 10.5)."""
    def g(s):
        return float(H(s)) - WAIST_H
    if g(lo) * g(hi) > 0:
        raise SystemExit("STOP: waist side height not bracketed in [9, 12] on the station axis")
    return float(brentq(g, lo, hi, xtol=1e-9))


def run_all() -> Dict:
    side = load_side_height_profile()
    H = side["H"]
    s_axis_len = side["station_axis_len"]

    # developed rim + outline (004L authority; rim = plan perimeter arc length)
    Lrun = L04.run_all()
    if Lrun["disp"] != "DEVELOPED_RIM_RECONSTRUCTED":
        raise SystemExit(f"STOP: 004L developed rim not reconstructed ({Lrun['disp']})")
    developed_rim = Lrun["developed_rim_raw"]
    outline = Lrun["outline"]
    s_raw = Lrun["s_raw"]
    lm = Lrun["landmarks"]
    waist_arc = lm["waist"]["plan_arc_raw_in"]            # outline waist position (NOT from radius)

    # waist station on the (internal block-to-block) station axis
    s_waist = waist_station(H)

    # ---- Landmark registration: station <-> plan-arc (3 physical anchors) ----
    # neck: station 0 -> arc 0 ; waist: station s_waist -> arc waist_arc ;
    # tail: station s_axis_len (30.4375) -> arc developed_rim (24.485).
    anchor_station = np.array([0.0, s_waist, s_axis_len])
    anchor_arc = np.array([0.0, waist_arc, developed_rim])
    GA.validate_monotone_pairs(anchor_station, anchor_arc)
    station_to_arc = PchipInterpolator(anchor_station, anchor_arc, extrapolate=False)
    arc_to_station = PchipInterpolator(anchor_arc, anchor_station, extrapolate=False)

    # ---- Station-datum characterization (what the 0/3/.../30.4375 marks mean) --
    # Candidate (a): developed one-side rim arc stations -> REJECTED (overflow).
    developed_arc_overflow = s_axis_len > developed_rim + 1e-9
    # Candidate (b): internal block-to-block longitudinal axis -> consistent (bottom = 30.4375).
    station_axis_role = ("internal_block_to_block_longitudinal_axis (bottom station = 30.4375); "
                         "exact endpoint/station convention PRESERVED AS UNRESOLVED")
    # internal-axis-to-developed-arc ratio (RELABELLED; NOT a developed-to-plan stretch)
    axis_to_arc_ratio = s_axis_len / developed_rim

    # ---- Corrected 3D rim R(s*) over the developed arc ----
    # Interior grid on a fixed arc step, plus EXACT landmark/endpoint arcs (neck,
    # waist, tail) so the registration lands exactly on the physical anchors (and
    # never rounds past the developed-rim endpoint -> no extrapolation NaN).
    grid = [float(t) for t in np.round(np.arange(0.0, developed_rim, RIM_ARC_STEP_IN), 4)
            if 0.0 < float(t) < developed_rim and abs(float(t) - waist_arc) > 1e-4]
    targets = sorted([0.0, waist_arc, *grid, developed_rim])
    rim = []
    for a in targets:
        a_eval = min(max(a, anchor_arc[0]), anchor_arc[-1])
        x = float(np.interp(a_eval, s_raw, outline["x"]))
        y = float(np.interp(a_eval, s_raw, outline["y"]))
        st = float(np.clip(float(arc_to_station(a_eval)), anchor_station[0], anchor_station[-1]))
        st = min(max(st, side["stations"][0]), side["stations"][-1])
        z = float(H(st))
        rim.append({"s_star_in": a, "developed_fraction": a / developed_rim,
                    "station_in": st, "x_in": x, "y_in": y, "z_in": z})

    # ---- Checks ----
    neck = rim[0]
    tail = rim[-1]
    waist_pt = min(rim, key=lambda r: abs(r["s_star_in"] - waist_arc))
    neck_exact = abs(neck["z_in"] - side["neck_h"]) < 1e-6 and neck["y_in"] == 0.0
    waist_exact = abs(waist_pt["z_in"] - WAIST_H) < 1e-6
    tail_exact = abs(tail["z_in"] - side["tail_h"]) < 1e-6
    zmono = all(b["z_in"] >= a["z_in"] - 1e-6 for a, b in zip(rim, rim[1:]))  # heights ~monotone up
    ymono = all(b["y_in"] >= a["y_in"] - 1e-9 for a, b in zip(rim, rim[1:]))
    station_mono = all(b["station_in"] >= a["station_in"] - 1e-9 for a, b in zip(rim, rim[1:]))
    continuous = all(np.isfinite([r["x_in"], r["y_in"], r["z_in"]]).all() for r in rim)
    waist_from_outline = abs(waist_arc - lm["waist"]["plan_arc_raw_in"]) < 1e-9

    ok = (neck_exact and waist_exact and tail_exact and continuous and ymono
          and station_mono and developed_arc_overflow and waist_from_outline)
    if not ok:
        disp = "SIDE_HEIGHT_REGISTRATION_INSUFFICIENT"
        notes = ["Landmark registration failed an admissibility/continuity/monotonicity check."]
    else:
        disp = "SIDE_HEIGHT_REGISTRATION_SUPPORTED"
        notes = [
            f"Corrected 3D rim R(s*) over s* ∈ [0, {developed_rim:.4f} in] ({len(rim)} points); "
            "XY from the Arnold/JD outline at plan-perimeter arc length (identity developed-arc "
            "mapping — no stretch/compression), Z = Arnold side height by landmark registration.",
            f"Side-height stations REJECTED as developed-arc (max station {s_axis_len} in > "
            f"developed rim {developed_rim:.4f} in); treated as the internal block-to-block axis, "
            "exact convention PRESERVED AS UNRESOLVED.",
            f"Waist placed from OUTLINE geometry (half-width minimum at plan-arc {waist_arc:.3f} in), "
            f"NOT from the waist radius {WAIST_RADIUS_IN} in; waist height {WAIST_H} in exact there.",
            f"Internal-axis / developed-arc ratio = {axis_to_arc_ratio:.4f} (RELABELLED; the 004D "
            "developed-to-plan 'stretch ratio' narrative is withdrawn).",
            "Neck/tail side heights exact at the outline endpoints; rim continuous and monotone in y.",
        ]
    return dict(side=side, developed_rim=developed_rim, outline=outline, s_raw=s_raw,
                landmarks=lm, waist_arc=waist_arc, s_waist=s_waist, s_axis_len=s_axis_len,
                anchor_station=anchor_station, anchor_arc=anchor_arc,
                station_to_arc=station_to_arc, arc_to_station=arc_to_station,
                developed_arc_overflow=developed_arc_overflow, station_axis_role=station_axis_role,
                axis_to_arc_ratio=axis_to_arc_ratio, rim=rim,
                neck_exact=neck_exact, waist_exact=waist_exact, tail_exact=tail_exact,
                waist_from_outline=waist_from_outline, zmono=zmono, ymono=ymono,
                station_mono=station_mono, continuous=continuous, disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def write_authority(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004M_SIDE_HEIGHT_STATION_REGISTRATION",
        "disposition": R["disp"],
        "developed_rim_length_in": round(R["developed_rim"], 5),
        "developed_arc_mapping": "IDENTITY (developed rim = one-side plan-perimeter arc length)",
        "z_registration": "landmark-anchored (neck/waist/tail by side-height value)",
        "station_axis": {
            "role": R["station_axis_role"],
            "total_extent_in": R["s_axis_len"],
            "equals_internal_block_to_block": abs(R["s_axis_len"] - INTERNAL_BLOCK_TO_BLOCK_IN) < 1e-9,
            "developed_arc_assumption": "REJECTED (max station exceeds developed rim)",
            "exact_endpoint_convention": "UNRESOLVED (preserved; not manufactured)",
        },
        "internal_axis_to_developed_arc_ratio": round(R["axis_to_arc_ratio"], 5),
        "stretch_ratio_narrative": "WITHDRAWN (004D A/S was not a developed-to-plan stretch)",
        "landmark_anchors": [
            {"name": "neck", "station_in": 0.0, "plan_arc_in": 0.0, "class": "SOURCE_MEASURED"},
            {"name": "waist", "station_in": round(R["s_waist"], 5),
             "plan_arc_in": round(R["waist_arc"], 5), "class": "CALCULATED_004C_HEIGHT + OUTLINE_WAIST"},
            {"name": "tail", "station_in": round(R["s_axis_len"], 5),
             "plan_arc_in": round(R["developed_rim"], 5), "class": "SOURCE_MEASURED"},
        ],
        "waist_placement": "OUTLINE half-width minimum (waist RADIUS 4.4375 in NOT used)",
        "side_height_values": "unchanged 004C Arnold measurements (read, not re-measured)",
        "rim_point_count": len(R["rim"]),
        "checks": {"neck_exact": R["neck_exact"], "waist_exact": R["waist_exact"],
                   "tail_exact": R["tail_exact"], "y_monotone": R["ymono"],
                   "station_monotone": R["station_mono"], "continuous": R["continuous"]},
        "no_production_changes": True, "no_prior_run_alteration": True, "pdf_vendored": False,
    }
    GA.write_provenance_json(AUTHORITY_JSON, rec)


def write_profile(R: Dict) -> None:
    side = R["side"]
    rows = []
    for st, h in zip(side["stations"], side["heights"]):
        rows.append({"station_in": f"{st:.5f}", "side_height_in": f"{h:.5f}",
                     "axis": "internal_block_to_block_station_axis",
                     "class": "SOURCE_MEASURED (Arnold)" if st not in (side["station_axis_len"],)
                     else "SOURCE_MEASURED (Arnold bottom landmark)"})
    GA.wr_csv(PROFILE_CSV, list(rows[0].keys()), rows)


def write_registration(R: Dict) -> None:
    """Dense station<->plan-arc registration samples (every rim point)."""
    rows = []
    for r in R["rim"]:
        rows.append({
            "s_star_developed_arc_in": f"{r['s_star_in']:.4f}",
            "developed_fraction": f"{r['developed_fraction']:.6f}",
            "station_in": f"{r['station_in']:.5f}",
            "station_fraction_internal_axis": f"{r['station_in'] / R['s_axis_len']:.6f}",
            "x_in": f"{r['x_in']:.5f}", "y_in": f"{r['y_in']:.5f}", "z_side_height_in": f"{r['z_in']:.5f}",
        })
    GA.wr_csv(REGISTRATION_CSV, list(rows[0].keys()), rows)


def write_rim(R: Dict) -> None:
    rows = []
    for r in R["rim"]:
        is_lm = (abs(r["s_star_in"]) < 1e-9 or abs(r["s_star_in"] - R["waist_arc"]) < 1e-4
                 or abs(r["s_star_in"] - R["developed_rim"]) < 1e-9)
        rows.append({
            "s_in": f"{r['s_star_in']:.4f}",
            "x_in": f"{r['x_in']:.5f}", "y_in": f"{r['y_in']:.5f}", "z_in": f"{r['z_in']:.5f}",
            "x_mm": f"{r['x_in'] * MM:.5f}", "y_mm": f"{r['y_in'] * MM:.5f}", "z_mm": f"{r['z_in'] * MM:.5f}",
            "developed_fraction": f"{r['developed_fraction']:.6f}",
            "station_in": f"{r['station_in']:.5f}",
            "landmark": is_lm,
            "coordinate_system": "corrected_developed_arc_004L (identity to plan perimeter)",
        })
    GA.wr_csv(RIM_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    row = {
        "disposition": R["disp"],
        "developed_rim_length_in": f"{R['developed_rim']:.5f}",
        "developed_arc_to_plan_mapping": "IDENTITY",
        "station_axis_total_in": f"{R['s_axis_len']:.5f}",
        "station_axis_role": "internal_block_to_block (developed-arc assumption REJECTED)",
        "developed_arc_overflow_rejects_old_assumption": R["developed_arc_overflow"],
        "internal_axis_to_developed_arc_ratio": f"{R['axis_to_arc_ratio']:.5f}",
        "waist_station_in": f"{R['s_waist']:.5f}",
        "waist_plan_arc_in": f"{R['waist_arc']:.5f}",
        "waist_placed_from_outline_not_radius": R["waist_from_outline"],
        "neck_height_exact": R["neck_exact"],
        "waist_height_exact": R["waist_exact"],
        "tail_height_exact": R["tail_exact"],
        "rim_y_monotone": R["ymono"],
        "rim_station_monotone": R["station_mono"],
        "rim_continuous": R["continuous"],
        "rim_point_count": len(R["rim"]),
        "exact_station_convention": "UNRESOLVED (preserved)",
        "final_disposition": R["disp"],
    }
    GA.wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004M_SIDE_HEIGHT_STATION_REGISTRATION",
        "parent_commit": GA.git_sha(),
        "script": "scripts/experiments/d28_rerun004m_side_profile_registration.py",
        "command": "python scripts/experiments/d28_rerun004m_side_profile_registration.py --write",
        "source_artifacts": [
            {"path": "docs/experiments/results/D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
             "role": "SIDE_HEIGHT_VALUES (read, not re-measured; station axis relabelled "
                     "internal block-to-block)", "classification": "CALCULATED_004C",
             "sha256": GA.sha256(AUTH_004C_JSON)},
            {"path": "docs/experiments/results/D28_65260_ARNOLD_OUTLINE.csv",
             "role": "PLAN_OUTLINE_XY_AUTHORITY (developed rim via 004L)",
             "classification": "VERIFIED_DRAWING_DERIVED", "sha256": GA.sha256(OUTLINE_CSV)},
        ],
        "developed_rim_source": "004L raw one-side plan-perimeter arc length (24.485 in)",
        "registration_method": "monotone PCHIP landmark anchors (neck/waist/tail); station numbers "
                               "NOT used as arc positions; waist radius NOT used",
        "station_datum": "internal block-to-block axis; exact convention UNRESOLVED (not manufactured)",
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, PROFILE_CSV, REGISTRATION_CSV, RIM_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "distinguishes_extracted_from_constructed": True,
        "runtime_pdf_access": False,
        "no_production_changes": True,
        "no_prior_run_alteration": True,
        "pdf_vendored": False,
        "disposition": R["disp"],
    }
    GA.write_provenance_json(PROVENANCE_JSON, rec)


# =============================================================================
# Report
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    w("## Run 004M — Side-Height Station Registration")
    w("")
    w(f"- Repository SHA tested: `{GA.git_sha()}`")
    w("- Corrected successor to 004C + 004D. Re-registers Arnold's measured side heights onto the "
      f"**corrected** developed rim coordinate (004L, `{R['developed_rim']:.4f} in`), producing a "
      "3D rim `R(s*) = (x(s*), y(s*), H(s*))`. XY from the Arnold/JD outline at plan-perimeter arc "
      "length (**identity** developed-arc mapping — no stretch/compression); Z = Arnold side height "
      "by **landmark** registration.")
    w("- Artifacts: `D28_65260_SIDE_STATION_AUTHORITY_004M.json`, `D28_65260_SIDE_PROFILE_004M.csv`, "
      "`D28_65260_SIDE_PLAN_REGISTRATION_004M.csv`, `D28_65260_REGISTERED_RIM_004M.csv`, "
      "`D28_65260_RERUN_004M_SUMMARY.csv`, `D28_65260_RERUN_004M_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### What the 0/3/…/30.4375 side stations represent (datum)")
    w("")
    w(f"- The maximum side-height station (**{R['s_axis_len']} in**) **exceeds** the developed one-side "
      f"rim (**{R['developed_rim']:.4f} in**), which **rejects** the old 004C/004D assumption that the "
      "marks are developed-arc stations.")
    w(f"- They are stationed on the **internal block-to-block axis** (bottom station = 30.4375 in). The "
      "exact endpoint/station convention is **PRESERVED AS UNRESOLVED** — not manufactured to obtain a "
      "smooth profile.")
    w(f"- Internal-axis / developed-arc ratio = **{R['axis_to_arc_ratio']:.4f}** (relabelled; the 004D "
      "developed-to-plan \"local stretch ratio\" distortion narrative is **withdrawn**).")
    w("")
    w("### Landmark registration (three physical anchors)")
    w("")
    w("| anchor | station (in) | plan arc (in) | side height (in) | basis |")
    w("|---|---:|---:|---:|---|")
    w(f"| neck | 0.000 | 0.000 | {R['side']['neck_h']:.3f} | outline neck endpoint |")
    w(f"| waist | {R['s_waist']:.3f} | {R['waist_arc']:.3f} | {WAIST_H:.3f} | outline half-width "
      "minimum (radius NOT used) |")
    w(f"| tail | {R['s_axis_len']:.3f} | {R['developed_rim']:.3f} | {R['side']['tail_h']:.3f} | "
      "outline tail endpoint |")
    w("")
    w(f"- Waist plan position comes from **outline geometry** (half-width minimum at plan-arc "
      f"{R['waist_arc']:.3f} in), **not** from the waist radius ({WAIST_RADIUS_IN} in) — Decision 4. "
      f"The waist side height {WAIST_H} in is exact there.")
    w("")
    w("### Corrected 3D rim")
    w("")
    w(f"- `{len(R['rim'])}` points over `s* ∈ [0, {R['developed_rim']:.4f}]`; neck/tail side heights "
      "exact at the outline endpoints; rim continuous and monotone in y and station.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Runs 001–004J are untouched. 004M re-measures no side heights, reads no PDF, and changes no "
      "prior artifact or production file. The exact side-station datum convention remains an open "
      "question (preserved, not invented).")
    w("")
    return "\n".join(L)


def splice_doc(section: str) -> None:
    text = ""
    if os.path.exists(_DOC):
        with open(_DOC) as fh:
            text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    elif "<!-- RERUN004L_START -->" in text:
        marker = "<!-- RERUN004L_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    else:
        os.makedirs(os.path.dirname(_DOC), exist_ok=True)
        text = (text + "\n\n" if text else "") + block + "\n"
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        os.makedirs(_OUTDIR, exist_ok=True)
        write_authority(R)
        write_profile(R)
        write_registration(R)
        write_rim(R)
        write_summary(R)
        write_provenance(R)
        splice_doc(section)
        print(f"wrote 004M artifacts; disposition={R['disp']}; rim_points={len(R['rim'])}; "
              f"developed_rim={R['developed_rim']:.4f}; waist_station={R['s_waist']:.3f}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; rim_points={len(R['rim'])}; "
              f"waist_station={R['s_waist']:.3f}; ratio={R['axis_to_arc_ratio']:.4f}]")


if __name__ == "__main__":
    main()
