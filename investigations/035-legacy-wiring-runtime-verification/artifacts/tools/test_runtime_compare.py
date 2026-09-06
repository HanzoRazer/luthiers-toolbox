"""Utility C — test/runtime path comparison helper.

Does not build an AST platform. Reads frozen witness JSON plus a small
manual map of direct-test entrypoints and prints SAME/DIFFERENT/PARTIAL/UNKNOWN.

DIFFERENT is not synonymous with defect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "artifacts" / "census"

# Manual extraction from tests/ (frozen with candidate selection).
MANUAL_MAP = [
    {
        "specimen": "S1_CAM_SIM_FE_PATH",
        "test_entrypoint": "services/api/tests/test_simulation_endpoint_smoke.py → POST /api/cam/sim/gcode (and related /api/cam/sim/*)",
        "test_implementation": "app.routers.simulation_consolidated_router.simulate_gcode_json",
        "production_entrypoint": "POST /api/cam/simulate_gcode (FE SimLab)",
        "production_implementation_from_witness": None,  # filled from JSON
        "relation_if_fe_404": "DIFFERENT",
        "notes": "App-level tests witness /api/cam/sim/*, not the FE URL.",
    },
    {
        "specimen": "S2_SOUNDHOLE_POST_DUAL_MOUNT",
        "test_entrypoint": "services/api/tests/test_soundhole_spiral_endpoint.py → POST /api/instrument/soundhole via TestClient(app)",
        "test_implementation": "whichever handler FastAPI first-match selects (same as production if same app)",
        "production_entrypoint": "POST /api/instrument/soundhole",
        "notes": "TestClient on the real app is the same entrypoint as production HTTP. Direct facade unit tests are a second test path.",
    },
    {
        "specimen": "S3_POLYGON_OFFSET_NC_DUAL_MOUNT",
        "test_entrypoint": "services/api/tests/test_polygon_offset_endpoint_smoke.py → POST /api/cam/polygon_offset.nc",
        "test_implementation": "whichever colliding handler first-match selects",
        "production_entrypoint": "POST /api/cam/polygon_offset.nc (OffsetLabView)",
        "notes": "Same URL as FE. Relation to governed polygon_offset_nc depends on which handler wins.",
    },
    {
        "specimen": "S4_DXF_CURVEMATH_LEGACY_EXPORT",
        "test_entrypoint": "governed translate TestClient on POST /api/export/translate/dxf; legacy /exports/polyline_dxf lightly witnessed",
        "test_implementation": "app.routers.export.dxf_translate_router.translate_to_dxf (heavy tests) vs legacy_dxf_exports_router (FE)",
        "production_entrypoint": "POST /exports/polyline_dxf",
        "notes": "FE consumer is the legacy path; governed translator tests are a different entrypoint.",
    },
    {
        "specimen": "S5_FRET_SLOTS_CAM_PREVIEW",
        "test_entrypoint": "services/api/tests/test_cam_fret_slots_preview_smoke.py → POST /api/cam/fret_slots/preview",
        "test_implementation": "app.cam.routers.fret_slots_router.preview_fret_slots",
        "production_entrypoint": "POST /api/cam/fret_slots/preview",
        "notes": "Same URL. Ecosphere /api/v1/fretboard/dxf is a sibling product path, not this request.",
    },
]


def infer_relation(row: dict, witness: dict | None) -> str:
    if not witness:
        return "UNKNOWN"
    calls = witness.get("ACTUAL_CALLS") or {}
    status = (witness.get("HTTP_CLI_RESULT") or {}).get("status_code")
    specimen = row["specimen"]
    if specimen.startswith("S1"):
        expected = calls.get("expected_sim_json", 0)
        if status == 404 and expected == 0:
            return "DIFFERENT"
        if expected:
            return "PARTIAL"
        return "UNKNOWN"
    if specimen.startswith("S2"):
        geo = calls.get("expected_geometry_router", 0)
        legacy = calls.get("alternate_legacy_instrument_router", 0)
        facade_bound = calls.get("legacy_router_bound_facade", 0)
        geo_bound = calls.get("geometry_router_bound_compute", 0)
        if geo and not legacy:
            return "SAME"
        if legacy and not geo:
            return "PARTIAL"
        if facade_bound or geo_bound:
            return "PARTIAL"
        return "UNKNOWN"
    if specimen.startswith("S3"):
        gov = calls.get("expected_governed_nc", 0)
        util = calls.get("alternate_utility_n17", 0)
        if gov and not util:
            return "SAME"
        if util and not gov:
            return "DIFFERENT"
        if gov and util:
            return "UNKNOWN"
        return "UNKNOWN"
    if specimen.startswith("S4"):
        gov = calls.get("expected_governed_translate", 0)
        leg = calls.get("actual_legacy_handler", 0)
        if leg and not gov:
            return "DIFFERENT"
        if gov and not leg:
            return "SAME"
        return "UNKNOWN"
    if specimen.startswith("S5"):
        prev = calls.get("expected_preview_handler", 0)
        gen = calls.get("expected_standard_generator", 0)
        if prev and gen:
            return "SAME"
        if prev:
            return "PARTIAL"
        return "UNKNOWN"
    return "UNKNOWN"


def main() -> int:
    bundle_path = CENSUS / "WITNESS_BUNDLE.json"
    witnesses = {}
    if bundle_path.exists():
        data = json.loads(bundle_path.read_text(encoding="utf-8"))
        for r in data.get("results", []):
            witnesses[r.get("SPECIMEN")] = r
    rows = []
    for row in MANUAL_MAP:
        w = witnesses.get(row["specimen"])
        prod_impl = None
        if w:
            fired = [k for k, n in (w.get("ACTUAL_CALLS") or {}).items() if n]
            prod_impl = fired or ["NO_SPIED_IMPLEMENTATION_CALLED"]
        relation = infer_relation(row, w)
        rows.append(
            {
                "TEST_ENTRYPOINT": row["test_entrypoint"],
                "TEST_IMPLEMENTATION": row["test_implementation"],
                "PRODUCTION_ENTRYPOINT": row["production_entrypoint"],
                "PRODUCTION_IMPLEMENTATION": prod_impl,
                "RELATION": relation,
                "NOTES": row.get("notes"),
                "SPECIMEN": row["specimen"],
            }
        )
    out = CENSUS / "TEST_RUNTIME_COMPARISON.json"
    out.write_text(json.dumps({"rows": rows, "d_status_by_tool": False}, indent=2) + "\n")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
