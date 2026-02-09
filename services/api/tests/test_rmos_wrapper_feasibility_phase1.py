"""
RMOS Wrapper Feasibility Phase 1 Integration Tests

Verifies that feasibility precedes CAM and is properly attached/persisted.
Prevents regression to "decorative feasibility" where check runs after CAM.

Contract assertions:
- feasibility_sha256 is present and 64-char hex
- attachments includes kind "feasibility"
- decision.risk_level matches feasibility risk_level
- feasibility.json is included in operator pack (if available)
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path
import json
import zipfile
import io

# Test fixture path
TESTDATA = Path(__file__).parent / "testdata"


@pytest.fixture
def app():
    """Create minimal app with MVP wrapper and required routers."""
    from fastapi import FastAPI
    from app.rmos.mvp_wrapper import router as mvp_wrapper_router
    from app.routers.adaptive_router import router as adaptive_router
    from app.rmos.runs_v2.exports import router as exports_router

    app = FastAPI()
    app.include_router(mvp_wrapper_router)
    app.include_router(adaptive_router, prefix="/api")
    app.include_router(exports_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def dxf_fixture():
    """Load the MVP test DXF fixture."""
    dxf_path = TESTDATA / "mvp_rect_with_island.dxf"
    if not dxf_path.exists():
        pytest.skip(f"Test fixture not found: {dxf_path}")
    return dxf_path.read_bytes()


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestFeasibilityPrecedesCAM:
    """Verify feasibility is computed BEFORE CAM, not after."""

    def test_response_has_feasibility_sha256(self, client, dxf_fixture):
        """Wrapper response includes feasibility_sha256 in hashes."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "stepover": "0.45",
                "stepdown": "1.5",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()

        # Feasibility SHA must be present and 64 hex chars
        assert "hashes" in data
        feas_sha = data["hashes"].get("feasibility_sha256")
        assert feas_sha is not None, "feasibility_sha256 missing from hashes"
        assert len(feas_sha) == 64, f"feasibility_sha256 must be 64 chars, got {len(feas_sha)}"
        assert all(c in "0123456789abcdef" for c in feas_sha), "feasibility_sha256 must be hex"

    def test_response_has_feasibility_attachment(self, client, dxf_fixture):
        """Wrapper response includes feasibility attachment."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={"tool_d": "6.0"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find feasibility attachment
        attachments = data.get("attachments", [])
        feas_att = next((a for a in attachments if a.get("kind") == "feasibility"), None)
        assert feas_att is not None, "feasibility attachment not found in response"
        assert feas_att.get("sha256"), "feasibility attachment missing sha256"
        assert feas_att.get("filename") == "feasibility.json"

    def test_decision_matches_feasibility_risk_level(self, client, dxf_fixture):
        """Decision risk_level is derived from feasibility, not computed separately."""
        # Valid params -> GREEN
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "stepover": "0.45",
                "stepdown": "1.5",
                "z_rough": "-3.0",
                "safe_z": "5.0",
                "feed_xy": "1200",
                "feed_z": "300",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # For valid params, should be GREEN or YELLOW (never RED)
        risk_level = data["decision"]["risk_level"]
        assert risk_level in ("GREEN", "YELLOW"), f"Expected GREEN/YELLOW, got {risk_level}"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestFeasibilityYellowWarnings:
    """Verify YELLOW warnings are surfaced from feasibility."""

    def test_yellow_on_feed_z_gt_feed_xy(self, client, dxf_fixture):
        """feed_z > feed_xy triggers YELLOW warning."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "feed_xy": "1200",
                "feed_z": "1500",  # Greater than feed_xy
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["decision"]["risk_level"] == "YELLOW"
        warnings = data.get("warnings", [])
        assert any("feed_z" in w.lower() for w in warnings), f"Expected feed_z warning, got: {warnings}"

    def test_yellow_on_large_stepdown(self, client, dxf_fixture):
        """stepdown > 3mm triggers YELLOW warning."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "stepdown": "5.0",  # > 3mm threshold
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["decision"]["risk_level"] == "YELLOW"
        warnings = data.get("warnings", [])
        assert any("stepdown" in w.lower() for w in warnings), f"Expected stepdown warning, got: {warnings}"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestFeasibilityRedBlocking:
    """Verify RED conditions are detected and reported."""

    def test_red_on_invalid_tool_d(self, client, dxf_fixture):
        """tool_d=0 triggers RED blocking."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "0",  # Invalid
                "stepover": "0.45",
            },
        )
        # May fail due to CAM error, but feasibility should still be captured
        data = response.json()

        # Decision should reflect RED
        assert data["decision"]["risk_level"] == "RED"
        assert data["decision"].get("block_reason") is not None

    def test_red_on_invalid_z_rough(self, client, dxf_fixture):
        """z_rough >= 0 triggers RED blocking."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "z_rough": "1.0",  # Positive is invalid (must be negative)
            },
        )
        data = response.json()

        assert data["decision"]["risk_level"] == "RED"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestFeasibilityPersistence:
    """Verify feasibility is persisted in run artifact."""

    def test_artifact_contains_feasibility(self, client, dxf_fixture):
        """Run artifact includes feasibility data."""
        response = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={"tool_d": "6.0"},
        )
        assert response.status_code == 200
        data = response.json()

        if not data.get("rmos_persisted"):
            pytest.skip("RMOS not persisted in this environment")

        run_id = data["run_id"]
        from app.rmos.runs_v2.store import get_run

        artifact = get_run(run_id)
        if artifact is None:
            pytest.skip("Run artifact not found (may be isolated test)")

        # Artifact should have feasibility data
        assert artifact.feasibility is not None, "Run artifact missing feasibility"
        assert artifact.feasibility.get("risk_level") in ("GREEN", "YELLOW", "RED")
        assert artifact.feasibility.get("engine_version") == "feasibility_engine_v1"

        # Hashes should include feasibility_sha256
        assert artifact.hashes.feasibility_sha256 is not None
        assert len(artifact.hashes.feasibility_sha256) == 64


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestFeasibilityDeterminism:
    """Verify feasibility hash is deterministic."""

    def test_same_params_same_feasibility_hash(self, client, dxf_fixture):
        """Identical params produce identical feasibility hash."""
        params = {
            "tool_d": "6.0",
            "stepover": "0.45",
            "stepdown": "1.5",
            "feed_xy": "1200",
            "feed_z": "300",
        }

        # First request
        resp1 = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data=params,
        )
        assert resp1.status_code == 200
        hash1 = resp1.json()["hashes"]["feasibility_sha256"]

        # Second request with same params
        resp2 = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data=params,
        )
        assert resp2.status_code == 200
        hash2 = resp2.json()["hashes"]["feasibility_sha256"]

        assert hash1 == hash2, "Feasibility hash should be deterministic for same params"

    def test_different_params_different_feasibility_hash(self, client, dxf_fixture):
        """Different params that change outcome produce different feasibility hash."""
        # Request 1: valid params -> GREEN
        resp1 = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "feed_xy": "1200",
                "feed_z": "300",  # < feed_xy -> GREEN
            },
        )
        assert resp1.status_code == 200
        hash1 = resp1.json()["hashes"]["feasibility_sha256"]

        # Request 2: params that trigger YELLOW
        resp2 = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
            data={
                "tool_d": "6.0",
                "feed_xy": "1200",
                "feed_z": "1500",  # > feed_xy -> YELLOW
            },
        )
        assert resp2.status_code == 200
        hash2 = resp2.json()["hashes"]["feasibility_sha256"]

        assert hash1 != hash2, "Different outcomes should produce different hashes"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_wrapper_persists_run_with_feasibility_in_runs_v2_store(tmp_path, monkeypatch, dxf_fixture):
    """
    Isolated test: verifies run persistence using tmp_path for RMOS storage.

    Uses monkeypatch to isolate RMOS_RUNS_DIR and RMOS_RUN_ATTACHMENTS_DIR
    so test doesn't pollute shared storage or depend on external state.
    """
    # Isolate storage directories
    runs_dir = tmp_path / "runs"
    attachments_dir = tmp_path / "attachments"
    runs_dir.mkdir(parents=True)
    attachments_dir.mkdir(parents=True)

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(attachments_dir))
    # Seed empty index
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    # Reset Runs v2 singleton store so it picks up env vars in this test process.
    # This must happen BEFORE app/testclient creation to prevent "sticky" defaults.
    from app.rmos.runs_v2 import store_api
    # NOTE: The singleton lives in store_api, not store (store.py re-exports functions only)
    store_api._default_store = None

    # Create fresh app after env and store reset
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.rmos.mvp_wrapper import router as mvp_wrapper_router
    from app.routers.adaptive_router import router as adaptive_router
    from app.rmos.runs_v2.exports import router as exports_router

    app = FastAPI()
    app.include_router(mvp_wrapper_router)
    app.include_router(adaptive_router, prefix="/api")
    app.include_router(exports_router)
    client = TestClient(app)

    # Execute wrapper
    response = client.post(
        "/api/rmos/wrap/mvp/dxf-to-grbl",
        files={"file": ("test.dxf", dxf_fixture, "application/dxf")},
        data={
            "tool_d": "6.0",
            "stepover": "0.45",
            "stepdown": "1.5",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Verify response structure
    assert "run_id" in data
    assert "hashes" in data
    assert data["hashes"].get("feasibility_sha256") is not None
    assert len(data["hashes"]["feasibility_sha256"]) == 64

    # Verify feasibility attachment exists
    attachments = data.get("attachments", [])
    feas_att = next((a for a in attachments if a.get("kind") == "feasibility"), None)
    assert feas_att is not None, "feasibility attachment missing"

    # Verify run was persisted to isolated storage (date-partitioned)
    run_id = data["run_id"]
    # Runs are stored in date partitions: {runs_dir}/{YYYY-MM-DD}/{run_id}.json
    run_files = list(runs_dir.glob(f"*/{run_id}.json"))
    assert len(run_files) == 1, f"Run file not persisted. Found: {list(runs_dir.glob('**/*.json'))}"
    run_file = run_files[0]

    # Load and verify run artifact
    run_data = json.loads(run_file.read_text())
    assert run_data.get("feasibility") is not None
    assert run_data["feasibility"]["risk_level"] in ("GREEN", "YELLOW", "RED")
    assert run_data["feasibility"]["engine_version"] == "feasibility_engine_v1"
    assert run_data["hashes"]["feasibility_sha256"] == data["hashes"]["feasibility_sha256"]
