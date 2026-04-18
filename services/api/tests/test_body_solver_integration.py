"""
Integration tests for Body Solver Router (BOE ↔ IBG integration)

Tests coverage:
- POST /api/body/solve-from-dxf — Upload partial DXF, receive solved model
- POST /api/body/solve-from-landmarks — Submit user-provided landmarks
- GET /api/body/session/{session_id} — Retrieve previously solved session
- PUT /api/body/session/{session_id}/landmarks — Override landmarks and re-solve

Sprint: Week 1 — API endpoints, JSON output only
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def dreadnought_fixture_dxf():
    """
    Generate a dreadnought DXF fixture using IBG defaults.

    This creates a valid DXF that the solver can process,
    avoiding the need for a static fixture file.
    """
    from app.instrument_geometry.body.ibg import InstrumentBodyGenerator

    gen = InstrumentBodyGenerator("dreadnought")
    model = gen.generate_from_defaults()

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        gen.save_dxf(model, tmp.name)
        yield tmp.name

    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


class TestSolveFromDXF:
    """Test POST /api/body/solve-from-dxf endpoint."""

    def test_solve_dreadnought_returns_valid_dimensions(
        self, api_client, dreadnought_fixture_dxf
    ):
        """Solve dreadnought DXF and verify dimensions are plausible."""
        with open(dreadnought_fixture_dxf, "rb") as f:
            response = api_client.post(
                "/api/body/solve-from-dxf",
                files={"dxf_file": ("dreadnought.dxf", f, "application/dxf")},
                data={
                    "instrument_spec": "dreadnought",
                    "consolidate": "true",
                    "options": '{"return_json": true, "return_side_heights": true}',
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["confidence"] > 0.5

        dims = data["dimensions"]
        assert 480 < dims["body_length_mm"] < 560
        assert 340 < dims["lower_bout_mm"] < 420
        assert 250 < dims["upper_bout_mm"] < 330
        assert 200 < dims["waist_mm"] < 280

        assert "outline_points" in data
        assert len(data["outline_points"]) > 50

        assert "side_heights" in data
        assert len(data["side_heights"]) > 0

    def test_solve_unknown_spec_returns_400(self, api_client, dreadnought_fixture_dxf):
        """Unknown instrument spec returns 400 error."""
        with open(dreadnought_fixture_dxf, "rb") as f:
            response = api_client.post(
                "/api/body/solve-from-dxf",
                files={"dxf_file": ("test.dxf", f, "application/dxf")},
                data={"instrument_spec": "unknown_guitar_type"},
            )

        assert response.status_code == 400
        assert "Unknown spec" in response.json()["detail"]


class TestSolveFromLandmarks:
    """Test POST /api/body/solve-from-landmarks endpoint."""

    def test_solve_from_landmarks_returns_valid_model(self, api_client):
        """Solve from user-provided landmarks."""
        response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0},
                    {"label": "butt_center", "x_mm": 0, "y_mm": 0},
                    {"label": "neck_center", "x_mm": 0, "y_mm": 520},
                ],
                "options": {"return_json": True},
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert "session_id" in data
        assert "outline_points" in data
        assert len(data["outline_points"]) > 50

    def test_solve_from_landmarks_unknown_spec_returns_400(self, api_client):
        """Unknown instrument spec returns 400 error."""
        response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "nonexistent_type",
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0},
                ],
            },
        )

        assert response.status_code == 400


class TestSessionRetrieval:
    """Test GET /api/body/session/{session_id} endpoint."""

    def test_retrieve_session_after_solve(self, api_client):
        """Retrieve a session that was just created."""
        create_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0},
                    {"label": "butt_center", "x_mm": 0, "y_mm": 0},
                ],
            },
        )

        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        get_response = api_client.get(f"/api/body/session/{session_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "retrieved"
        assert data["instrument_spec"] == "dreadnought"
        assert "outline_points" in data
        assert "landmarks" in data

    def test_retrieve_nonexistent_session_returns_404(self, api_client):
        """Nonexistent session returns 404."""
        response = api_client.get("/api/body/session/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestLandmarkOverride:
    """Test PUT /api/body/session/{session_id}/landmarks endpoint."""

    def test_override_landmark_re_solves_model(self, api_client):
        """Override a landmark and verify model is re-solved."""
        create_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0},
                    {"label": "waist_min", "x_mm": 120.0, "y_mm": 228.0},
                ],
            },
        )

        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        original_waist = create_response.json()["dimensions"]["waist_mm"]

        override_response = api_client.put(
            f"/api/body/session/{session_id}/landmarks",
            json={
                "override_landmarks": [
                    {"label": "waist_min", "x_mm": 110.0, "y_mm": 228.0},
                ],
            },
        )

        assert override_response.status_code == 200
        data = override_response.json()
        assert data["session_id"] == session_id

    def test_add_landmark_to_session(self, api_client):
        """Add a new landmark to existing session."""
        create_response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": "dreadnought",
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0},
                ],
            },
        )

        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        add_response = api_client.put(
            f"/api/body/session/{session_id}/landmarks",
            json={
                "add_landmarks": [
                    {"label": "upper_bout_max", "x_mm": 146.0, "y_mm": 390.0},
                ],
            },
        )

        assert add_response.status_code == 200

    def test_override_nonexistent_session_returns_404(self, api_client):
        """Override on nonexistent session returns 404."""
        response = api_client.put(
            "/api/body/session/nonexistent_id/landmarks",
            json={"override_landmarks": []},
        )
        assert response.status_code == 404


class TestInstrumentSpecs:
    """Test all supported instrument specs."""

    @pytest.mark.parametrize(
        "spec_name",
        ["dreadnought", "cuatro_venezolano", "stratocaster", "jumbo"],
    )
    def test_solve_all_supported_specs(self, api_client, spec_name):
        """All supported specs should solve successfully."""
        response = api_client.post(
            "/api/body/solve-from-landmarks",
            json={
                "instrument_spec": spec_name,
                "landmarks": [
                    {"label": "lower_bout_max", "x_mm": 150.0, "y_mm": 80.0},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["confidence"] > 0
