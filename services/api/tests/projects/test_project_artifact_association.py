"""
Tests for the Project ↔ Manufacturing Artifact association edge (SPINE-004).

Covers the association of REFERENCES to RMOS run artifacts with the canonical project
record (ADR-002), without duplicating artifact payloads:

  1. ``app.projects.project_artifact_service`` — validation, ref-from-artifact mapping,
     append-only-by-run_id merge, conflict rejection, and the association write.
  2. ``POST /api/projects/{project_id}/artifacts`` — the router edge: auth, row-locked
     write, idempotency, and the 404/403/409/422 paths.
  3. Boundary — only ``manufacturing_artifacts`` is touched; RMOS artifact is never mutated.

The reference is built from the actual persisted artifact (never fabricated); RMOS keeps
sole ownership of the payload.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.projects import project_artifact_service as pas
from app.projects.project_artifact_service import (
    ArtifactAssociationConflictError,
    ArtifactNotFoundError,
    ArtifactProvenanceMismatchError,
    associate_artifact_with_project,
    build_artifact_ref_from_run,
    merge_artifact_refs,
    retrieve_project_artifacts,
    validate_project_artifact,
    _reject_artifact_conflicts,
)
from app.projects.service import (
    ProjectStateUninitializedError,
    serialize_design_state,
)
from app.schemas.instrument_project import (
    InstrumentProjectData,
    InstrumentSpec,
    ProjectArtifactRef,
)

RUN_ID = "run_abcdef"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _fake_run(run_id=RUN_ID, tool_id="adaptive:plan", status="OK", feas="f" * 64, tp="t" * 64):
    return SimpleNamespace(
        run_id=run_id,
        tool_id=tool_id,
        mode="adaptive",
        event_type="adaptive_plan_execution",
        status=status,
        created_at_utc=datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc),
        decision=SimpleNamespace(risk_level="GREEN"),
        hashes=SimpleNamespace(feasibility_sha256=feas, toolpaths_sha256=tp),
    )


def _state(with_spec=True, artifacts=None) -> InstrumentProjectData:
    return InstrumentProjectData(
        instrument_type="acoustic_guitar",
        spec=InstrumentSpec(scale_length_mm=645.0) if with_spec else None,
        manufacturing_artifacts=artifacts or [],
    )


def _project(state, owner_id=None, itype="acoustic_guitar"):
    from app.db.models.project import Project

    project = Project()
    project.id = uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.name = "Artifact Test"
    project.instrument_type = itype
    project.data = serialize_design_state(state) if state is not None else {}
    project.created_at = datetime(2026, 7, 1, tzinfo=timezone.utc)
    project.updated_at = datetime(2026, 7, 13, tzinfo=timezone.utc)
    project.archived_at = None
    return project


def _ref(run_id=RUN_ID, tool_id="adaptive:plan", associated_at="2026-07-13T00:00:00Z"):
    return ProjectArtifactRef(run_id=run_id, tool_id=tool_id, associated_at=associated_at)


# ---------------------------------------------------------------------------
# Unit — build_artifact_ref_from_run
# ---------------------------------------------------------------------------

class TestBuildRef:
    def test_maps_artifact_fields(self):
        ref = build_artifact_ref_from_run(_fake_run(), associated_at="2026-07-13T00:00:00Z", project_revision="rev1")
        assert ref.run_id == RUN_ID
        assert ref.tool_id == "adaptive:plan"
        assert ref.mode == "adaptive"
        assert ref.event_type == "adaptive_plan_execution"
        assert ref.status == "OK"
        assert ref.risk_level == "GREEN"
        assert ref.artifact_created_at == "2026-07-13T12:00:00+00:00"
        assert ref.feasibility_sha256 == "f" * 64
        assert ref.toolpaths_sha256 == "t" * 64
        assert ref.associated_at == "2026-07-13T00:00:00Z"
        assert ref.project_revision == "rev1"

    def test_no_payload_fields_present(self):
        # A reference must not carry toolpath/move payload data.
        ref = build_artifact_ref_from_run(_fake_run(), associated_at="t")
        dumped = ref.model_dump()
        assert "moves" not in dumped and "toolpaths" not in dumped and "gcode" not in dumped


# ---------------------------------------------------------------------------
# Unit — validate_project_artifact
# ---------------------------------------------------------------------------

class TestValidate:
    def test_found_returns_artifact(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            assert validate_project_artifact(RUN_ID).run_id == RUN_ID

    def test_missing_raises(self):
        with patch.object(pas, "get_run", return_value=None):
            with pytest.raises(ArtifactNotFoundError):
                validate_project_artifact(RUN_ID)

    def test_blank_run_id_raises(self):
        with pytest.raises(ArtifactNotFoundError):
            validate_project_artifact("   ")

    def test_tool_id_mismatch_raises(self):
        with patch.object(pas, "get_run", return_value=_fake_run(tool_id="drilling")):
            with pytest.raises(ArtifactProvenanceMismatchError):
                validate_project_artifact(RUN_ID, expected_tool_id="adaptive:plan")

    def test_hash_mismatch_raises(self):
        with patch.object(pas, "get_run", return_value=_fake_run(feas="a" * 64)):
            with pytest.raises(ArtifactProvenanceMismatchError):
                validate_project_artifact(RUN_ID, expected_feasibility_sha256="b" * 64)

    def test_expected_matches_passes(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            validate_project_artifact(RUN_ID, expected_tool_id="adaptive:plan", expected_feasibility_sha256="f" * 64)


# ---------------------------------------------------------------------------
# Unit — merge / conflict
# ---------------------------------------------------------------------------

class TestMergeAndConflict:
    def test_none_state_returns_incoming(self):
        incoming = [_ref("a"), _ref("b")]
        assert merge_artifact_refs(None, incoming) == incoming

    def test_append_new_run_ids(self):
        state = _state(artifacts=[_ref("a")])
        merged = merge_artifact_refs(state, [_ref("b")])
        assert [r.run_id for r in merged] == ["a", "b"]

    def test_dedupe_existing_run_id_idempotent(self):
        # Same run_id, even with a later associated_at, is dropped (original kept).
        state = _state(artifacts=[_ref("a", associated_at="2026-01-01T00:00:00Z")])
        merged = merge_artifact_refs(state, [_ref("a", associated_at="2026-09-09T00:00:00Z")])
        assert len(merged) == 1
        assert merged[0].associated_at == "2026-01-01T00:00:00Z"

    def test_conflict_ignores_association_metadata(self):
        # Different associated_at only -> NOT a conflict (idempotent re-association).
        state = _state(artifacts=[_ref("a", associated_at="2026-01-01T00:00:00Z")])
        _reject_artifact_conflicts(state, [_ref("a", associated_at="2026-09-09T00:00:00Z")])

    def test_conflict_on_different_provenance_raises(self):
        state = _state(artifacts=[_ref("a", tool_id="adaptive:plan")])
        with pytest.raises(ArtifactAssociationConflictError):
            _reject_artifact_conflicts(state, [_ref("a", tool_id="drilling")])


# ---------------------------------------------------------------------------
# Service — associate_artifact_with_project
# ---------------------------------------------------------------------------

class TestAssociateService:
    def test_associates_reference(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            project = _project(_state())
            new_state = associate_artifact_with_project(project, RUN_ID)
        assert [r.run_id for r in new_state.manufacturing_artifacts] == [RUN_ID]
        assert new_state.manufacturing_artifacts[0].project_revision == "2026-07-13T00:00:00+00:00"

    def test_idempotent_by_run_id(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            project = _project(_state())
            associate_artifact_with_project(project, RUN_ID, associated_at="2026-01-01T00:00:00Z")
            new_state = associate_artifact_with_project(project, RUN_ID, associated_at="2026-09-09T00:00:00Z")
        assert len(new_state.manufacturing_artifacts) == 1
        assert new_state.manufacturing_artifacts[0].associated_at == "2026-01-01T00:00:00Z"

    def test_missing_artifact_raises(self):
        with patch.object(pas, "get_run", return_value=None):
            with pytest.raises(ArtifactNotFoundError):
                associate_artifact_with_project(_project(_state()), RUN_ID)

    def test_uninitialized_project_raises(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            with pytest.raises(ProjectStateUninitializedError):
                associate_artifact_with_project(_project(None, itype=None), RUN_ID)

    def test_seeds_from_instrument_type_when_no_state(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            project = _project(None, itype="electric_guitar")
            new_state = associate_artifact_with_project(project, RUN_ID)
        assert new_state.instrument_type.value == "electric_guitar"
        assert len(new_state.manufacturing_artifacts) == 1

    def test_only_artifacts_field_changed(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            state = _state()
            project = _project(state)
            before = serialize_design_state(state)
            new_state = associate_artifact_with_project(project, RUN_ID)
        after = serialize_design_state(new_state)
        for key in after:
            if key == "manufacturing_artifacts":
                continue
            assert after[key] == before.get(key), f"association mutated '{key}'"

    def test_retrieve_project_artifacts(self):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            project = _project(_state())
            new_state = associate_artifact_with_project(project, RUN_ID)
            project.data = serialize_design_state(new_state)
        assert [r.run_id for r in retrieve_project_artifacts(project)] == [RUN_ID]

    def test_retrieve_empty_when_no_state(self):
        assert retrieve_project_artifacts(_project(None)) == []


# ---------------------------------------------------------------------------
# API — POST /api/projects/{project_id}/artifacts
# ---------------------------------------------------------------------------

class TestAssociateRoute:
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
        return f"/api/projects/{project.id}/artifacts"

    def test_associates_returns_state(self, client, project):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            resp = client.post(self._url(project), json={"run_id": RUN_ID})
        assert resp.status_code == 200, resp.text
        arts = resp.json()["design_state"]["manufacturing_artifacts"]
        assert len(arts) == 1 and arts[0]["run_id"] == RUN_ID
        assert arts[0]["tool_id"] == "adaptive:plan"

    def test_idempotent(self, client, project):
        with patch.object(pas, "get_run", return_value=_fake_run()):
            client.post(self._url(project), json={"run_id": RUN_ID})
            resp = client.post(self._url(project), json={"run_id": RUN_ID})
        assert resp.status_code == 200
        assert len(resp.json()["design_state"]["manufacturing_artifacts"]) == 1

    def test_missing_artifact_404(self, client, project):
        with patch.object(pas, "get_run", return_value=None):
            resp = client.post(self._url(project), json={"run_id": "nope"})
        assert resp.status_code == 404

    def test_provenance_mismatch_422(self, client, project):
        with patch.object(pas, "get_run", return_value=_fake_run(tool_id="drilling")):
            resp = client.post(self._url(project), json={"run_id": RUN_ID, "expected_tool_id": "adaptive:plan"})
        assert resp.status_code == 422

    def test_foreign_project_403(self, client, project):
        project.owner_id = uuid.uuid4()
        with patch.object(pas, "get_run", return_value=_fake_run()):
            resp = client.post(self._url(project), json={"run_id": RUN_ID})
        assert resp.status_code == 403

    def test_missing_run_id_422(self, client, project):
        resp = client.post(self._url(project), json={})
        assert resp.status_code == 422  # schema-level required field

    def test_conflict_409(self, client, principal):
        # Pre-seed a stored ref for RUN_ID with DIFFERENT provenance than the live artifact.
        seeded = _state(artifacts=[_ref(RUN_ID, tool_id="stale:tool")])
        proj = _project(seeded, owner_id=principal.user_id)
        from app.main import app
        from app.db.session import get_db
        db = MagicMock()
        db.get.return_value = proj
        app.dependency_overrides[get_db] = lambda: db
        with patch.object(pas, "get_run", return_value=_fake_run(tool_id="adaptive:plan")):
            resp = client.post(f"/api/projects/{proj.id}/artifacts", json={"run_id": RUN_ID})
        assert resp.status_code == 409

    def test_read_only_against_artifact(self, client, project):
        artifact = _fake_run()
        with patch.object(pas, "get_run", return_value=artifact):
            client.post(self._url(project), json={"run_id": RUN_ID})
        # The artifact object is never mutated by association.
        assert artifact.tool_id == "adaptive:plan"
        assert artifact.status == "OK"

    def test_put_design_state_preserves_artifacts(self, client, principal):
        # Data-loss guard: a full-state PUT that omits manufacturing_artifacts must not
        # drop associations already recorded on the project (append-only merge in PUT).
        seeded = _state(artifacts=[_ref(RUN_ID)])
        proj = _project(seeded, owner_id=principal.user_id)
        from app.main import app
        from app.db.session import get_db
        db = MagicMock()
        db.get.return_value = proj
        app.dependency_overrides[get_db] = lambda: db

        put_body = {"design_state": _state(artifacts=[]).model_dump(mode="json")}
        resp = client.put(f"/api/projects/{proj.id}/design-state", json=put_body)
        assert resp.status_code == 200, resp.text
        arts = resp.json()["design_state"]["manufacturing_artifacts"]
        assert [a["run_id"] for a in arts] == [RUN_ID]
