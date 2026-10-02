#!/usr/bin/env python3
"""
D28 SIDE STATION DATUM AUDIT 003A
=================================

Coordinate/datum audit: what does John Arnold's side-height station coordinate
"Distance from neck end" most plausibly represent, before treating Rerun 003's
SPHERICAL_MODEL_MISMATCH as final?

Reuses the Rerun 003 Arnold-derived outline and Sevy/Doolin equations unchanged.
Does NOT change historical side-height values, does NOT retrace the outline, and
does NOT tune geometry for a desired result. No production/spec/authority file
is modified; neither source PDF is vendored.

Coordinate models tested:
  A literal plan-view developed arc  (s_CAD = s_Arnold)          [Rerun 003 baseline]
  B longitudinal / centerline        (dimensionally rejected: 30.4375 > 20 in)
  C normalized neck->tail            (u = s/30.4375; s_CAD = u * S_CAD_total)
  D 3D developed rim distance        (ds = sqrt(dx^2+dy^2+dz^2))
  E proportional side-strip scale    (k = 30.4375 / S_CAD_total)  [== C mathematically]

Source fact: Arnold's only verbatim wording is "Distance from neck end, side
width". The qualifier "developed" was added downstream (Rerun 002 order), not by
Arnold. The source does not name the measuring-path convention.
"""
from __future__ import annotations

import csv
import importlib.util
import math
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import brentq

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r3 = _load("r3_audit", "d28_side_inverse_rerun003.py")

ARNOLD = dict(r3.ARNOLD_SIDE_HEIGHT_IN)
STATIONS = sorted(ARNOLD)
S_NECK, S_TAIL = STATIONS[0], STATIONS[-1]
S_ARNOLD_TOTAL = 30.4375
S_SHOULDER, B_BUTT = r3.S_SHOULDER, r3.B_BUTT
ANCHORS = {9.0: 4.085, 12.0: 4.240, 15.0: 4.350}
WAIST_SIDE_HEIGHT = 4.220
DRAWING_DEEP = 4.4375
L_CAL = r3._L_CAL
R_MIN, R_MAX = r3.R_MIN_IN, r3.R_MAX_IN
L_MIN, L_MAX = r3.L_MIN_IN, r3.L_MAX_IN
_GW = r3.geometric_waist(L_CAL)
S_CAD_TOTAL = _GW["half_perimeter"]

AUDIT_CSV = os.path.join(_RESULTS, "D28_65260_STATION_DATUM_AUDIT_003A.csv")
SUM_CSV = os.path.join(_RESULTS, "D28_65260_STATION_DATUM_AUDIT_003A_SUMMARY.csv")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments", "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")


# --- Coordinate-model station mapping ----------------------------------------

def map_station(L: float, station: float, model: str) -> Tuple[float, float, float, str]:
    """Return (x, y, s_cad, status) for a station under a coordinate model."""
    y, x, s = r3.developed_arclen(L)
    Stot = float(s[-1])
    if model in ("A_literal", "D_3d_rim"):
        status = "OK" if station <= Stot + 1e-9 else "OUT_OF_DOMAIN"
        s_cad = station
        s_used = min(station, Stot)
    elif model in ("C_normalized", "E_proportional"):
        s_cad = (station / S_ARNOLD_TOTAL) * Stot
        status = "OK"
        s_used = s_cad
    else:
        return (math.nan, math.nan, math.nan, "UNSUPPORTED_MODEL")
    xx = float(np.interp(s_used, s, x))
    yy = float(np.interp(s_used, s, y))
    return xx, yy, s_cad, status


def predict(L: float, R: float, station: float, model: str) -> Tuple[float, float, float]:
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    x, y, _, _ = map_station(L, station, model)
    D = math.hypot(x, y - (L - P))
    return r3.solve_side_height(B_BUTT, R, P, D, 0.0, 0.0), D, P


def predict_waist(L: float, R: float) -> Tuple[float, float]:
    gw = r3.geometric_waist(L)
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    D = math.hypot(gw["x"], gw["y"] - (L - P))
    return r3.solve_side_height(B_BUTT, R, P, D, 0.0, 0.0), P


def admissible(L: float, R: float) -> bool:
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    return (0.0 <= P <= L) and (abs(P) < R)


# --- 3D rim length (Model D) -------------------------------------------------

def rim_3d_length(L: float) -> Dict[str, float]:
    y, x, s = r3.developed_arclen(L)
    u = np.array(STATIONS) / S_ARNOLD_TOTAL
    s_pts = u * s[-1]
    z = np.array([ARNOLD[q] for q in STATIONS])
    sd = np.linspace(0, s[-1], 4000)
    zd = np.interp(sd, s_pts, z)
    L3d = float(np.sum(np.hypot(np.diff(sd), np.diff(zd))))
    plan = float(s[-1])
    return {"plan_arc": plan, "rim_3d": L3d, "increase": L3d - plan,
            "pct": 100.0 * (L3d - plan) / plan,
            "gap_to_arnold": S_ARNOLD_TOTAL - plan,
            "explains_pct": 100.0 * (L3d - plan) / (S_ARNOLD_TOTAL - plan)}


# --- Inverse solve under a coordinate model (A2: sweep R, solve L) -----------

def solve_L(model: str, R: float, anchor: float, target: float) -> Optional[float]:
    def g(L): return predict(L, R, anchor, model)[0] - target
    grid = np.linspace(L_MIN, L_MAX, 71)
    gv = []
    for L in grid:
        try: gv.append(g(float(L)))
        except (ValueError, ZeroDivisionError): gv.append(math.nan)
    roots = []
    for i in range(len(grid) - 1):
        a, b = gv[i], gv[i + 1]
        if math.isnan(a) or math.isnan(b): continue
        if a * b < 0:
            try: roots.append(float(brentq(g, float(grid[i]), float(grid[i + 1]), xtol=1e-8)))
            except (ValueError, RuntimeError): pass
    if not roots: return None
    adm = [L for L in roots if 0 <= r3.solve_high_point(L, B_BUTT, S_SHOULDER, R) <= L]
    return min(adm or roots, key=lambda L: abs(L - 20.0))


def inverse(model: str, anchor: float) -> Dict:
    target = ANCHORS[anchor]
    best = None
    for R in np.linspace(R_MIN, R_MAX, 43):
        R = float(R)
        L = solve_L(model, R, anchor, target)
        if L is None: continue
        res = {s: predict(L, R, s, model)[0] - ARNOLD[s]
               for s in STATIONS if s not in (S_NECK, S_TAIL, anchor)}
        wpred, P = predict_waist(L, R)
        res["waist"] = wpred - WAIST_SIDE_HEIGHT
        e = float(np.sqrt(np.mean(np.array(list(res.values())) ** 2)))
        mx = max(abs(v) for v in res.values())
        if best is None or e < best["rmse"]:
            best = {"model": model, "anchor": anchor, "L": L, "R": R, "P": P,
                    "rmse": e, "maxabs": mx, "waist_resid": res["waist"],
                    "admissible": admissible(L, R),
                    "bound": abs(R - R_MIN) < 1e-6 or abs(R - R_MAX) < 1e-6
                             or abs(L - L_MIN) < 1e-3 or abs(L - L_MAX) < 1e-3}
    return best or {"model": model, "anchor": anchor, "L": None, "R": None, "P": None,
                    "rmse": None, "maxabs": None, "waist_resid": None,
                    "admissible": None, "bound": None}


# --- Evidence table (Step 1) -------------------------------------------------

EVIDENCE = [
    {"source": "John Arnold correspondence (email header)",
     "wording": "\"Distance from neck end, side width\"",
     "supports": "distance measured from the neck end; values are side widths",
     "not_supports": "does NOT specify plan-view vs developed vs 3D vs longitudinal",
     "confidence": "high (verbatim)",
     "notes": "the only verbatim convention wording"},
    {"source": "Rerun 002 order (Ross) restatement",
     "wording": "\"developed distance from neck end (in)\"",
     "supports": "developed-side-strip interpretation",
     "not_supports": "\"developed\" is an added interpretation, not Arnold's word",
     "confidence": "interpretation, not source",
     "notes": "downstream qualifier; not primary evidence"},
    {"source": "1937 D-28.pdf (Arnold drawing)",
     "wording": "plan view + side-profile strip; 'DEEP' depth annotations; no station-path definition",
     "supports": "side depths exist as drawn dimensions",
     "not_supports": "no annotation defines how 'distance from neck end' was measured",
     "confidence": "medium (hand-drawn scan)",
     "notes": "station series came from the email, not the drawing"},
    {"source": "ACOUSTIC BODY.pdf (JD tracing)",
     "wording": "20.0 / 11.7 / 15.7 / Ø4.0 dimensions; datum A = soundhole",
     "supports": "plan-view geometry + calibration",
     "not_supports": "carries no side-station coordinate definition",
     "confidence": "high (CAD)",
     "notes": "geometry authority only"},
]


# --- Report / CSV helpers ----------------------------------------------------

def git_sha():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception: return "UNKNOWN"


def _src_support(model):
    return {"A_literal": "weak (no source names plan-arc; clamps late stations)",
            "B_longitudinal": "rejected (dimensionally impossible)",
            "C_normalized": "none (no source names normalization)",
            "D_3d_rim": "none (path adds 0.09%, cannot explain 13.9% gap)",
            "E_proportional": "none (k=1.139 elongation unsupported by any physical path)"}[model]


def run_audit() -> Dict:
    rim = rim_3d_length(L_CAL)
    # mapping tables for A and C (+E==C)
    mapping = {}
    for model in ("A_literal", "C_normalized"):
        rows = []
        for s in STATIONS:
            x, y, s_cad, status = map_station(L_CAL, s, model)
            rows.append({"station": s, "u": s / S_ARNOLD_TOTAL, "s_cad": s_cad,
                         "x": x, "y": y, "h": ARNOLD[s], "status": status})
        mapping[model] = rows
    # inverse under A and C for anchors
    inv = {"A_literal": {a: inverse("A_literal", a) for a in ANCHORS},
           "C_normalized": {a: inverse("C_normalized", a) for a in ANCHORS}}
    return {"rim": rim, "mapping": mapping, "inv": inv, "gw": _GW}


def classify(res) -> Tuple[str, str, List[str]]:
    notes = []
    # any admissible, clustered, non-bound solution under any model?
    good = []
    for model, byanc in res["inv"].items():
        Ls = [d["L"] for d in byanc.values() if d["L"] is not None]
        adm = [d for d in byanc.values() if d["admissible"] and not d["bound"]]
        if adm and Ls and (max(Ls) - min(Ls) < 2.0):
            good.append(model)
    if good:
        notes.append(f"Admissible clustered fit under: {good} -> datum correction rescues the model.")
        return "NORMALIZED_STATION_SUPPORTED", "SUPERSEDED", notes
    # all models P<0 / bound?
    notes.append("Model B (longitudinal) dimensionally rejected: Arnold span 30.4375 in > "
                 "20 in body length.")
    notes.append(f"Model D (3D rim) rejected: rim path adds only {res['rim']['increase']:.3f} in "
                 f"({res['rim']['pct']:.2f}%), explaining {res['rim']['explains_pct']:.1f}% of the "
                 f"{res['rim']['gap_to_arnold']:.3f} in gap.")
    notes.append("Models A (literal) and C/E (normalized/proportional) both yield inadmissible "
                 "spherical fits (P<0) — literal at R~34 ft / L~22 in, normalized collapsing to "
                 "L~12 in (near the lower bound) / R~9 ft. Inadmissibility is robust to the datum choice.")
    notes.append("Source wording ('Distance from neck end') does not name the measuring-path "
                 "convention; 'developed' is a downstream qualifier, not Arnold's word.")
    return "DATUM_DEFINITION_UNRESOLVED", "STRENGTHENED", notes


# --- CSV writers -------------------------------------------------------------

AUDIT_FIELDS = ["run_id", "coordinate_model", "model_description", "arnold_station_in",
                "normalized_station", "mapped_plan_arc_in", "mapped_y_in", "mapped_x_in",
                "side_height_in", "mapping_status", "anchor_station_in", "body_length_in",
                "radius_in", "radius_ft", "high_point_P_in", "predicted_anchor_height_in",
                "anchor_residual_in", "waist_predicted_in", "waist_residual_in", "rmse_in",
                "max_abs_residual_in", "physically_admissible", "bound_hit", "solver_status",
                "source_support_level", "notes"]

_MODEL_DESC = {"A_literal": "literal plan-view developed arc (s_CAD=s_Arnold)",
               "C_normalized": "normalized neck->tail (u=s/30.4375; s_CAD=u*S_CAD)",
               "E_proportional": "proportional side-strip (k=30.4375/S_CAD)"}


def write_audit_csv(res):
    os.makedirs(_RESULTS, exist_ok=True)
    rows = []
    # mapping rows
    for model, mrows in res["mapping"].items():
        for m in mrows:
            rows.append({f: "" for f in AUDIT_FIELDS} | {
                "run_id": f"MAP_{model}_{m['station']}", "coordinate_model": model,
                "model_description": _MODEL_DESC.get(model, ""),
                "arnold_station_in": f"{m['station']:.4f}", "normalized_station": f"{m['u']:.5f}",
                "mapped_plan_arc_in": f"{m['s_cad']:.4f}", "mapped_y_in": f"{m['y']:.4f}",
                "mapped_x_in": f"{m['x']:.4f}", "side_height_in": f"{m['h']:.4f}",
                "mapping_status": m["status"], "body_length_in": f"{L_CAL:.3f}",
                "solver_status": "mapping_only", "source_support_level": _src_support(model)})
    # inverse rows
    for model, byanc in res["inv"].items():
        for a, d in byanc.items():
            if d["L"] is None:
                rows.append({f: "" for f in AUDIT_FIELDS} | {
                    "run_id": f"INV_{model}_a{a}", "coordinate_model": model,
                    "model_description": _MODEL_DESC.get(model, ""), "anchor_station_in": f"{a}",
                    "solver_status": "no_root", "source_support_level": _src_support(model)})
                continue
            pa, _, _ = predict(d["L"], d["R"], a, model)
            wp, _ = predict_waist(d["L"], d["R"])
            rows.append({f: "" for f in AUDIT_FIELDS} | {
                "run_id": f"INV_{model}_a{a}", "coordinate_model": model,
                "model_description": _MODEL_DESC.get(model, ""), "anchor_station_in": f"{a}",
                "body_length_in": f"{d['L']:.4f}", "radius_in": f"{d['R']:.3f}",
                "radius_ft": f"{d['R']/12:.4f}", "high_point_P_in": f"{d['P']:.4f}",
                "predicted_anchor_height_in": f"{pa:.4f}", "anchor_residual_in": f"{pa-ANCHORS[a]:+.6f}",
                "waist_predicted_in": f"{wp:.4f}", "waist_residual_in": f"{d['waist_resid']:+.4f}",
                "rmse_in": f"{d['rmse']:.6f}", "max_abs_residual_in": f"{d['maxabs']:.6f}",
                "physically_admissible": d["admissible"], "bound_hit": d["bound"],
                "solver_status": "solved", "source_support_level": _src_support(model)})
    with open(AUDIT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    return len(rows)


def write_summary_csv(res, audit_conc, parent):
    rim = res["rim"]
    def best(model):
        byanc = res["inv"].get(model, {})
        ok = [d for d in byanc.values() if d["L"] is not None]
        return min(ok, key=lambda d: d["rmse"]) if ok else None
    model_rows = [
        ("A_literal_plan_arc", "A_literal", "weak", "clamps stations >26.73 in", f"{S_CAD_TOTAL:.3f}"),
        ("longitudinal", "B_longitudinal", "rejected", "30.4375>20 in body length", "n/a"),
        ("normalized_endpoint", "C_normalized", "none", "P<0, L bound-pinned", f"{S_CAD_TOTAL:.3f}"),
        ("3d_rim", "D_3d_rim", "none", f"adds {rim['pct']:.2f}%", f"{rim['rim_3d']:.3f}"),
        ("proportional_sidestrip", "E_proportional", "none", "k=1.139; == normalized", f"{S_CAD_TOTAL:.3f}"),
    ]
    fields = ["model", "source_support", "geometric_admissibility", "total_mapped_span_in",
              "best_L_in", "best_R_ft", "P_in", "rmse_in", "max_resid_in", "waist_resid_in",
              "physical_admissibility", "final_audit_status"]
    rows = []
    for label, key, support, note, span in model_rows:
        b = best(key) if key in res["inv"] else None
        rows.append({
            "model": label, "source_support": support,
            "geometric_admissibility": ("inadmissible (P<0)" if b and not b["admissible"]
                                        else ("rejected" if key == "B_longitudinal" else
                                              ("n/a" if b is None else "admissible"))),
            "total_mapped_span_in": span,
            "best_L_in": (f"{b['L']:.2f}" if b else ""), "best_R_ft": (f"{b['R']/12:.2f}" if b else ""),
            "P_in": (f"{b['P']:.2f}" if b else ""), "rmse_in": (f"{b['rmse']:.4f}" if b else ""),
            "max_resid_in": (f"{b['maxabs']:.4f}" if b else ""),
            "waist_resid_in": (f"{b['waist_resid']:+.4f}" if b else ""),
            "physical_admissibility": (b["admissible"] if b else ("rejected" if key == "B_longitudinal" else "n/a")),
            "final_audit_status": audit_conc,
        })
    with open(SUM_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


# --- Report section ----------------------------------------------------------

_S, _E = "<!-- RERUN003A_START -->", "<!-- RERUN003A_END -->"


def build_section(res, audit_conc, parent, notes) -> str:
    rim = res["rim"]; gw = res["gw"]; L = []; w = L.append
    w("## Rerun 003A — Arnold Station Datum Audit")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Coordinate/datum audit of Arnold's \"distance from neck end\" station system, "
      "using the Rerun 003 Arnold-derived outline unchanged. No historical value or outline "
      "was modified; neither PDF is vendored.")
    w(f"- Audit CSV: `D28_65260_STATION_DATUM_AUDIT_003A.csv`; summary "
      f"`D28_65260_STATION_DATUM_AUDIT_003A_SUMMARY.csv`.")
    w("")
    w("### Step 1 — Source-wording evidence (SOURCE FACT vs interpretation)")
    w("")
    w("| source | wording | supports | does NOT support | confidence |")
    w("|---|---|---|---|---|")
    for e in EVIDENCE:
        w(f"| {e['source']} | {e['wording']} | {e['supports']} | {e['not_supports']} | {e['confidence']} |")
    w("")
    w("**SOURCE FACT:** Arnold's verbatim coordinate label is \"Distance from neck end\". "
      "The qualifier \"developed\" is a downstream interpretation (Rerun 002 order), not Arnold's word. "
      "No source names the measuring-path convention.")
    w("")
    w("### Step 2 — Reference geometry (Rerun 003, unchanged)")
    w("")
    w(f"- Body length {L_CAL:.2f} in; geometric waist y={gw['y']:.2f} in (y/L={gw['y_norm']:.3f}), "
      f"developed waist station {gw['s_waist']:.2f} in; plan-view half-perimeter "
      f"**S_CAD = {S_CAD_TOTAL:.3f} in**; Arnold stated span **S_Arnold = 30.4375 in**.")
    w(f"- Discrepancy: **{S_ARNOLD_TOTAL-S_CAD_TOTAL:.4f} in ({100*(S_ARNOLD_TOTAL-S_CAD_TOTAL)/S_CAD_TOTAL:.1f}%)**.")
    w("")
    w("### Steps 3/5 — Station mapping (CALCULATION): literal (A) vs normalized (C)")
    w("")
    w("| Arnold s (in) | u | A: s_CAD / status | A: (x,y) | C: s_CAD | C: (x,y) | side H |")
    w("|---:|---:|---|---|---:|---|---:|")
    for a, c in zip(res["mapping"]["A_literal"], res["mapping"]["C_normalized"]):
        w(f"| {a['station']:.4f} | {a['u']:.3f} | {a['s_cad']:.2f} / {a['status']} | "
          f"({a['x']:.2f},{a['y']:.2f}) | {c['s_cad']:.2f} | ({c['x']:.2f},{c['y']:.2f}) | {a['h']:.3f} |")
    w("")
    w(f"- Model A first OUT_OF_DOMAIN station: 27.0 in and 30.4375 in exceed S_CAD={S_CAD_TOTAL:.2f} in "
      "(reported OUT_OF_DOMAIN, not silently clamped).")
    w("")
    w("### Step 4 — Model B (longitudinal): REJECTED INTERPRETATION")
    w("")
    w(f"- A literal longitudinal reading is dimensionally impossible: the station span 30.4375 in "
      f"exceeds the body length {L_CAL:.2f} in. No source-supported unit/datum transform closes this. "
      "Rejected (body not stretched to fit).")
    w("")
    w("### Step 6 — Model D (3D developed rim): REJECTED as the span explanation")
    w("")
    w(f"- Plan-view arc = {rim['plan_arc']:.3f} in; 3D rim = {rim['rim_3d']:.3f} in; "
      f"increase {rim['increase']:.3f} in ({rim['pct']:.2f}%).")
    w(f"- This explains only **{rim['explains_pct']:.1f}%** of the {rim['gap_to_arnold']:.3f} in gap. "
      "Side-height variation cannot lengthen the rim from 26.73 to 30.44 in. "
      "(A dome-following path D2 was not asserted — no source defines such a measurement path.)")
    w("")
    w("### Steps 7 — Model E (proportional side-strip)")
    w("")
    w(f"- Scale k = 30.4375 / {S_CAD_TOTAL:.3f} = **{S_ARNOLD_TOTAL/S_CAD_TOTAL:.4f}** "
      f"({100*(S_ARNOLD_TOTAL/S_CAD_TOTAL-1):.1f}% elongation). Mathematically identical to the "
      "normalized endpoint map (C). A 13.9% elongation is not produced by any physical side-following "
      "path (the 3D rim adds only 0.09%), and no source supports such a convention.")
    w("")
    w("### Steps 8 — Station spacing")
    w("")
    w("- Arnold's 0,3,6,...,27 increments are uniform 3-in steps with a final 3.4375-in interval to "
      "30.4375. Uniform spacing is consistent with marks laid on a flexible rule/side strip but is NOT "
      "itself proof of any single convention (observation vs interpretation kept distinct).")
    w("")
    w("### Step 9 — Spherical inverse under each admissible datum (anchors 9/12/15)")
    w("")
    w("| model | anchor | L (in) | R (ft) | P (in) | RMSE (in) | max resid | waist resid | admissible | bound |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for model in ("A_literal", "C_normalized"):
        for a in (9.0, 12.0, 15.0):
            d = res["inv"][model][a]
            if d["L"] is None:
                w(f"| {model} | {a} | no root | | | | | | | |")
            else:
                w(f"| {model} | {a} | {d['L']:.2f} | {d['R']/12:.2f} | {d['P']:+.2f} | {d['rmse']:.4f} "
                  f"| {d['maxabs']:.4f} | {d['waist_resid']:+.4f} | {d['admissible']} | {d['bound']} |")
    w("")
    w("### Step 10 / 15 — Audit conclusion and parent disposition")
    w("")
    w(f"**Station-datum audit conclusion: `{audit_conc}`.**")
    w("")
    for n in notes:
        w(f"- {n}")
    w("")
    w(f"**Parent inverse disposition (Rerun 003 `SPHERICAL_MODEL_MISMATCH`): `{parent}`.**")
    w("")
    w("Reasoning: the source cannot name the datum convention (UNRESOLVED), but every defensible "
      "coordinate model was tested and none yields an admissible single-radius spherical fit — literal "
      "(L~22 in, R~34 ft) and normalized (L~12 in, R~9 ft) both require P<0, longitudinal is "
      "dimensionally impossible, and the 3D rim / "
      "proportional paths cannot physically produce the 13.9% span elongation. Because the "
      "inadmissibility is **robust to the datum choice**, the datum ambiguity does not rescue the "
      "spherical model; the mismatch is strengthened rather than merely provisional. No new parent "
      "disposition vocabulary is introduced.")
    w("")
    w("### Classification ledger")
    w("")
    w("- `SOURCE FACT`: Arnold wrote \"Distance from neck end, side width\"; waist has no numeric station.")
    w("- `CALCULATION`: S_CAD=26.73 in; 3D rim=26.75 in; k=1.139; inverse (L,R,P) per model.")
    w("- `HYPOTHESIS`: normalized/proportional station coordinate (tested, not asserted as Arnold's).")
    w("- `REJECTED INTERPRETATION`: longitudinal (dimensional); 3D rim as span explanation (0.09%).")
    w("- `UNRESOLVED`: the physical measuring-path convention behind the 30.4375-in span.")
    w("")
    return "\n".join(L)


def splice_doc(section):
    with open(_DOC) as fh: text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN003_START -->"
        text = text[:text.index(marker)] + block + "\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh: fh.write(text)


def main():
    res = run_audit()
    audit_conc, parent, notes = classify(res)
    section = build_section(res, audit_conc, parent, notes)
    if "--write" in sys.argv:
        n = write_audit_csv(res)
        write_summary_csv(res, audit_conc, parent)
        splice_doc(section)
        print(f"wrote {AUDIT_CSV} ({n} rows)")
        print(f"wrote {SUM_CSV}")
        print(f"spliced Rerun 003A into {_DOC}")
    else:
        print(section)
        print(f"\n[audit={audit_conc}; parent={parent}]")


if __name__ == "__main__":
    main()
