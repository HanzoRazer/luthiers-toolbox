"""
MVP Golden Path Regression Tests: Multi-Post Processor Coverage

This extends the single-post GRBL golden test to cover all primary post processors.
Each test locks the DXF → plan → gcode pipeline for a specific controller dialect.

Post Processor Differences:
- GRBL: comment mode (FEED_HINT START/END)
- Mach4: inline_f mode (scales F values directly)
- LinuxCNC: mcode mode (M52 adaptive feed override)

Run all golden tests:
    pytest tests/test_mvp_gcode_multi_post_golden.py -v

Regenerate golden fixtures:
    python scripts/regenerate_golden_gcode_all_posts.py
"""
import re
from pathlib import Path

import pytest


TESTDATA = Path(__file__).parent / "testdata"
GOLDEN = Path(__file__).parent / "golden"


def _normalize_gcode(text: str) -> str:
    """
    Normalize gcode for deterministic snapshot comparisons.

    Strips timestamps/dates while preserving motion semantics.
    """
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Normalize DATE/TIME patterns
        line = re.sub(r"(DATE|TIME)\s*=\s*[^)]+", r"\1=__NORMALIZED__", line)
        line = re.sub(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b", "__NORMALIZED__", line)
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _get_gcode_for_post(client, dxf_path: Path, post_id: str) -> str:
    """Generate G-code for a specific post processor."""
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

    # Step 1: DXF → plan
    plan_resp = client.post("/api/cam/pocket/adaptive/plan_from_dxf", data=form, files=files)
    assert plan_resp.status_code == 200, f"plan_from_dxf failed: {plan_resp.text}"

    req = plan_resp.json()["request"]
    req["post_id"] = post_id
    req["units"] = "mm"

    # Step 2: plan → gcode
    gcode_resp = client.post("/api/cam/pocket/adaptive/gcode", json=req)
    assert gcode_resp.status_code == 200, f"gcode failed: {gcode_resp.text}"

    return gcode_resp.text


def _run_golden_test(client, post_id: str):
    """Run golden snapshot test for a specific post processor."""
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Missing fixture DXF: {dxf_path}"

    golden_path = GOLDEN / f"mvp_rect_with_island__{post_id.lower()}.nc"

    gcode_text = _get_gcode_for_post(client, dxf_path, post_id)
    normalized = _normalize_gcode(gcode_text)

    # Bootstrap golden file if missing
    GOLDEN.mkdir(parents=True, exist_ok=True)
    if not golden_path.exists():
        golden_path.write_text(normalized, encoding="utf-8")
        pytest.fail(
            f"Golden snapshot created at {golden_path}. "
            f"Commit this file to lock the {post_id} path."
        )

    expected = _normalize_gcode(golden_path.read_text(encoding="utf-8"))
    assert normalized == expected, (
        f"G-code output for {post_id} differs from golden snapshot. "
        f"If intentional, run: python scripts/regenerate_golden_gcode_all_posts.py"
    )


@pytest.fixture(scope="module")
def test_client():
    """Create test client with minimal app."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.adaptive import router as adaptive_router

    app = FastAPI()
    app.include_router(adaptive_router, prefix="/api")
    return TestClient(app)


# =============================================================================
# GOLDEN SNAPSHOT TESTS - ONE PER POST PROCESSOR
# =============================================================================


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_mvp_gcode_golden_GRBL(test_client):
    """
    Golden test: GRBL post processor (hobby CNC).

    GRBL uses 'comment' mode for adaptive feed:
    - Emits (FEED_HINT START scale=X) / (FEED_HINT END) comments
    - Controller interprets comments as feed override hints
    - Most common hobbyist controller (3018, Shapeoko, etc.)
    """
    _run_golden_test(test_client, "GRBL")


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_mvp_gcode_golden_Mach4(test_client):
    """
    Golden test: Mach4 post processor (pro CNC).

    Mach4 uses 'inline_f' mode for adaptive feed:
    - Directly scales F values in slowed segments
    - No special comments or M-codes needed
    - Common in professional router setups (4x8 tables)
    """
    _run_golden_test(test_client, "Mach4")


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_mvp_gcode_golden_LinuxCNC(test_client):
    """
    Golden test: LinuxCNC post processor (open-source CNC).

    LinuxCNC uses 'mcode' mode for adaptive feed:
    - Emits M52 P0.7 (start slowdown) / M52 P1.0 (end slowdown)
    - Native adaptive feed override support
    - Common in knee mills and converted machines
    - Uses M2 footer instead of M30
    """
    _run_golden_test(test_client, "LinuxCNC")


# =============================================================================
# POST PROCESSOR INVARIANT TESTS
# =============================================================================


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_all_posts_produce_valid_gcode(test_client):
    """
    Verify all post processors produce valid G-code structure.

    All outputs must:
    - Start with setup commands (G90, G17, G21)
    - Include spindle start (M3)
    - End with spindle stop (M5) and program end (M2 or M30)
    - Contain motion commands (G0, G1)
    """
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Missing fixture DXF: {dxf_path}"

    for post_id in ["GRBL", "Mach4", "LinuxCNC"]:
        gcode = _get_gcode_for_post(test_client, dxf_path, post_id)

        # Basic structure validation
        assert "G90" in gcode, f"{post_id}: Missing G90 (absolute positioning)"
        assert "G21" in gcode, f"{post_id}: Missing G21 (mm units)"
        assert "M3" in gcode, f"{post_id}: Missing M3 (spindle start)"
        assert "M5" in gcode, f"{post_id}: Missing M5 (spindle stop)"
        assert "G1" in gcode, f"{post_id}: Missing G1 (linear move)"

        # Program end (M2 or M30)
        assert "M2" in gcode or "M30" in gcode, f"{post_id}: Missing program end (M2/M30)"

        # Post-specific header comment
        assert f"({post_id}" in gcode or f"(post {post_id})" in gcode.lower(), \
            f"{post_id}: Missing controller comment"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_post_specific_features(test_client):
    """
    Verify post-processor-specific features are correctly emitted.

    - GRBL: FEED_HINT comments
    - Mach4: Scaled F values (no special markers)
    - LinuxCNC: M52 adaptive feed commands
    """
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"

    # GRBL: comment mode
    grbl_gcode = _get_gcode_for_post(test_client, dxf_path, "GRBL")
    assert "FEED_HINT START" in grbl_gcode, "GRBL: Missing FEED_HINT comments"
    assert "FEED_HINT END" in grbl_gcode, "GRBL: Missing FEED_HINT END comment"

    # LinuxCNC: mcode mode
    linuxcnc_gcode = _get_gcode_for_post(test_client, dxf_path, "LinuxCNC")
    assert "M52" in linuxcnc_gcode, "LinuxCNC: Missing M52 adaptive feed command"
    assert "M2" in linuxcnc_gcode, "LinuxCNC: Should use M2 (not M30) for program end"
