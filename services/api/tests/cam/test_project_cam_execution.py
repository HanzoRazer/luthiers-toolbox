"""
Tests for the Project Spine -> CAM adoption edge (SPINE-003).

Covers the validated read path that drives the existing governed adaptive-clearing CAM
operation from canonical ``InstrumentProjectData`` (ADR-002):

  1. ``app.cam.project_adapter`` — pure translation/validation project state -> ``PlanIn``.
  2. ``app.projects.service.load_project_for_cam`` — project-level CAM readiness gate.
  3. ``POST /api/cam/projects/{project_id}/adaptive-plan`` — the router edge: auth,
     translation, governed execution, provenance headers, read-only boundary.
  4. Parity — a project-derived ``PlanIn`` equals the equivalent hand-built request.

Execution is read-only against project state; the adapter invents no geometry.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.cam.project_adapter import (
    build_cam_request_from_project,
    validate_project_cam_inputs,
    ALLOWED_MACHINING_OVERRIDES,
)
from app.projects.service import load_project_for_cam, serialize_design_state
from app.schemas.adaptive_schemas import PlanIn, Loop
from app.schemas.instrument_project import (
    InstrumentProjectData,
    InstrumentSpec,
    BlueprintDerivedGeometry,
    BlueprintSource,
    ManufacturingState,
    ManufacturingStatus,
)

SQUARE = [(0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0)]


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _state(outline=SQUARE, with_spec=True, manufacturing=None) -> InstrumentProjectData:
    return InstrumentProjectData(
        instrument_type="acoustic_guitar",
        spec=InstrumentSpec(scale_length_mm=645.0) if with_spec else None,
        blueprint_geometry=(
            BlueprintDerivedGeometry(source=BlueprintSource.MANUAL, body_outline_mm=outline)
            if outline is not None
            else None
        ),
        manufacturing_state=manufacturing,
    )


def _project(state: InstrumentProjectData, owner_id=None):
    from app.db.models.project import Project

    project = Project()
    project.id = uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.name = "CAM Test"
    project.instrument_type = "acoustic_guitar"
    project.data = serialize_design_state(state) if state is not None else {}
    project.created_at = datetime(2026, 7, 1, tzinfo=timezone.utc)
    project.updated_at = datetime(2026, 7, 13, tzinfo=timezone.utc)
    project.archived_at = None
    return project


# ---------------------------------------------------------------------------
# Unit — validate_project_cam_inputs
# ---------------------------------------------------------------------------

class TestValidateInputs:
    def test_valid_passes(self):
        validate_project_cam_inputs(_state())

    def test_none_state_raises(self):
        with pytest.raises(ValueError, match="No project design state"):
            validate_project_cam_inputs(None)  # type: ignore[arg-type]

    def test_missing_outline_raises(self):
        with pytest.raises(ValueError, match="body_outline_mm"):
            validate_project_cam_inputs(_state(outline=None))

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError, match="at least 3 points"):
            validate_project_cam_inputs(_state(outline=[(0.0, 0.0), (1.0, 1.0)]))

    def test_non_finite_raises(self):
        with pytest.raises(ValueError, match="non-finite"):
            validate_project_cam_inputs(_state(outline=[(0.0, 0.0), (1.0, 0.0), (float("inf"), 1.0)]))

    def test_malformed_point_raises(self):
        # Pydantic coerces to 2-tuples on construction; mutate in place (no re-validation)
        # to exercise the defensive guard against a non-(x, y) point.
        state = _state()
        state.blueprint_geometry.body_outline_mm.append((1.0, 2.0, 3.0))  # type: ignore[arg-type]
        with pytest.raises(ValueError, match=r"\(x, y\) pair"):
            validate_project_cam_inputs(state)


# ---------------------------------------------------------------------------
# Unit — build_cam_request_from_project
# ---------------------------------------------------------------------------

class TestBuildRequest:
    def test_outline_maps_to_outer_loop(self):
        plan_in = build_cam_request_from_project(_state(), tool_d=6.0)
        assert isinstance(plan_in, PlanIn)
        assert plan_in.loops[0].pts == SQUARE
        assert plan_in.tool_d == 6.0

    def test_omitted_params_keep_planin_defaults(self):
        plan_in = build_cam_request_from_project(_state(), tool_d=6.0)
        default = PlanIn(loops=[Loop(pts=SQUARE)], tool_d=6.0)
        assert plan_in.stepover == default.stepover
        assert plan_in.stepdown == default.stepdown
        assert plan_in.strategy == default.strategy

    def test_overrides_applied(self):
        plan_in = build_cam_request_from_project(
            _state(), tool_d=6.0, overrides={"stepover": 0.3, "feed_xy": 900.0, "climb": False}
        )
        assert plan_in.stepover == 0.3
        assert plan_in.feed_xy == 900.0
        assert plan_in.climb is False

    def test_unknown_override_raises(self):
        with pytest.raises(ValueError, match="Unsupported machining override"):
            build_cam_request_from_project(_state(), tool_d=6.0, overrides={"z_target": -3.0})

    def test_allowed_overrides_are_planin_fields(self):
        planin_fields = set(PlanIn.model_fields)
        assert ALLOWED_MACHINING_OVERRIDES <= planin_fields

    def test_translation_is_single_and_faithful(self):
        # Parity: project-derived request == equivalent hand-built request.
        overrides = {"stepover": 0.35, "strategy": "Spiral", "feed_xy": 1100.0}
        derived = build_cam_request_from_project(_state(), tool_d=6.0, overrides=overrides)
        direct = PlanIn(loops=[Loop(pts=SQUARE)], tool_d=6.0, **overrides)
        assert derived.model_dump() == direct.model_dump()


# ---------------------------------------------------------------------------
# Service — load_project_for_cam
# ---------------------------------------------------------------------------

class TestLoadProjectForCam:
    def test_loads_ready_project(self):
        loaded = load_project_for_cam(_project(_state()))
        assert loaded.is_ready_for_cam()

    def test_no_design_state_raises(self):
        proj = _project(None)
        with pytest.raises(ValueError, match="no design state"):
            load_project_for_cam(proj)

    def test_not_ready_raises(self):
        proj = _project(_state(with_spec=False))
        with pytest.raises(ValueError, match="not ready for CAM"):
            load_project_for_cam(proj)


# ---------------------------------------------------------------------------
# API — POST /api/cam/projects/{project_id}/adaptive-plan
# ---------------------------------------------------------------------------

class TestProjectCamRoute:
    @pytest.fixture
    def principal(self):
        from app.auth.principal import Principal
        return Principal(user_id=str(uuid.uuid4()), roles={"user"}, email="t@example.com")

    @pytest.fixture
    def project(self, principal):
        return _project(_state(), owner_id=principal.user_id)

    @pytest.fixture
    def client(self, principal, project):
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        db = MagicMock()
        db.get.return_value = project

        app.dependency_overrides[get_current_principal] = lambda: principal
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def _url(self, project):
        return f"/api/cam/projects/{project.id}/adaptive-plan"

    def test_executes_from_project_state(self, client, project):
        resp = client.post(self._url(project), json={"tool_d": 6.0})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "moves" in data and "stats" in data
        assert len(data["moves"]) > 0

    def test_provenance_headers(self, client, project):
        resp = client.post(self._url(project), json={"tool_d": 6.0})
        assert resp.status_code == 200, resp.text
        assert resp.headers.get("X-Project-Id") == str(project.id)
        assert resp.headers.get("X-Project-Revision") == project.updated_at.isoformat()
        assert resp.headers.get("X-Run-Id")  # RMOS run persisted by the governed path

    def test_read_only_does_not_mutate_project(self, client, project):
        before = dict(project.data)
        client.post(self._url(project), json={"tool_d": 6.0})
        assert project.data == before
        # manufacturing status untouched (loading a project confers no approval)
        assert project.data.get("manufacturing_state") in (None, {}) or \
            project.data["manufacturing_state"].get("status") == ManufacturingStatus.DRAFT.value

    def test_unknown_project_404(self, client):
        from app.main import app
        from app.db.session import get_db

        db = MagicMock()
        db.get.return_value = None
        app.dependency_overrides[get_db] = lambda: db
        resp = client.post(f"/api/cam/projects/{uuid.uuid4()}/adaptive-plan", json={"tool_d": 6.0})
        assert resp.status_code == 404

    def test_foreign_project_403(self, client, project):
        project.owner_id = uuid.uuid4()
        resp = client.post(self._url(project), json={"tool_d": 6.0})
        assert resp.status_code == 403

    def test_not_ready_project_422(self, client, principal):
        from app.main import app
        from app.db.session import get_db

        proj = _project(_state(with_spec=False), owner_id=principal.user_id)
        db = MagicMock()
        db.get.return_value = proj
        app.dependency_overrides[get_db] = lambda: db
        resp = client.post(f"/api/cam/projects/{proj.id}/adaptive-plan", json={"tool_d": 6.0})
        assert resp.status_code == 422
        assert "not ready for CAM" in resp.json()["detail"]

    def test_no_outline_422(self, client, principal):
        from app.main import app
        from app.db.session import get_db

        proj = _project(_state(outline=None), owner_id=principal.user_id)
        db = MagicMock()
        db.get.return_value = proj
        app.dependency_overrides[get_db] = lambda: db
        resp = client.post(f"/api/cam/projects/{proj.id}/adaptive-plan", json={"tool_d": 6.0})
        assert resp.status_code == 422
        assert "body_outline_mm" in resp.json()["detail"]

    def test_missing_tool_d_422(self, client, project):
        resp = client.post(self._url(project), json={})
        assert resp.status_code == 422  # schema-level required field

    def test_existing_adaptive_endpoint_unchanged(self, client):
        # Regression: the existing governed operation still accepts a direct PlanIn.
        resp = client.post(
            "/api/cam/pocket/adaptive/plan",
            json={"loops": [{"pts": SQUARE}], "tool_d": 6.0},
        )
        assert resp.status_code == 200, resp.text
        assert "moves" in resp.json()
