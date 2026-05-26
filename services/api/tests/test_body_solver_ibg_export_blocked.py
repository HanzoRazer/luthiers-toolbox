"""API contract: IBG DXF export fail-closed returns 422 (DO 80 Phase D)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    from app.main import app

    return TestClient(app)


@pytest.fixture
def minimal_dxf_bytes():
    pytest.importorskip("ezdxf")
    import ezdxf

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "CONTOUR"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        path = tmp.name

    try:
        with open(path, "rb") as f:
            yield f.read()
    finally:
        os.unlink(path)


def test_solve_from_dxf_return_dxf_blocked_422(api_client, minimal_dxf_bytes):
    """return_dxf must not 500 when export is governance-blocked."""
    response = api_client.post(
        "/api/body/solve-from-dxf",
        files={"dxf_file": ("partial.dxf", minimal_dxf_bytes, "application/dxf")},
        data={
            "instrument_spec": "dreadnought",
            "consolidate": "false",
            "options": json.dumps({"return_dxf": True}),
        },
    )
    assert response.status_code == 422
    body = response.json()
    detail = body.get("detail", body)
    if isinstance(detail, dict):
        assert detail.get("error") == "ibg_dxf_export_blocked"
        assert detail.get("r1_required") is True
