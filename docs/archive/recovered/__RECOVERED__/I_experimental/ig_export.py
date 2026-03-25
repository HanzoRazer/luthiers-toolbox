"""
CLI command: ig_export cam-profile-op

Exports ProfileOpPlan + GRBL G-code for truss union profile.

Target: instrument_geometry/cli/ig_export.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

from instrument_geometry.api import keys as K
from instrument_geometry.exports.paths import ExportPaths
from instrument_geometry.exports.cam_export import export_json, export_text
from instrument_geometry.golden.case_loader import load_case_geom  # adjust to your actual loader


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("ig_export")
    sub = p.add_subparsers(dest="cmd", required=True)

    cam = sub.add_parser("cam-profile-op", help="Export ProfileOpPlan + GRBL gcode for truss union profile.")
    cam.add_argument("--case", required=True)
    cam.add_argument("--out", default="exports/cam", help="Output directory")
    cam.add_argument("--tool-mm", type=float, default=6.0)
    cam.add_argument("--material-id", default="hardwood")
    cam.add_argument("--hardness", default="med")
    cam.add_argument("--datum", default="nut")
    cam.add_argument("--rotate", default="align:+X")
    cam.add_argument("--finish-allowance", type=float, default=0.25)
    cam.add_argument("--entry", default="helix_first_ramp_rest",
                     help="plunge|ramp|helix|helix_first_ramp_rest")
    cam.add_argument("--helix-turns", type=float, default=1.0)
    cam.add_argument("--helix-seg", type=int, default=36)
    cam.add_argument("--helix-margin", type=float, default=1.0)
    cam.add_argument("--helix-start", type=float, default=0.5)
    cam.add_argument("--helix-safe-margin", type=float, default=1.0)
    cam.add_argument("--ramp-len", type=float, default=12.0)
    cam.add_argument("--ramp-scale", type=float, default=0.7)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    geom, case_id = load_case_geom(args.case)  # expected: returns InstrumentGeometry instance
    out = ExportPaths(root=Path(args.out)).ensure()

    # 1) OpPlan JSON
    opplan = geom.api.get(
        K.TRUSS_UNION_PROFILE_OPPLAN,
        tool_diameter_mm=float(args.tool_mm),
        material_id=str(args.material_id),
        hardness=str(args.hardness),
        finish_allowance_mm=float(args.finish_allowance),
        datum=str(args.datum),
        rotate=str(args.rotate),
    )
    op_id = opplan.get("op_id", "truss_union_profile_opplan_v1")
    opplan_path = out.opplan_path(case_id, op_id)
    export_json(opplan, opplan_path)

    # 2) GRBL G-code
    gcode = geom.api.get(
        K.TRUSS_UNION_PROFILE_GCODE_GRBL,
        tool_diameter_mm=float(args.tool_mm),
        material_id=str(args.material_id),
        hardness=str(args.hardness),
        finish_allowance_mm=float(args.finish_allowance),
        datum=str(args.datum),
        rotate=str(args.rotate),
        entry_mode=str(args.entry),
        helix_turns=float(args.helix_turns),
        helix_segments_per_turn=int(args.helix_seg),
        helix_margin_mm=float(args.helix_margin),
        helix_start_above_stock_mm=float(args.helix_start),
        helix_safe_margin_mm=float(args.helix_safe_margin),
        ramp_length_mm=float(args.ramp_len),
        ramp_feed_scale=float(args.ramp_scale),
    )
    gcode_path = out.gcode_path(case_id, op_id, post="grbl")
    export_text(gcode, gcode_path)

    print(f"Wrote opplan: {opplan_path}")
    print(f"Wrote gcode: {gcode_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
