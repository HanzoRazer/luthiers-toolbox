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

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError

from ..schemas.instrument_project import (
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
