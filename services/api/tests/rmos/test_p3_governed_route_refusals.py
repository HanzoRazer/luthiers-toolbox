"""Fail-closed governed routes, plus a test-only permitting branch.

The permitting fixture replaces the evaluator result. It is not autouse and
it is not qualification evidence.
"""

from __future__ import annotations

import pytest

from test_p2_neck_gcode_proof import program_records

pytestmark = pytest.mark.allow_missing_request_id

POLYGON = "/api/cam/polygon_offset_governed.nc"
POLYGON_DRAFT = "/api/cam/polygon_offset.nc"
EXPORT = "/api/geometry/export_gcode_governed"
EXPORT_DRAFT = "/api/geometry/export_gcode"
SQUARE = {
    "polygon": [[0, 0], [60, 0], [60, 40], [0, 40], [0, 0]],
    "tool_dia": 6.0,
    "stepover": 0.4,
}
SIM_OK = {"gcode": "G1 X1\n", "simulation_passed": True, "simulation_hash": "abc"}
OVERRIDE = {
    "gcode": "G1 X1\n",
    "simulation_override": True,
    "simulation_override_reason": "known-good program",
}

PROBES = [
    ("/api/probe/boss/gcode/download_governed", "app.routers.probe.boss_router", "generate_boss_probe"),
    ("/api/probe/corner/gcode/download_governed", "app.routers.probe.corner_router", "generate_corner_probe"),
    ("/api/probe/pocket/gcode/download_governed", "app.routers.probe.pocket_router", "generate_pocket_probe"),
    ("/api/probe/surface_z/gcode/download_governed", "app.routers.probe.surface_z_router", "generate_surface_z_probe"),
    ("/api/probe/vise_square/gcode/download_governed", "app.routers.probe.vise_square_router", "generate_vise_square_probe"),
]


class _MemoryStore:
    def __init__(self) -> None:
        self.saved: list = []

    def put(self, artifact):
        self.saved.append(artifact)
        return artifact


@pytest.fixture
def memory_store(monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr("app.rmos.runs_v2.store._get_default_store", lambda: store)
    return store


@pytest.fixture
def p3_test_only_permitting_evaluator(monkeypatch):
    """Test-only. Not qualification evidence. Restored by monkeypatch."""

    def compute(*, tool_id, req, context=None):
        return {
            "tool_id": tool_id,
            "risk_level": "GREEN",
            "warnings": ["p3-test-only-not-qualification"],
            "score": 1,
        }

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal",
        compute,
    )


def _records(response) -> list[str]:
    return program_records(response.headers.get("content-type", ""), response.content)


def _refuse(response):
    disposition = response.headers.get("content-disposition") or ""
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "SAFETY_BLOCKED"
    assert _records(response) == []
    assert "attachment" not in disposition.lower()
    assert response.headers.get("X-GCode-SHA256") is None


def test_polygon_default_authority_refuses(client, memory_store):
    response = client.post(POLYGON, json=SQUARE)
    _refuse(response)
    assert len(memory_store.saved) == 1
    artifact = memory_store.saved[0]
    assert artifact.status == "BLOCKED"
    assert artifact.hashes.gcode_sha256 is None


def test_polygon_generator_is_not_called(client, monkeypatch):
    import app.routers.polygon_offset_router as module

    def forbidden(req):
        raise AssertionError("generator ran")

    monkeypatch.setattr(module, "generate_polygon_offset_nc_program", forbidden)
    response = client.post(POLYGON, json=SQUARE)
    _refuse(response)


def test_polygon_permitting_fixture_preserves_the_program(
    client, memory_store, p3_test_only_permitting_evaluator
):
    pytest.importorskip("pyclipper")
    response = client.post(POLYGON, json=SQUARE)
    assert response.status_code == 200
    assert _records(response)
    artifact = memory_store.saved[0]
    assert artifact.decision.risk_level == "GREEN"
    assert artifact.decision.warnings == ["p3-test-only-not-qualification"]
    assert artifact.hashes.gcode_sha256
    assert len(memory_store.saved) == 1


def test_polygon_draft_sibling_still_emits(client):
    """Outside P-3 containment. The draft route is not fail-closed by this order."""
    pytest.importorskip("pyclipper")
    response = client.post(POLYGON_DRAFT, json=SQUARE)
    assert response.status_code == 200
    assert response.headers.get("X-ToolBox-Lane") == "draft"
    assert _records(response)


def test_functional_polygon_assertion_fails_without_the_fixture(client):
    response = client.post(POLYGON, json=SQUARE)

    def functional_assertion():
        assert response.status_code == 200
        assert "G21" in response.text

    with pytest.raises(AssertionError):
        functional_assertion()
    assert response.status_code == 409


def test_simulation_pass_cannot_bypass_blocked_authority(client, monkeypatch):
    import importlib

    module = importlib.import_module("app.routers.geometry.export_router")
    monkeypatch.setattr(module, "_load_posts", lambda: (_ for _ in ()).throw(AssertionError("assembled")))
    response = client.post(EXPORT, json=SIM_OK)
    _refuse(response)


def test_simulation_override_cannot_bypass_blocked_authority(client):
    response = client.post(EXPORT, json=OVERRIDE)
    _refuse(response)


def test_disabled_simulation_policy_cannot_bypass_blocked_authority(client, monkeypatch):
    import importlib

    module = importlib.import_module("app.routers.geometry.export_router")
    monkeypatch.setattr(module, "RMOS_REQUIRE_SIMULATION", False)
    response = client.post(EXPORT, json={"gcode": "G1 X1\n"})
    _refuse(response)


def test_permission_without_simulation_still_fails_the_simulation_gate(
    client, p3_test_only_permitting_evaluator
):
    response = client.post(EXPORT, json={"gcode": "G1 X1\n"})
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "simulation_required"


def test_both_gates_permit_the_existing_export_contract(
    client, memory_store, p3_test_only_permitting_evaluator
):
    response = client.post(EXPORT, json=SIM_OK)
    assert response.status_code == 200
    assert response.headers.get("X-Simulation-Verified") == "true"
    assert response.headers.get("X-GCode-SHA256")
    assert "attachment" in (response.headers.get("content-disposition") or "").lower()
    artifact = memory_store.saved[0]
    assert artifact.decision.risk_level == "GREEN"
    assert artifact.meta["simulation_gate"]["simulation_passed"] is True
    assert artifact.hashes.gcode_sha256 == response.headers["X-GCode-SHA256"]


def test_export_draft_sibling_is_unchanged(client):
    """Outside P-3 containment."""
    response = client.post(EXPORT_DRAFT, json={"gcode": "G1 X1\n"})
    assert response.status_code == 200
    assert response.headers.get("X-ToolBox-Lane") == "draft"


@pytest.mark.parametrize("route,module_name,generator", PROBES)
def test_probe_default_authority_refuses(client, memory_store, monkeypatch, route, module_name, generator):
    module = __import__(module_name, fromlist=["probe_patterns"])

    def forbidden(**kwargs):
        raise AssertionError(generator)

    monkeypatch.setattr(module.probe_patterns, generator, forbidden)
    monkeypatch.setattr(
        module,
        "create_governed_probe_response",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("response helper")),
    )
    response = client.post(route, json={})
    _refuse(response)
    assert memory_store.saved[0].status == "BLOCKED"
    assert memory_store.saved[0].hashes.gcode_sha256 is None


@pytest.mark.parametrize("route,module_name,generator", PROBES)
def test_probe_permitting_fixture_keeps_filename_and_decision(
    client, memory_store, p3_test_only_permitting_evaluator, route, module_name, generator
):
    response = client.post(route, json={})
    assert response.status_code == 200, response.text
    disposition = response.headers.get("content-disposition") or ""
    assert response.headers.get("content-type", "").startswith("text/plain")
    assert "attachment" in disposition.lower()
    assert disposition.endswith(".nc") or ".nc" in disposition
    artifact = memory_store.saved[0]
    assert artifact.decision.risk_level == "GREEN"
    assert artifact.decision.warnings == ["p3-test-only-not-qualification"]
    assert len(memory_store.saved) == 1


def test_retract_aliases_still_block_before_generation(client):
    simple = client.post("/api/cam/retract/gcode_governed")
    download = client.post(
        "/api/cam/retract/gcode/download_governed",
        json={"features": [[[0, 0, -1], [1, 0, -1]]], "strategy": "safe"},
    )
    _refuse(simple)
    _refuse(download)
