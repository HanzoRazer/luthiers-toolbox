# services/api/app/projects/model_seeding.py
"""
Model-seeding helpers for InstrumentProjectData (GEN-1, GEN-2).

Extracted from service.py to keep that module under the 500-line gate.
Public API:
    create_design_state_from_model_id(model_id) -> Optional[InstrumentProjectData]

Internal helpers:
    _build_body_config_from_model(model_id, model_info, category_value) -> BodyConfig
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..schemas.instrument_project import BodyConfig, InstrumentProjectData

from ..schemas.instrument_project import CURRENT_SCHEMA_VERSION


def create_design_state_from_model_id(model_id: str) -> "Optional[InstrumentProjectData]":
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
    except Exception:  # audited: project-save-fallback
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
