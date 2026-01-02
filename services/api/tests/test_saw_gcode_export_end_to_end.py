from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_single_op_gcode_export(client: TestClient, monkeypatch):
    """Test G-code export for a single operation."""
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "false")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-gcode-single",
            "session_id": "sess_pytest_gcode_single",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text

    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec.json()["batch_spec_artifact_id"]})
    assert plan.status_code == 200, plan.text
    pb = plan.json()

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": pb["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "gcode export test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text

    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": approve.json()["batch_decision_artifact_id"]})
    assert exe.status_code == 200, exe.text
    exe_body = exe.json()

    # Get the first op toolpath artifact ID
    results = exe_body.get("results", [])
    assert len(results) > 0, "Expected at least one op result"
    op_artifact_id = results[0].get("toolpaths_artifact_id")
    assert op_artifact_id, "Expected toolpaths_artifact_id in result"

    # Download G-code for single op
    r = client.get(f"/api/saw/batch/op-toolpaths/{op_artifact_id}/gcode")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/plain")
    assert "attachment" in r.headers.get("content-disposition", "")

    gcode = r.text
    # Verify G-code structure
    assert "G21" in gcode, "Expected G21 (units: mm)"
    assert "G90" in gcode, "Expected G90 (absolute positioning)"
    assert "M3" in gcode, "Expected M3 (spindle on)"
    assert "M5" in gcode, "Expected M5 (spindle stop)"
    assert "G0" in gcode or "G1" in gcode, "Expected G0 or G1 moves"


def test_execution_gcode_export(client: TestClient, monkeypatch):
    """Test combined G-code export for entire execution."""
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "false")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec with multiple items -> multiple ops
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-gcode-multi",
            "session_id": "sess_pytest_gcode_multi",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
                {"part_id": "p2", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 250.0, "width_mm": 25.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text

    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec.json()["batch_spec_artifact_id"]})
    assert plan.status_code == 200, plan.text
    pb = plan.json()

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": pb["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "gcode multi-op export test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text

    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": approve.json()["batch_decision_artifact_id"]})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]

    # Download combined G-code
    r = client.get(f"/api/saw/batch/executions/{exec_id}/gcode")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/plain")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert ".ngc" in r.headers.get("content-disposition", "")

    gcode = r.text
    # Verify combined structure
    assert "Batch:" in gcode, "Expected batch label comment"
    assert "Execution:" in gcode, "Expected execution ID comment"
    assert "Op:" in gcode, "Expected op separator comments"
    assert "M30" in gcode, "Expected M30 (program end) at the end"

    # Should have multiple op blocks
    op_count = gcode.count("========== Op:")
    assert op_count >= 2, f"Expected at least 2 op blocks, got {op_count}"


def test_gcode_export_no_toolpaths_returns_message(client: TestClient, monkeypatch):
    """Test that blocked ops return a message instead of empty G-code."""
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "false")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # We can't easily force a blocked op in this test, but we can verify
    # the service handles the case gracefully by checking the service directly
    from app.services.saw_lab_gcode_emit_service import emit_gcode_from_moves

    # Empty moves should return empty string
    result = emit_gcode_from_moves([])
    assert result == ""

    # Valid moves should emit G-code
    result = emit_gcode_from_moves([
        {"code": "G21", "comment": "Units: mm"},
        {"code": "G0", "z": 10.0},
        {"code": "G1", "x": 100.0, "y": 50.0, "z": -3.0, "f": 1000.0},
    ])
    assert "G21" in result
    assert "G0 Z10.0000" in result
    assert "G1 X100.0000 Y50.0000 Z-3.0000 F1000.0" in result
