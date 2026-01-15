"""
RMOS Operator Pack Export Tests

Ensures the operator pack ZIP is a stable, auditable artifact that:
  - Contains the 4 canonical files (input.dxf, plan.json, manifest.json, output.nc)
  - G-code bytes match the run's recorded gcode_sha256
"""
import io
import zipfile
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_zip_contains_expected_files_and_hashes_match():
    """
    Ensures RMOS operator pack is a stable, auditable artifact:
      - contains input.dxf, plan.json, manifest.json, output.nc
      - gcode bytes match the run's recorded gcode_sha256
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.rmos.mvp_wrapper import router as mvp_wrapper_router
    from app.rmos.runs_v2.exports import router as exports_router
    from app.rmos.runs_v2.hashing import sha256_of_text

    app = FastAPI()
    app.include_router(mvp_wrapper_router)
    app.include_router(exports_router)
    client = TestClient(app)

    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Test fixture not found: {dxf_path}"

    form = {
        "layer_name": "GEOMETRY",
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "strategy": "Spiral",
        "feed_xy": "1200",
        "feed_z": "300",
        "rapid": "3000",
        "safe_z": "5.0",
        "z_rough": "-3.0",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }
    files = {"file": (dxf_path.name, dxf_path.read_bytes(), "application/dxf")}

    # Create a run via the wrapper (canonical production path)
    r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=form, files=files)
    assert r.status_code == 200, r.text
    payload = r.json()
    run_id = payload.get("run_id")
    assert run_id, "Expected run_id from wrapper"

    gcode_text = payload.get("gcode", {}).get("text") or ""
    assert gcode_text, "Expected inline gcode for MVP fixture"
    expected_gcode_sha = sha256_of_text(gcode_text)

    # Download operator pack
    z = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert z.status_code == 200, z.text
    assert z.headers.get("content-type", "").startswith("application/zip")

    zf = zipfile.ZipFile(io.BytesIO(z.content))
    names = set(zf.namelist())
    assert {"input.dxf", "plan.json", "manifest.json", "output.nc"} <= names

    output_nc = zf.read("output.nc").decode("utf-8", errors="replace")
    assert sha256_of_text(output_nc) == expected_gcode_sha


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_returns_404_for_missing_run():
    """Operator pack endpoint returns 404 for non-existent run."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.rmos.runs_v2.exports import router as exports_router

    app = FastAPI()
    app.include_router(exports_router)
    client = TestClient(app)

    r = client.get("/api/rmos/runs_v2/run_nonexistent_12345/operator-pack")
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()
