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
    BodyConfig,
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


def create_design_state_from_model_id(model_id: str) -> Optional[InstrumentProjectData]:
    """
    Create InstrumentProjectData seeded from a guitar model spec (GEN-1).

    When model_id is provided to POST /api/projects, this function looks up
    the canonical spec for that model and creates accurate defaults.

    Args:
        model_id: String model identifier (e.g., "stratocaster", "les_paul", "dreadnought")

    Returns:
        InstrumentProjectData with model-accurate defaults, or None if model not found.

    Example:
        >>> state = create_design_state_from_model_id("stratocaster")
        >>> state.spec.scale_length_mm
        648.0
        >>> state.spec.fret_count
        22
    """
    from ..schemas.instrument_project import BodyConfig, InstrumentCategory, InstrumentSpec

    # Direct mapping of model_id to (get_spec_fn, MODEL_INFO dict)
    # This avoids the circular import issues with InstrumentModelId enum
    MODEL_LOADERS = {}
    
    try:
        from ..instrument_geometry.guitars import strat, tele, les_paul, dreadnought
        from ..instrument_geometry.guitars import om_000, j_45, jazz_bass, classical
        from ..instrument_geometry.guitars import archtop, prs, sg, jumbo_j200, ukulele
        from ..instrument_geometry.guitars import gibson_l_00, flying_v, es_335
        from ..instrument_geometry.guitars import explorer, firebird, moderne
        
        MODEL_LOADERS = {
            "stratocaster": (strat.get_spec, strat.MODEL_INFO),
            "telecaster": (tele.get_spec, tele.MODEL_INFO),
            "les_paul": (les_paul.get_spec, les_paul.MODEL_INFO),
            "dreadnought": (dreadnought.get_spec, dreadnought.MODEL_INFO),
            "om_000": (om_000.get_spec, om_000.MODEL_INFO),
            "j_45": (j_45.get_spec, j_45.MODEL_INFO),
            "jazz_bass": (jazz_bass.get_spec, jazz_bass.MODEL_INFO),
            "classical": (classical.get_spec, classical.MODEL_INFO),
            "archtop": (archtop.get_spec, archtop.MODEL_INFO),
            "prs": (prs.get_spec, prs.MODEL_INFO),
            "sg": (sg.get_spec, sg.MODEL_INFO),
            "jumbo_j200": (jumbo_j200.get_spec, jumbo_j200.MODEL_INFO),
            "ukulele": (ukulele.get_spec, ukulele.MODEL_INFO),
            "gibson_l_00": (gibson_l_00.get_spec, gibson_l_00.MODEL_INFO),
            "flying_v": (flying_v.get_spec, flying_v.MODEL_INFO),
            "es_335": (es_335.get_spec, es_335.MODEL_INFO),
            "explorer": (explorer.get_spec, explorer.MODEL_INFO),
            "firebird": (firebird.get_spec, firebird.MODEL_INFO),
            "moderne": (moderne.get_spec, moderne.MODEL_INFO),
        }
    except ImportError:
        return None

    if model_id not in MODEL_LOADERS:
        return None

    get_spec_fn, model_info = MODEL_LOADERS[model_id]
    
    try:
        model_spec = get_spec_fn()
    except Exception:
        return None

    # Determine category from model info
    category_value = model_info.get("category", "electric_guitar")
    try:
        category = InstrumentCategory(category_value)
    except ValueError:
        category = InstrumentCategory.ELECTRIC_GUITAR

    # Build InstrumentSpec (pydantic) from model data
    spec = InstrumentSpec(
        scale_length_mm=model_spec.scale_length_mm,
        fret_count=model_spec.fret_count,
        string_count=model_spec.string_count,
        nut_width_mm=model_info.get("nut_width_mm", 43.0),
        heel_width_mm=56.0,
        neck_angle_degrees=0.0 if "electric" in category_value else 1.0,
        body_join_fret=14,
    )

    # Build BodyConfig from model-specific defaults (GEN-2)
    body_config = _build_body_config_from_model(model_id, model_info, category_value)

    return InstrumentProjectData(
        schema_version=CURRENT_SCHEMA_VERSION,
        instrument_type=category,
        spec=spec,
        body_config=body_config,
    )


def _build_body_config_from_model(
    model_id: str,
    model_info: dict,
    category_value: str,
) -> "BodyConfig":
    """
    Build BodyConfig defaults from model spec (GEN-2).

    Model-specific defaults:
        - stratocaster: pickup_config="sss", tremolo_style="vintage_6screw"
        - telecaster: pickup_config="ss", tremolo_style="hardtail"
        - les_paul: rear_routed=False, pickup_config="hh"
        - dreadnought: acoustic_body_style_id="dreadnought"
        - etc.
    """
    from ..schemas.instrument_project import BodyConfig

    # Model-specific body config defaults
    BODY_CONFIG_DEFAULTS = {
        # Electric guitars
        "stratocaster": {
            "pickup_config": "sss",
            "tremolo_style": "vintage_6screw",
            "belly_contour": True,
            "arm_contour": True,
            "rear_routed": True,
            "body_style_id": "stratocaster",
        },
        "telecaster": {
            "pickup_config": "ss",
            "tremolo_style": "hardtail",
            "belly_contour": False,
            "arm_contour": False,
            "rear_routed": True,
            "body_style_id": "telecaster",
        },
        "les_paul": {
            "pickup_config": "hh",
            "tremolo_style": "hardtail",
            "belly_contour": False,
            "arm_contour": False,
            "rear_routed": False,  # front-routed
            "body_style_id": "les_paul",
        },
        "sg": {
            "pickup_config": "hh",
            "tremolo_style": "hardtail",
            "rear_routed": False,
            "body_style_id": "sg",
        },
        "prs": {
            "pickup_config": "hh",
            "tremolo_style": "2point",
            "belly_contour": True,
            "arm_contour": True,
            "rear_routed": True,
            "body_style_id": "prs",
        },
        "flying_v": {
            "pickup_config": "hh",
            "rear_routed": False,
            "body_style_id": "flying_v",
        },
        "explorer": {
            "pickup_config": "hh",
            "rear_routed": False,
            "body_style_id": "explorer",
        },
        "firebird": {
            "pickup_config": "hh",
            "rear_routed": False,
            "body_style_id": "firebird",
        },
        "moderne": {
            "pickup_config": "hh",
            "rear_routed": False,
            "body_style_id": "moderne",
        },
        "es_335": {
            "pickup_config": "hh",
            "rear_routed": False,
            "body_style_id": "es_335",
        },
        "jazz_bass": {
            "pickup_config": "jj",
            "rear_routed": True,
            "body_style_id": "jazz_bass",
        },
        # Acoustic guitars
        "dreadnought": {
            "acoustic_body_style_id": "dreadnought",
            "belly_contour": False,
            "arm_contour": False,
            "rear_routed": False,
        },
        "om_000": {
            "acoustic_body_style_id": "om",
        },
        "j_45": {
            "acoustic_body_style_id": "round_shoulder",
        },
        "jumbo_j200": {
            "acoustic_body_style_id": "jumbo",
        },
        "gibson_l_00": {
            "acoustic_body_style_id": "parlor",
        },
        "classical": {
            "acoustic_body_style_id": "classical",
        },
        "archtop": {
            "acoustic_body_style_id": "archtop",
        },
        "ukulele": {
            "acoustic_body_style_id": "ukulele",
        },
    }

    defaults = BODY_CONFIG_DEFAULTS.get(model_id, {})

    # Set category-appropriate defaults
    is_acoustic = "acoustic" in category_value or model_id in [
        "dreadnought", "om_000", "j_45", "jumbo_j200", "gibson_l_00",
        "classical", "archtop", "ukulele"
    ]

    return BodyConfig(
        pickup_config=defaults.get("pickup_config"),
        tremolo_style=defaults.get("tremolo_style"),
        belly_contour=defaults.get("belly_contour", not is_acoustic),
        arm_contour=defaults.get("arm_contour", not is_acoustic),
        rear_routed=defaults.get("rear_routed", not is_acoustic),
        stock_thickness_mm=model_info.get("body_thickness_mm"),
        body_style_id=defaults.get("body_style_id"),
        acoustic_body_style_id=defaults.get("acoustic_body_style_id"),
    )



def create_default_design_state(
    instrument_type: str,
    scale_length_mm: Optional[float] = None,
) -> InstrumentProjectData:
    """
    Create a minimal default InstrumentProjectData for a new project.

    Used when a project is created without an initial design state.
    """
    from ..schemas.instrument_project import BodyConfig, InstrumentCategory, InstrumentSpec

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
