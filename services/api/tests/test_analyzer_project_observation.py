"""
Tests for the Analyzer -> Project Spine observation adoption edge (SPINE-002).

Covers the three new units of the ADR-002 enrichment edge:

  1. ``app.analyzer.project_observation`` — pure mapping/validation of a completed
     ``InterpretationResult`` into a canonical ``AnalyzerObservation`` (no fabrication).
  2. ``app.projects.service`` — the append-only-by-run_id merge and the
     ``append_analyzer_observation`` project-state write.
  3. ``POST /api/analyzer/projects/{project_id}/observations`` — the router edge,
     including auth gating, idempotency, and the advisory boundary.

The write is ADVISORY: it may only touch ``analyzer_observations`` and must confer no
geometry / material / CAM / RMOS authority.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.analyzer.schemas import (
    InterpretationResult,
    DesignRecommendation,
    RecommendationSeverity,
)
from app.analyzer.project_observation import (
    build_analyzer_observation,
    validate_analyzer_observation_source,
    _extract_mode_frequencies,
)
from app.projects.service import (
    merge_analyzer_observations,
    append_analyzer_observation,
    create_default_design_state,
    serialize_design_state,
    parse_design_state,
)
from app.schemas.instrument_project import AnalyzerObservation


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------

def _interpretation(**overrides) -> InterpretationResult:
    """A complete, valid interpretation; override individual fields per test."""
    base = dict(
        specimen_id="spec-1",
        interpreted_at="2026-07-13T10:00:00Z",
        primary_modes=[{"frequency_hz": 104.0}, {"frequency_hz": 210.5}],
        wolf_assessment="Mild wolf near G#.",
        tonal_character="balanced",
        recommendations=[
            DesignRecommendation(
                severity=RecommendationSeverity.SUGGESTION,
                category="bracing",
                message="Scallop the X-brace slightly.",
                reference_instrument="martin_d28_1937",
            ),
        ],
    )
    base.update(overrides)
    return InterpretationResult(**base)


def _seed_project(design_state=None, instrument_type: str = "acoustic_guitar"):
    """
    Build an in-memory Project ORM object (no DB session). SQLAlchemy models are
    plain Python objects until added to a session, so this exercises the real
    service/response code paths without a Postgres-specific backend.
    """
    from app.db.models.project import Project

    project = Project()
    project.id = uuid.uuid4()
    project.owner_id = uuid.uuid4()
    project.name = "Test Build"
    project.instrument_type = instrument_type
    project.data = serialize_design_state(design_state) if design_state else {}
    project.created_at = None
    project.updated_at = None
    project.archived_at = None
    return project


# ---------------------------------------------------------------------------
# Unit — _extract_mode_frequencies
# ---------------------------------------------------------------------------

class TestExtractModeFrequencies:
    def test_primary_key_frequency_hz(self):
        assert _extract_mode_frequencies([{"frequency_hz": 100.0}]) == [100.0]

    def test_alternate_frequency_keys(self):
        modes = [{"freq_hz": 80}, {"frequency": 90}, {"freq": 95}, {"hz": 110}]
        assert _extract_mode_frequencies(modes) == [80.0, 90.0, 95.0, 110.0]

    def test_first_matching_key_wins(self):
        # frequency_hz is tried before freq — only one value emitted per mode.
        assert _extract_mode_frequencies([{"frequency_hz": 100.0, "freq": 999.0}]) == [100.0]

    def test_skips_non_dict_and_keyless_entries(self):
        modes = [{"frequency_hz": 100.0}, "junk", {"amplitude": 5.0}, None]
        assert _extract_mode_frequencies(modes) == [100.0]

    def test_skips_non_numeric_values(self):
        assert _extract_mode_frequencies([{"frequency_hz": "not-a-number"}]) == []

    def test_none_value_skipped_falls_through_to_next_key(self):
        assert _extract_mode_frequencies([{"frequency_hz": None, "freq": 120.0}]) == [120.0]

    def test_empty_and_none_inputs(self):
        assert _extract_mode_frequencies([]) == []
        assert _extract_mode_frequencies(None) == []


# ---------------------------------------------------------------------------
# Unit — validate_analyzer_observation_source
# ---------------------------------------------------------------------------

class TestValidateSource:
    def test_valid_passes(self):
        validate_analyzer_observation_source(_interpretation(), "run-1")

    @pytest.mark.parametrize("bad_run_id", ["", "   ", None])
    def test_missing_run_id_raises(self, bad_run_id):
        with pytest.raises(ValueError, match="run_id"):
            validate_analyzer_observation_source(_interpretation(), bad_run_id)  # type: ignore[arg-type]

    def test_blank_specimen_id_raises(self):
        with pytest.raises(ValueError, match="specimen_id"):
            validate_analyzer_observation_source(_interpretation(specimen_id="  "), "run-1")

    def test_blank_interpreted_at_raises(self):
        with pytest.raises(ValueError, match="interpreted_at"):
            validate_analyzer_observation_source(_interpretation(interpreted_at=""), "run-1")


# ---------------------------------------------------------------------------
# Unit — build_analyzer_observation
# ---------------------------------------------------------------------------

class TestBuildObservation:
    def test_maps_all_fields(self):
        obs = build_analyzer_observation(
            _interpretation(), "run-1", wsi=0.2, interpretation_confidence=0.8
        )
        assert isinstance(obs, AnalyzerObservation)
        assert obs.run_id == "run-1"
        assert obs.specimen_id == "spec-1"
        assert obs.observed_at == "2026-07-13T10:00:00Z"
        assert obs.primary_modes_hz == [104.0, 210.5]
        assert obs.wsi == 0.2
        assert obs.tonal_character == "balanced"
        assert obs.reference_instrument == "martin_d28_1937"
        assert obs.interpretation_confidence == 0.8

    def test_wolf_assessment_prepended_to_findings(self):
        obs = build_analyzer_observation(_interpretation(), "run-1")
        assert obs.findings[0] == "Mild wolf near G#."
        assert "Scallop the X-brace slightly." in obs.findings

    def test_no_wolf_assessment_findings_from_recommendations_only(self):
        obs = build_analyzer_observation(_interpretation(wolf_assessment=None), "run-1")
        assert obs.findings == ["Scallop the X-brace slightly."]

    def test_reference_instrument_is_first_non_null(self):
        interp = _interpretation(recommendations=[
            DesignRecommendation(severity=RecommendationSeverity.INFO, category="a", message="m1"),
            DesignRecommendation(
                severity=RecommendationSeverity.INFO, category="b", message="m2",
                reference_instrument="gibson_j45",
            ),
        ])
        obs = build_analyzer_observation(interp, "run-1")
        assert obs.reference_instrument == "gibson_j45"

    def test_defaults_when_provenance_absent_not_fabricated(self):
        interp = _interpretation(
            wolf_assessment=None, tonal_character=None, recommendations=[], primary_modes=[]
        )
        obs = build_analyzer_observation(interp, "run-1")
        assert obs.wsi is None
        assert obs.tonal_character is None
        assert obs.reference_instrument is None
        assert obs.findings == []
        assert obs.primary_modes_hz == []
        assert obs.interpretation_confidence == 0.0

    def test_run_id_and_ids_are_stripped(self):
        obs = build_analyzer_observation(
            _interpretation(specimen_id=" spec-2 ", interpreted_at=" 2026-01-01T00:00:00Z "),
            " run-x ",
        )
        assert obs.run_id == "run-x"
        assert obs.specimen_id == "spec-2"
        assert obs.observed_at == "2026-01-01T00:00:00Z"

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError):
            build_analyzer_observation(_interpretation(), "")


# ---------------------------------------------------------------------------
# Unit — merge_analyzer_observations (append-only, dedup by run_id)
# ---------------------------------------------------------------------------

def _obs(run_id: str) -> AnalyzerObservation:
    return AnalyzerObservation(run_id=run_id, specimen_id="s", observed_at="t")


class TestMergeObservations:
    def test_none_existing_state_returns_incoming(self):
        incoming = [_obs("a"), _obs("b")]
        assert merge_analyzer_observations(None, incoming) == incoming

    def test_appends_new_run_ids(self):
        state = create_default_design_state("acoustic_guitar")
        state = state.model_copy(update={"analyzer_observations": [_obs("a")]})
        merged = merge_analyzer_observations(state, [_obs("b")])
        assert [o.run_id for o in merged] == ["a", "b"]

    def test_dedupes_existing_run_id_idempotent(self):
        state = create_default_design_state("acoustic_guitar")
        state = state.model_copy(update={"analyzer_observations": [_obs("a")]})
        merged = merge_analyzer_observations(state, [_obs("a")])
        assert [o.run_id for o in merged] == ["a"]

    def test_existing_never_mutated(self):
        state = create_default_design_state("acoustic_guitar")
        original = [_obs("a")]
        state = state.model_copy(update={"analyzer_observations": original})
        merge_analyzer_observations(state, [_obs("b")])
        assert original == [_obs("a")]  # source list untouched


# ---------------------------------------------------------------------------
# Unit — append_analyzer_observation (project-state write)
# ---------------------------------------------------------------------------

class TestAppendService:
    def test_appends_to_existing_state(self):
        state = create_default_design_state("acoustic_guitar")
        project = _seed_project(design_state=state)
        new_state = append_analyzer_observation(project, [_obs("run-1")])
        assert [o.run_id for o in new_state.analyzer_observations] == ["run-1"]
        # persisted back into project.data
        assert parse_design_state(project.data).analyzer_observations[0].run_id == "run-1"

    def test_idempotent_by_run_id(self):
        state = create_default_design_state("acoustic_guitar")
        project = _seed_project(design_state=state)
        append_analyzer_observation(project, [_obs("run-1")])
        new_state = append_analyzer_observation(project, [_obs("run-1")])
        assert len(new_state.analyzer_observations) == 1

    def test_seeds_default_from_project_instrument_type_when_no_state(self):
        project = _seed_project(design_state=None, instrument_type="electric_guitar")
        new_state = append_analyzer_observation(project, [_obs("run-1")])
        assert new_state.instrument_type.value == "electric_guitar"
        assert [o.run_id for o in new_state.analyzer_observations] == ["run-1"]

    def test_advisory_only_does_not_touch_spec_or_manufacturing(self):
        state = create_default_design_state("acoustic_guitar")
        project = _seed_project(design_state=state)
        before = serialize_design_state(state)
        new_state = append_analyzer_observation(project, [_obs("run-1")])
        after = serialize_design_state(new_state)
        # Only analyzer_observations changed.
        for key in after:
            if key == "analyzer_observations":
                continue
            assert after[key] == before.get(key), f"advisory write mutated '{key}'"


# ---------------------------------------------------------------------------
# Integration — POST /api/analyzer/projects/{project_id}/observations
# ---------------------------------------------------------------------------

class TestObservationRoute:
    @pytest.fixture
    def principal(self):
        from app.auth.principal import Principal
        return Principal(user_id=str(uuid.uuid4()), roles={"user"}, email="t@example.com")

    @pytest.fixture
    def project(self, principal):
        proj = _seed_project(design_state=create_default_design_state("acoustic_guitar"))
        proj.owner_id = principal.user_id  # owned by the caller
        return proj

    @pytest.fixture
    def client(self, principal, project):
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        db = MagicMock()
        db.get.return_value = project  # _get_project_or_404 resolves via db.get

        app.dependency_overrides[get_current_principal] = lambda: principal
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as c:
            c._seed_project = project  # type: ignore[attr-defined]
            yield c
        app.dependency_overrides.clear()

    def _payload(self, run_id="run-1"):
        return {
            "interpretation": {
                "specimen_id": "spec-1",
                "interpreted_at": "2026-07-13T10:00:00Z",
                "primary_modes": [{"frequency_hz": 104.0}],
                "wolf_assessment": "Mild wolf.",
                "tonal_character": "warm",
                "recommendations": [],
            },
            "run_id": run_id,
            "wsi": 0.3,
            "interpretation_confidence": 0.75,
        }

    def test_appends_observation_returns_design_state(self, client, project):
        resp = client.post(
            f"/api/analyzer/projects/{project.id}/observations", json=self._payload()
        )
        assert resp.status_code == 200
        obs = resp.json()["design_state"]["analyzer_observations"]
        assert len(obs) == 1
        assert obs[0]["run_id"] == "run-1"
        assert obs[0]["wsi"] == 0.3
        assert obs[0]["primary_modes_hz"] == [104.0]

    def test_idempotent_same_run_id(self, client, project):
        url = f"/api/analyzer/projects/{project.id}/observations"
        client.post(url, json=self._payload("run-1"))
        resp = client.post(url, json=self._payload("run-1"))
        assert resp.status_code == 200
        assert len(resp.json()["design_state"]["analyzer_observations"]) == 1

    def test_missing_run_id_is_422(self, client, project):
        payload = self._payload()
        del payload["run_id"]
        resp = client.post(
            f"/api/analyzer/projects/{project.id}/observations", json=payload
        )
        assert resp.status_code == 422  # schema-level required field

    def test_blank_run_id_is_400(self, client, project):
        resp = client.post(
            f"/api/analyzer/projects/{project.id}/observations",
            json=self._payload(run_id="   "),
        )
        assert resp.status_code == 400

    def test_foreign_project_is_403(self, client, project, principal):
        project.owner_id = uuid.uuid4()  # someone else owns it
        resp = client.post(
            f"/api/analyzer/projects/{project.id}/observations", json=self._payload()
        )
        assert resp.status_code == 403

    def test_missing_project_is_404(self, client):
        from app.auth.deps import get_current_principal
        from app.db.session import get_db
        from app.main import app

        # Rebind db.get -> None so _get_project_or_404 raises 404.
        db = MagicMock()
        db.get.return_value = None
        app.dependency_overrides[get_db] = lambda: db
        resp = client.post(
            f"/api/analyzer/projects/{uuid.uuid4()}/observations", json=self._payload()
        )
        assert resp.status_code == 404
