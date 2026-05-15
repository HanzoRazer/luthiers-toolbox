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
    data = {"spindle_rpm": "0"}  # Explicit zero to test no-spindle path
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
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


# =============================================================================
# Spindle Command Emission (Sprint A)
# =============================================================================

def test_spindle_default_rpm_emits_m3_s18000(client):
    """Default spindle_rpm=18000 emits M3 S18000 after safe-Z, before first cut."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    assert data["ok"] is True
    gcode = data["gcode"]["text"]
    assert "M3 S18000" in gcode
    # Verify ordering: M3 S18000 appears after G0 Z (safe-Z) and before first G1
    lines = gcode.split("\n")
    safe_z_idx = next((i for i, l in enumerate(lines) if l.startswith("G0 Z")), -1)
    spindle_idx = next((i for i, l in enumerate(lines) if "M3 S18000" in l), -1)
    first_g1_idx = next((i for i, l in enumerate(lines) if l.startswith("G1")), -1)
    assert safe_z_idx < spindle_idx < first_g1_idx, "M3 S18000 must be after safe-Z and before first G1"


def test_spindle_default_dwell_emits_g4_p2(client):
    """Default spindle_dwell_ms=2000 emits G4 P2.0 after M3 S18000."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    gcode = data["gcode"]["text"]
    assert "G4 P2.0" in gcode
    # Verify ordering: G4 appears after M3
    lines = gcode.split("\n")
    spindle_idx = next((i for i, l in enumerate(lines) if "M3 S18000" in l), -1)
    dwell_idx = next((i for i, l in enumerate(lines) if "G4 P2.0" in l), -1)
    assert spindle_idx < dwell_idx, "G4 dwell must be after M3 spindle on"


def test_spindle_zero_rpm_emits_no_spindle_commands(client):
    """spindle_rpm=0 emits no S, no M3, no G4, no M5 — matches pre-sprint output."""
    import re
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"spindle_rpm": "0"}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    result = response.json()
    assert result["ok"] is True
    gcode = result["gcode"]["text"]
    # No spindle commands at all
    assert "M3 S" not in gcode  # No spindle start command
    assert "M5" not in gcode    # No spindle stop
    assert not re.search(r'\bS\d+', gcode), "Should not contain S<digits> spindle speed"
    assert "G4 P" not in gcode  # No dwell
    # Still has standard structure
    assert "G21" in gcode
    assert "G90" in gcode
    assert "M30" in gcode


def test_spindle_custom_rpm_12000(client):
    """Custom spindle_rpm=12000 emits M3 S12000."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"spindle_rpm": "12000"}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    result = response.json()
    assert result["ok"] is True
    gcode = result["gcode"]["text"]
    assert "M3 S12000" in gcode
    assert "M3 S18000" not in gcode  # Not the default


def test_spindle_zero_dwell_emits_no_g4(client):
    """spindle_dwell_ms=0 emits M3 S but no G4."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    data = {"spindle_rpm": "18000", "spindle_dwell_ms": "0"}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files, data=data)
    result = response.json()
    assert result["ok"] is True
    gcode = result["gcode"]["text"]
    assert "M3 S18000" in gcode
    assert "G4 P" not in gcode


def test_spindle_m5_before_g0_home_and_m30(client):
    """M5 spindle off appears before G0 X0 Y0 and M30."""
    files = {"file": ("test.dxf", io.BytesIO(_make_simple_dxf()), "application/dxf")}
    response = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", files=files)
    data = response.json()
    gcode = data["gcode"]["text"]
    lines = gcode.split("\n")
    m5_idx = next((i for i, l in enumerate(lines) if "M5" in l), -1)
    home_idx = next((i for i, l in enumerate(lines) if "G0 X0 Y0" in l), -1)
    m30_idx = next((i for i, l in enumerate(lines) if "M30" in l), -1)
    assert m5_idx > 0, "M5 must be present"
    assert m5_idx < home_idx < m30_idx, "Order must be: M5, then G0 X0 Y0, then M30"
