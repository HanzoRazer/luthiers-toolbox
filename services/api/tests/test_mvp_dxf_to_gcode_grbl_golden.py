"""
MVP Golden Path Regression Test: DXF -> plan_from_dxf -> gcode (GRBL)

This is the single most important manufacturing regression gate in the repo.
It locks the ToolBox MVP golden path to a deterministic snapshot.
"""
import re
from pathlib import Path

import pytest


TESTDATA = Path(__file__).parent / "testdata"
GOLDEN = Path(__file__).parent / "golden"


def _normalize_gcode(text: str) -> str:
    """
    Normalize gcode for deterministic snapshot comparisons.

    We intentionally keep motion semantics stable while ignoring:
    - timestamps / generated dates (if present)
    - trailing whitespace
    - purely decorative comments (optional)
    """
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Normalize any embedded DATE/TIME patterns if they exist
        line = re.sub(r"(DATE|TIME)\s*=\s*[^)]+", r"\1=__NORMALIZED__", line)
        line = re.sub(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b", "__NORMALIZED__", line)

        # Keep comments (they help debugging) but normalize volatile content above
        lines.append(line)

    return "\n".join(lines).strip() + "\n"


@pytest.mark.integration
def test_mvp_dxf_to_gcode_grbl_golden_snapshot():
    """
    Locks the ToolBox MVP golden path:

      DXF -> /api/cam/pocket/adaptive/plan_from_dxf -> request.loops
          -> /api/cam/pocket/adaptive/gcode (post_id=GRBL)
          -> stable .nc output

    This is the single most important manufacturing regression gate in the repo.
    """
    # Import here to keep module import side-effects local to the test.
    # In CI, the full dependency set (ezdxf, pyclipper, etc.) must be installed.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Minimal app with only the required router to avoid unrelated startup deps.
    from app.routers.adaptive_router import router as adaptive_router

    app = FastAPI()
    app.include_router(adaptive_router, prefix="/api")
    client = TestClient(app)

    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Missing fixture DXF: {dxf_path}"

    # Golden-path parameters (keep conservative and stable)
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

    files = {"file": (dxf_path.name, dxf_path.read_bytes(), "application/dxf")}

    # Step 1: DXF -> plan (must include loops in response["request"]["loops"])
    plan_resp = client.post("/api/cam/pocket/adaptive/plan_from_dxf", data=form, files=files)
    assert plan_resp.status_code == 200, plan_resp.text
    plan = plan_resp.json()

    assert "request" in plan, "plan_from_dxf must return request payload for gcode export"
    req = plan["request"]
    assert "loops" in req and req["loops"], "plan_from_dxf must return non-empty request.loops"
    assert "tool_d" in req, "request.tool_d required for gcode export"

    # Step 2: plan request -> gcode (GRBL)
    req["post_id"] = "GRBL"
    req["units"] = "mm"

    gcode_resp = client.post("/api/cam/pocket/adaptive/gcode", json=req)
    assert gcode_resp.status_code == 200, gcode_resp.text
    gcode_text = gcode_resp.text

    normalized = _normalize_gcode(gcode_text)

    # Snapshot compare (bootstrap if missing)
    GOLDEN.mkdir(parents=True, exist_ok=True)
    golden_path = GOLDEN / "mvp_rect_with_island__grbl.nc"

    if not golden_path.exists():
        golden_path.write_text(normalized, encoding="utf-8")
        pytest.fail(
            f"Golden snapshot created at {golden_path}. "
            f"Commit this file to lock the MVP path."
        )

    expected = _normalize_gcode(golden_path.read_text(encoding="utf-8"))
    assert normalized == expected, (
        "G-code output differs from golden snapshot. "
        "If this is intentional, run: python scripts/regenerate_mvp_golden_gcode.py"
    )
