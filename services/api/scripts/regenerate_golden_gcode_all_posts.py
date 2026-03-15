#!/usr/bin/env python3
"""
Regenerate ToolBox MVP golden gcode snapshots for ALL post processors.

Usage:
  cd services/api
  python scripts/regenerate_golden_gcode_all_posts.py

This script rewrites golden files for each supported post processor:
  tests/golden/mvp_rect_with_island__grbl.nc
  tests/golden/mvp_rect_with_island__mach4.nc
  tests/golden/mvp_rect_with_island__linuxcnc.nc

Commit the updated golden files only when you intentionally accept CAM output changes.
"""

from pathlib import Path
import re
import sys


# Post processors to generate fixtures for (must match post_profiles.json)
POST_PROCESSORS = ["GRBL", "Mach4", "LinuxCNC"]


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


def generate_for_post(client, req_base: dict, post_id: str, golden_dir: Path) -> Path:
    """Generate golden fixture for a specific post processor."""
    req = req_base.copy()
    req["post_id"] = post_id
    req["units"] = "mm"

    print(f"  Generating G-code for {post_id}...")
    gcode_resp = client.post("/api/cam/pocket/adaptive/gcode", json=req)
    if gcode_resp.status_code != 200:
        print(f"    ERROR: gcode failed: {gcode_resp.text}")
        return None

    normalized = _normalize_gcode(gcode_resp.text)

    golden_path = golden_dir / f"mvp_rect_with_island__{post_id.lower()}.nc"
    golden_path.write_text(normalized, encoding="utf-8")
    print(f"    Wrote: {golden_path.name} ({len(normalized.splitlines())} lines)")
    return golden_path


def main() -> None:
    # Add parent to path for imports
    repo = Path(__file__).resolve().parents[1]  # services/api
    sys.path.insert(0, str(repo))

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.adaptive import router as adaptive_router

    testdata = repo / "tests" / "testdata" / "mvp_rect_with_island.dxf"
    golden_dir = repo / "tests" / "golden"
    golden_dir.mkdir(parents=True, exist_ok=True)

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

    req_base = plan_resp.json()["request"]

    print(f"\nStep 2: Generating golden fixtures for {len(POST_PROCESSORS)} post processors...")
    generated = []
    for post_id in POST_PROCESSORS:
        path = generate_for_post(client, req_base, post_id, golden_dir)
        if path:
            generated.append(path)

    print(f"\nGenerated {len(generated)} golden fixtures:")
    for path in generated:
        rel = path.relative_to(repo.parent.parent)
        print(f"  git add {rel}")

    print("\nCommit these files to lock the MVP path for all post processors.")


if __name__ == "__main__":
    main()
