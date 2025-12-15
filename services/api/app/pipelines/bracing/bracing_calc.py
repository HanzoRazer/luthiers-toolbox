#!/usr/bin/env python3
import argparse, json, math, os

def length_of_polyline(points):
    d = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        d += (dx*dx + dy*dy) ** 0.5
    return d

def brace_section_area_mm2(profile):
    t = profile.get("type")
    w = float(profile.get("width_mm", 0))
    h = float(profile.get("height_mm", 0))
    if t == "rectangular":
        return w * h
    elif t == "triangular":
        return 0.5 * w * h
    elif t == "parabolic":
        return 0.66 * w * h
    return w * h * 0.5

def estimate_mass_grams(length_mm, area_mm2, density_kg_m3):
    volume_m3 = (area_mm2 * length_mm) / 1e9
    return volume_m3 * density_kg_m3 * 1000.0

def run(inp_path, out_dir):
    with open(inp_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    model = cfg.get("model_name", "Bracing")
    braces = cfg.get("braces", [])
    report = {
        "model_name": model,
        "units": cfg.get("units", "mm"),
        "top_radius_mm": cfg.get("top_radius_mm"),
        "back_radius_mm": cfg.get("back_radius_mm"),
        "braces": []
    }
    total_mass = 0.0
    total_glue_extra = 0.0
    for b in braces:
        pts = b.get("path", {}).get("points_mm", [])
        L = length_of_polyline(pts)
        area = brace_section_area_mm2(b.get("profile", {}))
        dens = float(b.get("density_kg_m3", 420))
        mass_g = estimate_mass_grams(L, area, dens)
        glue_extra = float(b.get("glue_area_extra_mm", 0.0)) * L
        report["braces"].append({
            "name": b.get("name", "brace"),
            "length_mm": round(L, 2),
            "section_area_mm2": round(area, 2),
            "mass_g": round(mass_g, 2),
            "glue_edge_extra_mm2": round(glue_extra, 2)
        })
        total_mass += mass_g
        total_glue_extra += glue_extra

    report["totals"] = {
        "mass_g": round(total_mass, 2),
        "glue_edge_extra_mm2": round(total_glue_extra, 2)
    }

    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, f"{model}_bracing_report.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    qpath = os.path.join(out_dir, "queue.json")
    q = []
    if os.path.exists(qpath):
        try:
            with open(qpath, "r", encoding="utf-8") as qf:
                q = json.load(qf)
        except Exception:
            q = []
    q.append({"type": "bracing_report", "model": model, "file": os.path.basename(out_json)})
    with open(qpath, "w", encoding="utf-8") as qf:
        json.dump(q, qf, indent=2)

    print("OK", out_json)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()
    run(args.config, args.out_dir)
