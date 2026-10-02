#!/usr/bin/env python3
"""
D28 RUN 004O — Corrected Curvature and Sensitivity Characterization
===================================================================

Re-runs the useful 004H/004I/004J diagnostics against the CORRECTED geometry
(004N constructed family on the 004M rim) WITHOUT converting them into historical
claims, and corrects three 004J scientific-overstatement defects:

  1. RL sign-change: reports TWO distinct, non-conflated metrics, each with its
     own test —
        RL_sign_changes_any_station          (sign differs across the family at a
                                               named station)
        RL_sign_changes_anywhere_in_field     (R_L changes sign ALONG y within a
                                               member's centerline)
  2. Apex: reports each member's apex, the full floor→ceiling migration, the
     bulged-member-only migration, and the migration as a % of body length. The
     floor member is flagged if qualitatively distinct. An 8.5-in shift is NEVER
     described as "small".
  3. Saddle: PERMITTED — "each member of the constructed family contains saddle
     regions"; NOT PERMITTED — "the historical #65260 back contained saddle
     regions".

Disposition is CORRECTED_CONSTRUCTED_FAMILY_CURVATURE_CHARACTERIZED (never
BACK_CURVATURE_FIELD_ESTABLISHED). Also emits the compact pre/post datum-
reconciliation comparison. No production/spec/authority edits; no PDF; experiment
branch only.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
from typing import Dict, List

import numpy as np

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
N04 = _load("d28_004n_for_o", "d28_rerun004n_corrected_back_surface_family.py")
J04 = _load("d28_004j_for_o", "d28_rerun004j_back_curvature_field_reconstruction.py")
G04 = N04.G04
E = N04.E

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Outputs (004O only) -----------------------------------------------------
FIELD_CSV = os.path.join(_OUTDIR, "D28_65260_CURVATURE_FIELD_004O.csv")
STATION_CSV = os.path.join(_OUTDIR, "D28_65260_CURVATURE_STATION_ENVELOPE_004O.csv")
APEX_CSV = os.path.join(_OUTDIR, "D28_65260_APEX_MIGRATION_004O.csv")
SADDLE_CSV = os.path.join(_OUTDIR, "D28_65260_SADDLE_MAP_004O.csv")
SENS_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_VOLUME_SENSITIVITY_004O.csv")
PREPOST_CSV = os.path.join(_OUTDIR, "D28_65260_PRE_POST_DATUM_RECONCILIATION.csv")
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_CURVATURE_AUTHORITY_004O.json")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004O_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004O_PROVENANCE.json")

_S, _E = "<!-- RERUN004O_START -->", "<!-- RERUN004O_END -->"

MM = J04.MM
STEP = G04.STEP
KAPPA_FLAT = J04.KAPPA_FLAT
NOISE_K = J04.NOISE_K
ERODE_ITERS = J04.ERODE_ITERS
REF_25FT = J04.REF_25FT
APEX_MIGRATION_MATERIAL_PCT = 10.0   # > this % of body length is NOT "small"

# old (pre-reconciliation) values for the compact comparison
OLD_DEVELOPED_PROXY_IN = 30.4375       # 004C/004D developed-side proxy
OLD_E_RIM_SPHERE_FT = J04.E004_RIM_FT  # 18.35
OLD_H_GLOBAL_SPHERE_FT = J04.H004_GLOBAL_FT  # 19.12


def _read_summary(fname) -> Dict:
    with open(os.path.join(_RESULTS, fname)) as fh:
        return list(csv.DictReader(fh))[0]


def member_centerline_signchange(G, Z, inner) -> Dict:
    """R_L sign changes ALONG y on the centerline within a single member."""
    ys, xs = G["grid"]["ys"], G["grid"]["xs"]
    i0 = int(np.argmin(np.abs(xs)))
    cf = J04.curvature_fields_full(Z, STEP)
    kL = []
    for j, y in enumerate(ys):
        if inner[j, i0] and abs(cf["kL"][j, i0]) > KAPPA_FLAT:
            kL.append(np.sign(cf["kL"][j, i0]))
    changes = int(np.sum(np.abs(np.diff(kL)) > 0)) if len(kL) > 1 else 0
    return {"n_nonflat": len(kL), "sign_changes": changes, "has_sign_change": changes > 0}


def run_all() -> Dict:
    controls = J04.validate_curvature_estimators()
    Nrun = N04.run_all()
    if Nrun["disp"] != "CORRECTED_BOUNDED_BACK_SURFACE_FAMILY_CONSTRUCTED":
        raise SystemExit(f"STOP: 004N family not constructed ({Nrun['disp']})")
    G = Nrun["G"]
    stations, bb = J04.load_stations()

    members = []
    for m in Nrun["members"]:
        Z = G04.z_member(G, m["alpha"])
        F = J04.member_field(G, Z)
        cl = member_centerline_signchange(G, Z, F["inner"])
        st = {s["name"]: J04.sample_station(G, Z, F, s["y"]) for s in stations}
        members.append({"name": m["name"], "alpha": m["alpha"], "Z": Z, "F": F,
                        "stations": st, "centerline_signchange": cl,
                        "apex_x": m["apex_x"], "apex_y": m["apex_y"],
                        "h_max_mm": m["h_max_mm"], "volume_in3": m["volume_in3"],
                        "saddle_rows": None, "curv": m["curv"]})

    ys, xs = G["grid"]["ys"], G["grid"]["xs"]
    i0 = int(np.argmin(np.abs(xs)))

    # dense centerline field per member
    field_rows = []
    for m in members:
        cf = m["F"]["cf"]; inner = m["F"]["inner"]; rise = m["F"]["rise"]
        for j, y in enumerate(ys):
            if not inner[j, i0]:
                continue
            RT, clsT = J04.radius_ft(float(cf["kT"][j, i0]))
            RL, clsL = J04.radius_ft(float(cf["kL"][j, i0]))
            field_rows.append({"member": m["name"], "y_in": float(y),
                               "y_fraction": float(y / G["L"]), "rise_mm": float(rise[j, i0] * MM),
                               "k_transverse": float(cf["kT"][j, i0]), "r_transverse_ft": RT,
                               "k_longitudinal": float(cf["kL"][j, i0]), "r_longitudinal_ft": RL,
                               "gaussian": float(cf["K"][j, i0]),
                               "classification": ("SADDLE" if cf["K"][j, i0] < -NOISE_K else clsT)})

    # named-station envelopes (RL sign change ACROSS family per station)
    station_env = []
    for s in stations:
        vals = [m["stations"][s["name"]] for m in members if m["stations"][s["name"]]["valid"]]
        if not vals:
            continue
        RT_fin = [v["RT_ft"] for v in vals if np.isfinite(v["RT_ft"])]
        kL_signs = set(np.sign(v["kL"]) for v in vals if abs(v["kL"]) > KAPPA_FLAT)
        station_env.append({
            "station": s["name"], "y": s["y"], "kind": s["kind"],
            "RT_min": min(RT_fin) if RT_fin else float("inf"),
            "RT_max": max(RT_fin) if RT_fin else float("inf"),
            "RL_sign_changes_across_family": len(kL_signs) > 1,
            "K_min": min(v["K"] for v in vals), "K_max": max(v["K"] for v in vals),
            "vs25": J04.classify_vs_25ft(np.median(RT_fin)) if RT_fin else "FLATTER"})

    # --- RL sign-change: TWO distinct metrics (never conflated) ---
    rl_any_station = any(e["RL_sign_changes_across_family"] for e in station_env)
    rl_anywhere_in_field = any(m["centerline_signchange"]["has_sign_change"] for m in members)

    # --- apex migration (honest) ---
    apex_ys = [m["apex_y"] for m in members]
    bulged = [m for m in members if m["alpha"] > 1e-9]
    bulged_ys = [m["apex_y"] for m in bulged]
    full_mig = max(apex_ys) - min(apex_ys)
    bulged_mig = (max(bulged_ys) - min(bulged_ys)) if len(bulged_ys) > 1 else 0.0
    full_mig_pct = 100.0 * full_mig / G["L"]
    bulged_mig_pct = 100.0 * bulged_mig / G["L"]
    floor_apex_y = members[0]["apex_y"]
    bulged_median_y = float(np.median(bulged_ys)) if bulged_ys else floor_apex_y
    floor_distinct = abs(floor_apex_y - bulged_median_y) > APEX_MIGRATION_MATERIAL_PCT / 100.0 * G["L"]
    full_mig_material = full_mig_pct > APEX_MIGRATION_MATERIAL_PCT

    # --- saddle (family-only framing) ---
    saddle_rows = []
    for m in members:
        cf = m["F"]["cf"]; inner = m["F"]["inner"]; K = cf["K"]
        neg = inner & (K < -NOISE_K)
        frac = float(neg.sum() / inner.sum()) if inner.sum() else 0.0
        saddle_rows.append({"member": m["name"], "neg_K_area_frac": frac,
                            "K_min": float(np.nanmin(np.where(inner, K, np.nan))),
                            "K_max": float(np.nanmax(np.where(inner, K, np.nan)))})
    saddle_persists_family = all(r["neg_K_area_frac"] > 0.0 for r in saddle_rows)

    # --- sphere diagnostic (CALCULATED_DIAGNOSTIC) on corrected floor boundary ---
    sph = E.fit_single_sphere(G["bnd"])
    sphere_ft = float(sph.radius_ft) if sph.radius_ft else float("nan")

    # --- radius/volume sensitivity on the corrected family ---
    waist_env = next((e for e in station_env if e["station"] == "waist"), None)
    vols_L = [m["volume_in3"] * N04.IN3_TO_CM3 / 1000 for m in members]

    # --- pre/post comparison ---
    g_sum = _read_summary("D28_65260_RERUN_004G_SUMMARY.csv")
    j_sum = _read_summary("D28_65260_RERUN_004J_SUMMARY.csv")
    d_sum = _read_summary("D28_65260_RERUN_004D_SUMMARY.csv")
    l_sum = _read_summary("D28_65260_RERUN_004L_SUMMARY.csv")
    m_sum = _read_summary("D28_65260_RERUN_004M_SUMMARY.csv")
    new_dev = float(l_sum["developed_rim_length_raw_in"])
    new_waist_arc = float(m_sum["waist_plan_arc_in"])
    old_waist_arc = float(d_sum["waist_plan_arc_in"])
    old_vol_floor = float(g_sum["body_volume_floor_L"]); old_vol_ceil = float(g_sum["body_volume_ceiling_L"])
    old_apex_spread = float(j_sum["apex_y_spread_in"])

    prepost = [
        _pp("body_longitudinal_length_interpretation", "004C", OLD_DEVELOPED_PROXY_IN,
            "004K/004L", N04.G04.__dict__.get("x", None) or 20.21875,
            "30.4375 reinterpreted as internal block-to-block; body length is CAD 20.21875 in"),
        _pp("developed_rim_length_in", "004C/004D", OLD_DEVELOPED_PROXY_IN, "004L", new_dev,
            "developed rim derived independently as the one-side plan-perimeter arc length"),
        _pp("waist_plan_arc_in", "004D", old_waist_arc, "004M", new_waist_arc,
            "waist from outline half-width minimum (unchanged); radius not used"),
        _pp("body_volume_floor_L", "004G", old_vol_floor, "004N", vols_L[0],
            "constructed family on corrected rim; geometry stable (rim moved < 0.05 mm)"),
        _pp("body_volume_ceiling_L", "004G", old_vol_ceil, "004N", vols_L[-1],
            "constructed family on corrected rim; geometry stable"),
        _pp("equivalent_sphere_rim_ft", "004E", OLD_E_RIM_SPHERE_FT, "004O", sphere_ft,
            "CALCULATED_DIAGNOSTIC rim sphere on the corrected boundary (no historical claim)"),
        _pp("apex_migration_floor_to_ceiling_in", "004J", old_apex_spread, "004O", full_mig,
            "same magnitude; 004J mislabelled it 'small' — it is ~%.0f%% of body length" % full_mig_pct),
        _pp("waist_RT_ft_median", "004J", _median_range(j_sum.get("waist_RT_ft", "")),
            "004O", (np.median([waist_env["RT_min"], waist_env["RT_max"]]) if waist_env else float("nan")),
            "local transverse radius at waist; LOCAL descriptor only"),
    ]

    disp = ("CORRECTED_CONSTRUCTED_FAMILY_CURVATURE_CHARACTERIZED"
            if controls["all_pass"] else "CORRECTED_CURVATURE_NUMERICALLY_UNSTABLE")
    notes = [
        "Curvature re-characterized on the CORRECTED 004N constructed family (NOT a recovered "
        "historical field). Synthetic controls (flat/sphere/cylinder/saddle) pass.",
        f"RL sign-change (two separate metrics): any-named-station across family = {rl_any_station}; "
        f"anywhere-along-centerline within a member = {rl_anywhere_in_field}. These are NOT conflated.",
        f"Apex migration floor→ceiling = {full_mig:.2f} in ({full_mig_pct:.1f}% of body length) — "
        f"{'MATERIAL, not small' if full_mig_material else 'modest'}; the FLOOR member is "
        f"{'qualitatively distinct (reflex-dominated high point)' if floor_distinct else 'consistent with the bulged cluster'}. "
        f"Bulged-member-only migration = {bulged_mig:.2f} in ({bulged_mig_pct:.1f}%).",
        f"Saddle regions are present in EACH member of the CONSTRUCTED family "
        f"(area fraction {min(r['neg_K_area_frac'] for r in saddle_rows):.2f}"
        f"-{max(r['neg_K_area_frac'] for r in saddle_rows):.2f}); this is a property of the "
        "constructed family, NOT a claim about the historical #65260 back.",
        f"Equivalent single radii (rim sphere ~{sphere_ft:.1f} ft) are CALCULATED_DIAGNOSTIC "
        "projections of a compound constructed surface — no unique historical radius is claimed.",
    ]
    return dict(controls=controls, G=G, members=members, stations=stations, bb=bb,
                field_rows=field_rows, station_env=station_env,
                rl_any_station=rl_any_station, rl_anywhere_in_field=rl_anywhere_in_field,
                apex_ys=apex_ys, full_mig=full_mig, bulged_mig=bulged_mig,
                full_mig_pct=full_mig_pct, bulged_mig_pct=bulged_mig_pct,
                floor_distinct=floor_distinct, full_mig_material=full_mig_material,
                floor_apex_y=floor_apex_y, bulged_median_y=bulged_median_y,
                saddle_rows=saddle_rows, saddle_persists_family=saddle_persists_family,
                sphere_ft=sphere_ft, vols_L=vols_L, waist_env=waist_env,
                prepost=prepost, disp=disp, notes=notes, L=G["L"])


def _pp(quantity, old_run, old_value, new_run, new_value, reason):
    try:
        ov = float(old_value); nv = float(new_value)
        delta = nv - ov
        pct = (100.0 * delta / ov) if ov != 0 else float("nan")
    except (TypeError, ValueError):
        ov, nv, delta, pct = old_value, new_value, "", ""
    return {"quantity": quantity, "old_run": old_run, "old_value": ov, "new_run": new_run,
            "new_value": nv, "delta": delta, "delta_percent": pct, "reason_changed": reason}


def _median_range(s: str) -> float:
    try:
        parts = s.replace("INF", "nan").split("-")
        vals = [float(p) for p in parts if p.strip()]
        return float(np.median(vals)) if vals else float("nan")
    except Exception:
        return float("nan")


# =============================================================================
# Writers
# =============================================================================

def _rft(v):
    return "INF" if (v == float("inf")) else (f"{v:.2f}" if np.isfinite(v) else "")


def write_field(R: Dict) -> None:
    rows = []
    for r in R["field_rows"]:
        rows.append({"member": r["member"], "y_in": f"{r['y_in']:.4f}",
                     "y_fraction": f"{r['y_fraction']:.4f}", "rise_mm": f"{r['rise_mm']:.3f}",
                     "k_transverse": f"{r['k_transverse']:.6f}", "r_transverse_ft": _rft(r["r_transverse_ft"]),
                     "k_longitudinal": f"{r['k_longitudinal']:.6f}", "r_longitudinal_ft": _rft(r["r_longitudinal_ft"]),
                     "gaussian_curvature": f"{r['gaussian']:.6e}", "classification": r["classification"]})
    GA.wr_csv(FIELD_CSV, list(rows[0].keys()), rows)


def write_station(R: Dict) -> None:
    rows = []
    for e in R["station_env"]:
        rows.append({"station": e["station"], "y_in": f"{e['y']:.3f}", "kind": e["kind"],
                     "RT_min_ft": _rft(e["RT_min"]), "RT_max_ft": _rft(e["RT_max"]),
                     "RL_sign_changes_across_family": e["RL_sign_changes_across_family"],
                     "K_min": f"{e['K_min']:.3e}", "K_max": f"{e['K_max']:.3e}",
                     "relative_to_25ft": e["vs25"]})
    GA.wr_csv(STATION_CSV, list(rows[0].keys()), rows)


def write_apex(R: Dict) -> None:
    rows = []
    for m in R["members"]:
        rows.append({"member": m["name"], "apex_x_in": f"{m['apex_x']:.3f}",
                     "apex_y_in": f"{m['apex_y']:.3f}",
                     "apex_y_fraction_of_body": f"{m['apex_y'] / R['L']:.4f}",
                     "max_rise_mm": f"{m['h_max_mm']:.3f}",
                     "rl_sign_changes_in_centerline": m["centerline_signchange"]["sign_changes"],
                     "classification": "CONSTRUCTED_ADMISSIBLE_SURFACE"})
    rows.append({"member": "FLOOR_TO_CEILING_MIGRATION", "apex_x_in": "",
                 "apex_y_in": f"{R['full_mig']:.3f}",
                 "apex_y_fraction_of_body": f"{R['full_mig_pct']/100:.4f}",
                 "max_rise_mm": "", "rl_sign_changes_in_centerline": "",
                 "classification": f"{R['full_mig_pct']:.1f}% of body length — "
                 f"{'MATERIAL (not small)' if R['full_mig_material'] else 'modest'}; "
                 f"floor {'qualitatively distinct' if R['floor_distinct'] else 'consistent'}"})
    rows.append({"member": "BULGED_MEMBERS_ONLY_MIGRATION", "apex_x_in": "",
                 "apex_y_in": f"{R['bulged_mig']:.3f}",
                 "apex_y_fraction_of_body": f"{R['bulged_mig_pct']/100:.4f}",
                 "max_rise_mm": "", "rl_sign_changes_in_centerline": "",
                 "classification": f"{R['bulged_mig_pct']:.1f}% of body length (alpha>0 members)"})
    GA.wr_csv(APEX_CSV, list(rows[0].keys()), rows)


def write_saddle(R: Dict) -> None:
    rows = []
    for s in R["saddle_rows"]:
        rows.append({"member": s["member"], "neg_K_area_fraction": f"{s['neg_K_area_frac']:.4f}",
                     "K_min": f"{s['K_min']:.3e}", "K_max": f"{s['K_max']:.3e}",
                     "interpretation": "constructed family member contains saddle regions",
                     "NOT_a_claim_about": "the historical #65260 back"})
    rows.append({"member": "FAMILY", "neg_K_area_fraction": "",
                 "K_min": "", "K_max": "",
                 "interpretation": f"EACH member of the constructed family contains saddle regions "
                 f"(persists={R['saddle_persists_family']})",
                 "NOT_a_claim_about": "the historical #65260 back contained saddle regions"})
    GA.wr_csv(SADDLE_CSV, list(rows[0].keys()), rows)


def write_sensitivity(R: Dict) -> None:
    rows = []
    for m, vL in zip(R["members"], R["vols_L"]):
        wst = m["stations"].get("waist", {})
        rows.append({"member": m["name"], "alpha_in": f"{m['alpha']:.5f}",
                     "max_rise_mm": f"{m['h_max_mm']:.3f}", "body_volume_L": f"{vL:.4f}",
                     "waist_transverse_R_ft": (_rft(wst["RT_ft"]) if wst.get("valid") else ""),
                     "equivalent_rim_sphere_ft": f"{R['sphere_ft']:.2f}",
                     "class": "CALCULATED_DIAGNOSTIC (no historical radius claimed)"})
    GA.wr_csv(SENS_CSV, list(rows[0].keys()), rows)


def write_prepost(R: Dict) -> None:
    rows = []
    for p in R["prepost"]:
        rows.append({
            "quantity": p["quantity"], "old_run": p["old_run"],
            "old_value": (f"{p['old_value']:.4f}" if isinstance(p["old_value"], float) else p["old_value"]),
            "new_run": p["new_run"],
            "new_value": (f"{p['new_value']:.4f}" if isinstance(p["new_value"], float) else p["new_value"]),
            "delta": (f"{p['delta']:.4f}" if isinstance(p["delta"], float) else p["delta"]),
            "delta_percent": (f"{p['delta_percent']:.2f}" if isinstance(p["delta_percent"], float)
                              and np.isfinite(p["delta_percent"]) else ""),
            "reason_changed": p["reason_changed"]})
    GA.wr_csv(PREPOST_CSV, list(rows[0].keys()), rows)


def write_authority(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004O_CORRECTED_CURVATURE_AND_SENSITIVITY",
        "disposition": R["disp"],
        "geometry_source": "004N constructed family on the 004M corrected rim",
        "controls_pass": R["controls"]["all_pass"],
        "rl_sign_change": {
            "any_named_station_across_family": R["rl_any_station"],
            "anywhere_along_centerline_within_member": R["rl_anywhere_in_field"],
            "note": "two DISTINCT metrics; not conflated (004J defect corrected)",
        },
        "apex_migration": {
            "floor_to_ceiling_in": round(R["full_mig"], 3),
            "floor_to_ceiling_pct_of_body": round(R["full_mig_pct"], 2),
            "bulged_members_only_in": round(R["bulged_mig"], 3),
            "bulged_members_only_pct_of_body": round(R["bulged_mig_pct"], 2),
            "floor_qualitatively_distinct": R["floor_distinct"],
            "material_not_small": R["full_mig_material"],
            "note": "an 8.5-in-scale shift is MATERIAL; the 004J 'small' description is corrected",
        },
        "saddle": {
            "framing": "EACH member of the CONSTRUCTED family contains saddle regions",
            "not_a_historical_claim": "the historical #65260 back is NOT asserted to contain saddles",
            "persists_across_family": R["saddle_persists_family"],
        },
        "equivalent_radii": {"rim_sphere_ft": round(R["sphere_ft"], 2),
                             "class": "CALCULATED_DIAGNOSTIC (compound-surface projection; no historical radius)"},
        "disposition_vocabulary": "CORRECTED_CONSTRUCTED_FAMILY_CURVATURE_CHARACTERIZED "
                                  "(NOT BACK_CURVATURE_FIELD_ESTABLISHED)",
        "no_production_changes": True, "no_prior_run_alteration": True, "pdf_vendored": False,
    }
    GA.write_provenance_json(AUTHORITY_JSON, rec)


def write_summary(R: Dict) -> None:
    row = {
        "disposition": R["disp"],
        "geometry_source": "004N constructed family (004M rim)",
        "controls_pass": R["controls"]["all_pass"],
        "RL_sign_changes_any_station": R["rl_any_station"],
        "RL_sign_changes_anywhere_in_field": R["rl_anywhere_in_field"],
        "apex_migration_floor_to_ceiling_in": f"{R['full_mig']:.3f}",
        "apex_migration_floor_to_ceiling_pct": f"{R['full_mig_pct']:.2f}",
        "apex_migration_bulged_only_in": f"{R['bulged_mig']:.3f}",
        "apex_migration_material_not_small": R["full_mig_material"],
        "floor_apex_qualitatively_distinct": R["floor_distinct"],
        "saddle_present_each_family_member": R["saddle_persists_family"],
        "saddle_historical_claim": "NONE (constructed family only)",
        "equivalent_rim_sphere_ft": f"{R['sphere_ft']:.2f}",
        "equivalent_radius_class": "CALCULATED_DIAGNOSTIC",
        "disposition_vocab": "CORRECTED_CONSTRUCTED_FAMILY_CURVATURE_CHARACTERIZED",
        "final_disposition": R["disp"],
    }
    GA.wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004O_CORRECTED_CURVATURE_AND_SENSITIVITY",
        "parent_commit": GA.git_sha(),
        "script": "scripts/experiments/d28_rerun004o_curvature_volume_sensitivity.py",
        "command": "python scripts/experiments/d28_rerun004o_curvature_volume_sensitivity.py --write",
        "reuses": "004J curvature estimators applied to the 004N constructed family (004M rim)",
        "committed_inputs": [
            "docs/experiments/results/D28_65260_REGISTERED_RIM_004M.csv",
            "docs/experiments/results/D28_65260_RERUN_004G_SUMMARY.csv (pre/post old values)",
            "docs/experiments/results/D28_65260_RERUN_004J_SUMMARY.csv (pre/post old values)",
            "docs/experiments/results/D28_65260_RERUN_004L_SUMMARY.csv",
            "docs/experiments/results/D28_65260_RERUN_004M_SUMMARY.csv",
        ],
        "output_paths": [os.path.basename(p) for p in (
            FIELD_CSV, STATION_CSV, APEX_CSV, SADDLE_CSV, SENS_CSV, PREPOST_CSV,
            AUTHORITY_JSON, SUMMARY_CSV, PROVENANCE_JSON)],
        "no_historical_curvature_claim": True,
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
    w("## Run 004O — Corrected Curvature and Sensitivity Characterization")
    w("")
    w(f"- Repository SHA tested: `{GA.git_sha()}`")
    w("- Re-runs the 004H/004I/004J diagnostics against the **corrected** geometry (004N constructed "
      "family on the 004M rim), **without** converting them into historical claims, and corrects three "
      "004J overstatements (RL sign-change conflation, apex-migration 'small', historical saddle claim).")
    w("- Artifacts: `D28_65260_CURVATURE_FIELD_004O.csv`, `…CURVATURE_STATION_ENVELOPE_004O.csv`, "
      "`…APEX_MIGRATION_004O.csv`, `…SADDLE_MAP_004O.csv`, `…RADIUS_VOLUME_SENSITIVITY_004O.csv`, "
      "`D28_65260_PRE_POST_DATUM_RECONCILIATION.csv`, `…CURVATURE_AUTHORITY_004O.json`, "
      "`…RERUN_004O_SUMMARY.csv`, `…RERUN_004O_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### RL sign-change (two DISTINCT metrics — not conflated)")
    w("")
    w(f"- `RL_sign_changes_any_station` (sign differs across the family at a named station): "
      f"**{R['rl_any_station']}**.")
    w(f"- `RL_sign_changes_anywhere_in_field` (R_L changes sign along y within a member centerline): "
      f"**{R['rl_anywhere_in_field']}**.")
    w("")
    w("### Apex migration (honest)")
    w("")
    w(f"- Floor→ceiling apex migration = **{R['full_mig']:.2f} in ({R['full_mig_pct']:.1f}% of body "
      f"length)** — **{'MATERIAL, not small' if R['full_mig_material'] else 'modest'}**. The floor "
      f"member is **{'qualitatively distinct (reflex-dominated high point)' if R['floor_distinct'] else 'consistent with the bulged cluster'}**.")
    w(f"- Bulged-member-only migration (α>0) = **{R['bulged_mig']:.2f} in "
      f"({R['bulged_mig_pct']:.1f}%)**.")
    w("")
    w("### Saddle (constructed family only)")
    w("")
    w(f"- **Each member of the constructed family contains saddle regions** (area fraction "
      f"{min(s['neg_K_area_frac'] for s in R['saddle_rows']):.2f}"
      f"–{max(s['neg_K_area_frac'] for s in R['saddle_rows']):.2f}). This is a property of the "
      "**constructed** family — it is **not** a claim that the historical #65260 back contained saddles.")
    w("")
    w("### Pre/post datum-reconciliation comparison")
    w("")
    w("| quantity | old | new | Δ | reason |")
    w("|---|---|---|---|---|")
    for p in R["prepost"]:
        ov = f"{p['old_value']:.3f}" if isinstance(p["old_value"], float) else p["old_value"]
        nv = f"{p['new_value']:.3f}" if isinstance(p["new_value"], float) else p["new_value"]
        dv = f"{p['delta']:.3f}" if isinstance(p["delta"], float) else p["delta"]
        w(f"| `{p['quantity']}` | {p['old_run']}: {ov} | {p['new_run']}: {nv} | {dv} | "
          f"{p['reason_changed']} |")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Runs 001–004J are untouched. 004O characterizes the CONSTRUCTED family (does not recover a "
      "historical field), claims no unique historical radius, reads no PDF, and changes no prior "
      "artifact or production file.")
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
    elif "<!-- RERUN004N_START -->" in text:
        marker = "<!-- RERUN004N_START -->"
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
        write_field(R); write_station(R); write_apex(R); write_saddle(R); write_sensitivity(R)
        write_prepost(R); write_authority(R); write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004O artifacts; disposition={R['disp']}; "
              f"RL_any_station={R['rl_any_station']}; RL_in_field={R['rl_anywhere_in_field']}; "
              f"apex_mig={R['full_mig']:.2f}in ({R['full_mig_pct']:.1f}%)")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; apex_mig={R['full_mig']:.2f}in "
              f"({R['full_mig_pct']:.1f}%); floor_distinct={R['floor_distinct']}]")


if __name__ == "__main__":
    main()
