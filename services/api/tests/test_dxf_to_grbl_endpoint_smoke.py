"""Smoke tests for DXF-to-GRBL MVP endpoint (wired to real pipeline)."""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def _make_simple_dxf() -> bytes:
    """Create a valid DXF with a closed square polyline using ezdxf."""
    import ezdxf
    import tempfile
    import os
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    # 50mm square on layer "0"
    points = [(0, 0), (50, 0), (50, 50), (0, 50)]
    msp.add_lwpolyline(points, close=True)
    # Save to temp file and read back as bytes (ezdxf writes text, not binary)
    fd, path = tempfile.mkstemp(suffix=".dxf")
    try:
        os.close(fd)
        doc.saveas(path)
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_dxf_to_grbl_endpoint_exists(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl endpoint exists."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    assert response.status_code != 404


# =============================================================================
# Valid Export Cases
# =============================================================================

def test_dxf_to_grbl_returns_200(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns 200 with valid DXF."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    assert response.status_code == 200


def test_dxf_to_grbl_returns_ok_true(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns ok=True with valid DXF."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert data["ok"] is True


def test_dxf_to_grbl_returns_run_id(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns run_id."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert data["run_id"].startswith("RUN-DXF-")


def test_dxf_to_grbl_returns_gcode(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns G-code."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert "gcode" in data
    assert data["gcode"] is not None
    assert "inline" in data["gcode"]
    assert "text" in data["gcode"]


def test_dxf_to_grbl_gcode_contains_markers(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl G-code contains standard markers."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    gcode = data["gcode"]["text"]
    assert "G21" in gcode  # mm mode
    assert "G90" in gcode  # absolute mode
    assert "M30" in gcode  # end program


def test_dxf_to_grbl_returns_decision(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns decision."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert "decision" in data
    assert "risk_level" in data["decision"]


def test_dxf_to_grbl_returns_attachments(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns attachments list."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert "attachments" in data
    assert isinstance(data["attachments"], list)
    # Should have at least dxf_input attachment
    kinds = [a["kind"] for a in data["attachments"]]
    assert "dxf_input" in kinds


def test_dxf_to_grbl_returns_hashes(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl returns hashes."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert "hashes" in data
    assert "dxf_input" in data["hashes"]


# =============================================================================
# Custom Parameters
# =============================================================================

def test_dxf_to_grbl_accepts_tool_diameter(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl accepts tool_d parameter."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"tool_d": "3.175"}  # 1/8 inch
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True


def test_dxf_to_grbl_accepts_feeds(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl accepts feed parameters."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {
        "feed_xy": "800",
        "feed_z": "200",
        "rapid": "2500",
    }
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    assert response.status_code == 200


def test_dxf_to_grbl_accepts_stepover(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl accepts stepover parameter."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"stepover": "0.35"}  # 35%
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    assert response.status_code == 200


def test_dxf_to_grbl_accepts_stepdown(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl accepts stepdown parameter."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"stepdown": "1.5"}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    assert response.status_code == 200


def test_dxf_to_grbl_accepts_strategy(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl accepts strategy parameter."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"strategy": "Spiral"}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    assert response.status_code == 200


# =============================================================================
# Error Cases
# =============================================================================

def test_dxf_to_grbl_requires_file(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl requires file upload."""
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl")
    assert response.status_code == 422


def test_dxf_to_grbl_handles_invalid_dxf(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl handles invalid DXF gracefully."""
    files = {"file": ("bad.dxf", io.BytesIO(b"not a valid dxf file"), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    # Should return 200 with ok=False, not crash
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "message" in data


def test_dxf_to_grbl_handles_empty_dxf(client):
    """POST /api/rmos/wrap/mvp/dxf-to-grbl handles empty DXF (no polylines)."""
    # Create a valid DXF with no entities using ezdxf
    import ezdxf
    import tempfile
    import os
    doc = ezdxf.new(dxfversion="R2010")
    # Don't add any entities - empty modelspace
    fd, path = tempfile.mkstemp(suffix=".dxf")
    try:
        os.close(fd)
        doc.saveas(path)
        with open(path, "rb") as f:
            empty_dxf = f.read()
    finally:
        os.unlink(path)
    files = {"file": ("empty.dxf", io.BytesIO(empty_dxf), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "no closed polylines" in data.get("message", "").lower()
