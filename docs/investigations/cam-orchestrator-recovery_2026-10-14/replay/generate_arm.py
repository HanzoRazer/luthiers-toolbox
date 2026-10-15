#!/usr/bin/env python3
"""Generate the neck program for ONE replay arm, offline.

Run with ``-I`` from outside the tree, with the tree's ``services/api`` as the
only import root::

    python -I generate_arm.py --tree <extracted>/services/api --arm NAME --out-dir DIR

The arm is whatever ``app/cam/neck/orchestrator.py`` the tree contains. This
script changes nothing in the tree. If the orchestrator cannot be constructed
or run, the failure is the result: it is written to ``<arm>.json`` and the
script exits 4. It never retries with different inputs.

Fixture: the same one the LTB-REMEDIATE-P1 motion test uses --
``_build_pipeline_config(NeckConfigIn())`` with all four operations enabled.
The program's ``( Generated: ... UTC )`` comment is the only nondeterministic
line; it is replaced with a fixed marker before hashing, and that
normalisation is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

_GENERATED = re.compile(r"^\( Generated: .* UTC \)$", re.M)
_LITERAL_25 = re.compile(r"(?<![\d.])25\.0(?!\d)")


def _static_scan(tree: Path) -> dict:
    """Count 25.0 literals and safe/retract assignments in the neck emitters."""
    out = {}
    for name in ("truss_rod_channel.py", "profile_carving.py", "fret_slots.py", "orchestrator.py"):
        path = tree / "app" / "cam" / "neck" / name
        text = path.read_text(encoding="utf-8")
        out[name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "literal_25_0": len(_LITERAL_25.findall(text)),
            "safe_z_assignments": re.findall(r"self\.safe_z_mm\s*=\s*([^\n#]+)", text),
            "retract_z_assignments": re.findall(r"self\.retract_z_mm\s*=\s*([^\n#]+)", text),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    tree = args.tree.resolve()
    sys.path.insert(0, str(tree))
    record: dict = {"arm": args.arm, "tree": str(tree), "static": _static_scan(tree)}

    try:
        from app.cam.neck.orchestrator import NeckPipeline
        from app.routers.cam.cam_workspace_router import NeckConfigIn, _build_pipeline_config

        import app.cam.neck.orchestrator as orch_mod
        record["orchestrator_file"] = str(Path(orch_mod.__file__).relative_to(tree))
        pipeline = NeckPipeline(_build_pipeline_config(NeckConfigIn()))
        program = pipeline.generate(
            include_truss_rod=True,
            include_profile_rough=True,
            include_profile_finish=True,
            include_fret_slots=True,
        ).get_gcode()
    except Exception as exc:  # the failure IS the evidence for this arm
        tb = traceback.extract_tb(exc.__traceback__)
        last = tb[-1] if tb else None
        record.update({
            "status": "NOT_RUNNABLE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "raised_at": f"{Path(last.filename).name}:{last.lineno}" if last else None,
            "raised_in": last.line if last else None,
        })
        (args.out_dir / f"{args.arm}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return 4

    normalised, n = _GENERATED.subn("( Generated: <normalised> UTC )", program)
    gcode_path = args.out_dir / f"{args.arm}.nc"
    gcode_path.write_text(normalised + "\n", encoding="utf-8", newline="\n")
    record.update({
        "status": "GENERATED",
        "generated_lines_normalised": n,
        "gcode_file": gcode_path.name,
        "gcode_sha256": hashlib.sha256((normalised + "\n").encode("utf-8")).hexdigest(),
        "machine_safe_z_mm": getattr(getattr(pipeline, "machine", None), "safe_z_mm", None),
        "generator_safe_z_mm": {
            "truss_rod": pipeline.truss_rod_gen.safe_z_mm,
            "profile": pipeline.profile_gen.safe_z_mm,
            "fret_slots": pipeline.fret_slot_gen.safe_z_mm,
        },
        "generator_retract_z_mm": {
            "truss_rod": pipeline.truss_rod_gen.retract_z_mm,
            "profile": pipeline.profile_gen.retract_z_mm,
            "fret_slots": pipeline.fret_slot_gen.retract_z_mm,
        },
    })
    (args.out_dir / f"{args.arm}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
