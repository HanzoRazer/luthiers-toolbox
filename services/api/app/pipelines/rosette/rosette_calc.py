from __future__ import annotations
import json, math, argparse, pathlib

def compute(params):
    Di = float(params["soundhole_diameter_mm"])
    exposure = float(params.get("exposure_mm", 0.15))
    glue = float(params.get("glue_clearance_mm", 0.08))

    central = params.get("central_band", {"width_mm": 18.0, "thickness_mm": 1.0})
    inner = params.get("inner_purfling", [])
    outer = params.get("outer_purfling", [])

    # Simple channel estimate: total stack width = inner + central + outer
    def sum_width(rows): return sum(float(r.get("width_mm", 0)) for r in rows)
    W = sum_width(inner) + float(central["width_mm"]) + sum_width(outer) + 2*glue
    
    # Calculate max thickness (handle empty inner+outer case)
    all_layers = inner + outer
    if all_layers:
        D = max(float(central.get("thickness_mm", 1.0)), *(float(r.get("thickness_mm", 1.0)) for r in all_layers)) + exposure
    else:
        D = float(central.get("thickness_mm", 1.0)) + exposure

    return {
        "soundhole_diameter_mm": Di,
        "channel_width_mm": round(W, 3),
        "channel_depth_mm": round(D, 3),
        "stack": {
            "inner_purfling": inner, "central_band": central, "outer_purfling": outer
        }
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_in")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()

    p = json.loads(pathlib.Path(args.json_in).read_text())
    res = compute(p)

    out_dir = pathlib.Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rosette_calc.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
