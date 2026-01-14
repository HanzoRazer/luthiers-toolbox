#!/usr/bin/env python3
"""
Regenerate the ToolBox MVP golden gcode snapshot.

Usage:
  cd services/api
  python scripts/regenerate_mvp_golden_gcode.py

This script intentionally rewrites:
  tests/golden/mvp_rect_with_island__grbl.nc

Commit the updated golden file only when you intentionally accept CAM output changes.
"""

from pathlib import Path
import re
import sys


def _normalize_gcode(text: str) -> str:
    """Normalize gcode for deterministic snapshot comparisons."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"(DATE|TIME)\s*=\s*[^)]+", r"\1=__NORMALIZED__", line)
        line = re.sub(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b", "__NORMALIZED__", line)
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    # Add parent to path for imports
    repo = Path(__file__).resolve().parents[1]  # services/api
    sys.path.insert(0, str(repo))

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.adaptive_router import router as adaptive_router

    testdata = repo / "tests" / "testdata" / "mvp_rect_with_island.dxf"
    golden = repo / "tests" / "golden" / "mvp_rect_with_island__grbl.nc"
    golden.parent.mkdir(parents=True, exist_ok=True)

    if not testdata.exists():
        print(f"ERROR: Missing fixture DXF: {testdata}")
        sys.exit(1)

    app = FastAPI()
    app.include_router(adaptive_router, prefix="/api")
    client = TestClient(app)

    form = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "strategy": "Spiral",
        "feed_xy": "1200",
        "feed_z": "300",
        "rapid": "3000",
        "safe_z": "5.0",
        "z_rough": "-3.0",
        "layer_name": "GEOMETRY",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }

    files = {"file": (testdata.name, testdata.read_bytes(), "application/dxf")}

    print("Step 1: Calling plan_from_dxf...")
    plan_resp = client.post("/api/cam/pocket/adaptive/plan_from_dxf", data=form, files=files)
    if plan_resp.status_code != 200:
        print(f"ERROR: plan_from_dxf failed: {plan_resp.text}")
        sys.exit(1)

    req = plan_resp.json()["request"]
    req["post_id"] = "GRBL"
    req["units"] = "mm"

    print("Step 2: Calling gcode endpoint...")
    gcode_resp = client.post("/api/cam/pocket/adaptive/gcode", json=req)
    if gcode_resp.status_code != 200:
        print(f"ERROR: gcode failed: {gcode_resp.text}")
        sys.exit(1)

    normalized = _normalize_gcode(gcode_resp.text)

    golden.write_text(normalized, encoding="utf-8")
    print(f"Wrote golden snapshot: {golden}")
    print(f"Lines: {len(normalized.splitlines())}")
    print("\nCommit this file to lock the MVP path:")
    print(f"  git add {golden.relative_to(repo.parent.parent)}")


if __name__ == "__main__":
    main()
