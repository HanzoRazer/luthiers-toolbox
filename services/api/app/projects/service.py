# services/api/app/projects/service.py
"""
Instrument Project Service (PROJ-004)

Persistence layer for InstrumentProjectData inside the existing Project.data JSONB field.

No new database tables. The projects table already exists with:
    - id (UUID)
    - owner_id (UUID)
    - name (str)
    - instrument_type (str)  ← kept in sync with InstrumentProjectData.instrument_type
    - data (JSONB)           ← holds InstrumentProjectData as JSON
    - features_used (list)
    - created_at / updated_at

This service reads/writes the typed InstrumentProjectData from/into that data field.

See docs/PLATFORM_ARCHITECTURE.md — Layer 0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError

from ..schemas.instrument_project import (
    AnalyzerObservation,
    CURRENT_SCHEMA_VERSION,
    DesignStateResponse,
    InstrumentProjectData,
)
# ---------------------------------------------------------------------------
# Migration-safe defaults
# When reading an old project whose data field predates a schema field,
# Pydantic will fill in the Optional defaults (None / []).
# ---------------------------------------------------------------------------

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservationConflictError(Exception):
    """An incoming ``run_id`` already exists on the project with a DIFFERENT payload.

    Append-only + idempotent means re-posting the *same* run is a no-op, but re-posting a
    *different* payload under an existing ``run_id`` is a genuine conflict — surfaced rather
    than silently dropped (which would preserve stale/wrong data with no signal).
    """


class ProjectStateUninitializedError(Exception):
    """No design state exists yet and the project has no declared ``instrument_type``.

    Without a declared type there is no honest way to seed a canonical home for an
    observation — fail loudly rather than fabricating a default instrument type.
    """


def lock_project_row_for_update(db: Any, project: Any) -> None:
    """Row-lock a project before a read-modify-write of ``Project.data``.

    All ``Project.data`` writers (``PUT /design-state`` and the analyzer observation edge)
    serialize through ``SELECT ... FOR UPDATE`` so two whole-blob writes cannot silently
    lose each other's changes (classic read-merge-write race). Must be called inside the
    request transaction, BEFORE reading ``project.data``; the lock is held until commit.

    Backend-safe: on backends without row locking (e.g. SQLite in tests) the ``FOR UPDATE``
    clause is simply not emitted — no error, no serialization. Real serialization on
    PostgreSQL. A concurrency test requires a real two-session PostgreSQL harness.
    """
    db.refresh(project, with_for_update=True)


def parse_design_state(raw_data: Optional[Dict[str, Any]]) -> Optional[InstrumentProjectData]:
    """
    Parse raw JSONB dict into InstrumentProjectData.

    Returns None if raw_data is empty or None.
    Silently drops unrecognized fields (forward-compatibility from future schema versions).
    Raises ValueError with context if parsing fails on a non-empty blob.
    """
    if not raw_data:
        return None
    try:
        return InstrumentProjectData.model_validate(raw_data)
    except ValidationError as exc:
        # Preserve the original data — don't corrupt projects on schema drift
        raise ValueError(
            f"Failed to parse design_state — schema may have changed. "
            f"schema_version in data: {raw_data.get('schema_version', 'missing')}. "
            f"Current: {CURRENT_SCHEMA_VERSION}. "
            f"Errors: {exc}"
        ) from exc


def serialize_design_state(state: InstrumentProjectData) -> Dict[str, Any]:
    """
    Serialize InstrumentProjectData to a JSONB-safe dict.

    Always writes current schema_version.
    """
    data = state.model_dump(mode="json", exclude_none=False)
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    return data


def build_design_state_response(
    project_row: Any,
    design_state: Optional[InstrumentProjectData],
) -> DesignStateResponse:
    """
    Build the API response for GET /api/projects/{id}/design-state.

    project_row is the ORM Project object or a dict from the DB query.
    """
    if hasattr(project_row, "__dict__"):
        # SQLAlchemy ORM object
        project_id = str(project_row.id)
        name = project_row.name
        instrument_type = project_row.instrument_type
        created_at = project_row.created_at.isoformat() if project_row.created_at else ""
        updated_at = project_row.updated_at.isoformat() if project_row.updated_at else ""
    else:
        # Dict (e.g. from raw SQL)
        project_id = str(project_row.get("id", ""))
        name = project_row.get("name", "")
        instrument_type = project_row.get("instrument_type")
        created_at = str(project_row.get("created_at", ""))
        updated_at = str(project_row.get("updated_at", ""))

    return DesignStateResponse(
        project_id=project_id,
        name=name,
        instrument_type=instrument_type,
        design_state=design_state,
        created_at=created_at,
        updated_at=updated_at,
    )


def merge_analyzer_observations(
    existing_state: Optional[InstrumentProjectData],
    incoming: list[AnalyzerObservation],
) -> list[AnalyzerObservation]:
    """
    Append-only merge of analyzer observations, deduplicated by stable ``run_id``.

    Canonical single implementation of the ADR-002 append-only observation rule — used
    by both ``put_design_state`` (full-state write) and ``append_analyzer_observation``
    (targeted enrichment) so all writers behave identically. Existing observations are
    never mutated or replaced; an incoming observation whose ``run_id`` already exists is
    dropped (idempotent), preventing data loss.
    """
    existing = list(existing_state.analyzer_observations) if existing_state else []
    existing_ids = {obs.run_id for obs in existing}
    return existing + [obs for obs in incoming if obs.run_id not in existing_ids]


def _reject_run_id_conflicts(
    existing_state: Optional[InstrumentProjectData],
    incoming: list[AnalyzerObservation],
) -> None:
    """Raise :class:`ObservationConflictError` if an incoming ``run_id`` already exists
    with a *different* payload. Identical re-posts pass through (idempotent)."""
    existing_by_id = {
        obs.run_id: obs
        for obs in (existing_state.analyzer_observations if existing_state else [])
    }
    for obs in incoming:
        prior = existing_by_id.get(obs.run_id)
        if prior is not None and prior != obs:
            raise ObservationConflictError(
                f"run_id '{obs.run_id}' is already recorded with a different payload; "
                "re-posting a run must be byte-identical (append-only — no silent overwrite "
                "of the earlier observation)."
            )


def append_analyzer_observation(
    project: Any,
    observations: list[AnalyzerObservation],
) -> InstrumentProjectData:
    """
    Append advisory ``AnalyzerObservation`` records to a project's canonical state,
    through the existing project-state serialization (ADR-002 Layer-0).

    Append-only + deduplicated by ``run_id`` (see :func:`merge_analyzer_observations`).
    Only ``analyzer_observations`` is touched — spec / geometry / bridge / neck /
    material / manufacturing state are preserved unchanged. Confers no manufacturing or
    geometry authority.

    Fail-closed integrity:
      - An incoming ``run_id`` that already exists with a *different* payload raises
        :class:`ObservationConflictError` (never silently keeps stale data).
      - If the project has no design state yet, a default is seeded keyed to the project's
        own declared ``instrument_type`` — **read, never fabricated**. A project with
        neither state nor a declared ``instrument_type`` raises
        :class:`ProjectStateUninitializedError` rather than inventing a default type.

    Concurrency: this is a read-modify-write of the whole ``Project.data`` blob. Callers
    that persist must first row-lock via :func:`lock_project_row_for_update` (the routers
    do) and are responsible for ``session.commit()``.
    """
    existing_state = parse_design_state(project.data)
    if existing_state is None:
        if not project.instrument_type:
            raise ProjectStateUninitializedError(
                "project has no design state and no declared instrument_type; cannot seed a "
                "canonical home for the observation without fabricating an instrument type."
            )
        existing_state = create_default_design_state(
            instrument_type=project.instrument_type,
        )
    _reject_run_id_conflicts(existing_state, observations)
    merged = merge_analyzer_observations(existing_state, observations)
    new_state = existing_state.model_copy(update={"analyzer_observations": merged})
    apply_design_state_to_project(project, new_state)
    return new_state


def apply_design_state_to_project(
    project: Any,
    new_state: InstrumentProjectData,
) -> None:
    """
    Write InstrumentProjectData back into the Project ORM object.

    Keeps project.instrument_type in sync with the design state.
    Caller is responsible for session.commit().
    """
    project.data = serialize_design_state(new_state)
    # Keep the top-level instrument_type column in sync
    if new_state.instrument_type:
        project.instrument_type = new_state.instrument_type.value
    project.updated_at = datetime.now(timezone.utc)


def create_default_design_state(
    instrument_type: str,
    scale_length_mm: Optional[float] = None,
) -> InstrumentProjectData:
    """
    Create a minimal default InstrumentProjectData for a new project.

    Used when a project is created without an initial design state.
    """
    from ..schemas.instrument_project import InstrumentCategory, InstrumentSpec

    # Map string to enum safely
    try:
        category = InstrumentCategory(instrument_type)
    except ValueError:
        category = InstrumentCategory.CUSTOM

    # Sensible defaults per instrument type
    defaults = {
        InstrumentCategory.ACOUSTIC_GUITAR: (645.0, 20, 43.0, 56.0, 1.0, 14),
        InstrumentCategory.ELECTRIC_GUITAR:  (648.0, 22, 42.0, 56.0, 0.0, 14),
        InstrumentCategory.BASS:             (864.0, 21, 38.0, 60.0, 0.0, 14),
        InstrumentCategory.CLASSICAL:        (650.0, 19, 52.0, 56.0, 1.5, 12),
        InstrumentCategory.VIOLIN:           (328.0, 0,  24.0, 30.0, 0.0, 0),
        InstrumentCategory.UKULELE:          (349.0, 15, 35.0, 42.0, 0.0, 12),
        InstrumentCategory.MANDOLIN:         (356.0, 19, 27.0, 33.0, 0.0, 12),
        InstrumentCategory.ARCHTOP:          (648.0, 20, 43.0, 58.0, 3.0, 14),
    }

    sl, fc, nw, hw, na, bjf = defaults.get(
        category,
        (648.0, 22, 42.0, 56.0, 0.0, 14),  # custom / unknown
    )

    return InstrumentProjectData(
        schema_version=CURRENT_SCHEMA_VERSION,
        instrument_type=category,
        spec=InstrumentSpec(
            scale_length_mm=scale_length_mm or sl,
            fret_count=fc,
            nut_width_mm=nw,
            heel_width_mm=hw,
            neck_angle_degrees=na,
            body_join_fret=bjf,
        ),
    )
