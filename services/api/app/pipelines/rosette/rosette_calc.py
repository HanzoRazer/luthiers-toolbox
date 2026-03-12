"""
Rosette channel calculator — legacy pipeline math (preserved).

Computes the required channel width and depth from a rosette layer stack
(inner purfling + central band + outer purfling).  Used by the pipeline
runner; for new integrations prefer the full manufacturing planner
(``app.core.rosette_planner.generate_manufacturing_plan``).
"""
from __future__ import annotations

import json
import math
import argparse
import pathlib
from typing import Any, Dict, List


def compute(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate channel dimensions from a rosette layer-stack definition.

    Parameters
    ----------
    params : dict
        Must contain ``soundhole_diameter_mm``.
        Optional: ``exposure_mm``, ``glue_clearance_mm``, ``central_band``,
        ``inner_purfling``, ``outer_purfling``.

    Returns
    -------
    dict
        Keys: ``soundhole_diameter_mm``, ``channel_width_mm``,
        ``channel_depth_mm``, ``stack``.
    """
    Di = float(params["soundhole_diameter_mm"])
    exposure = float(params.get("exposure_mm", 0.15))
    glue = float(params.get("glue_clearance_mm", 0.08))

    central = params.get("central_band", {"width_mm": 18.0, "thickness_mm": 1.0})
    inner = params.get("inner_purfling", [])
    outer = params.get("outer_purfling", [])

    # Simple channel estimate: total stack width = inner + central + outer
    def sum_width(rows: List[Dict[str, Any]]) -> float:
        return sum(float(r.get("width_mm", 0)) for r in rows)
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

def main() -> None:
    """CLI entry point — reads JSON input, writes rosette_calc.json."""
    ap = argparse.ArgumentParser(description="Rosette channel calculator")
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
