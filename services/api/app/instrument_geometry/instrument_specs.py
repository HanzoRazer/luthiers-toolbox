"""
Instrument Specs — Canonical Body Dimension Reference
======================================================

Single source of truth for instrument body dimensions used by:
- Scale validation gate (blueprint vectorizer)
- Photo vectorizer calibration
- Curvature profiler zone thresholds

Consolidates data from:
- body_dimension_reference.json (18 specs, body landmarks)
- INSTRUMENT_SPECS in photo_vectorizer_v2.py (7 specs, feature routes)

All dimensions in millimeters.

Author: Production Shop
Date: 2026-04-14
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any


@dataclass(frozen=True)
class BodyDimensions:
    """Body landmark dimensions for scale validation and curvature analysis."""
    body_length_mm: float           # Total body length heel to tail
    upper_bout_width_mm: float      # Maximum width in upper third
    waist_width_mm: float           # Minimum width at body waist
    lower_bout_width_mm: float      # Maximum width in lower half
    waist_y_norm: float = 0.45      # Waist position as fraction of body length (0-1)
    family: str = "unknown"         # Instrument family for family-hint matching


@dataclass(frozen=True)
class FeatureRoutes:
    """Pocket/route dimensions for feature classification."""
    neck_pocket: Optional[Tuple[float, float]] = None       # (width, depth) mm
    pickup_routes: Optional[List[Tuple[float, float]]] = None  # [(width, height), ...]
    bridge_route: Optional[Tuple[float, float]] = None      # (width, height) mm
    control_cavity: Optional[Tuple[float, float]] = None    # (width, height) mm
    soundhole: Optional[Tuple[float, float]] = None         # (width, height) mm
    f_holes: Optional[List[Tuple[float, float]]] = None     # [(length, width), ...]


@dataclass(frozen=True)
class InstrumentSpec:
    """Complete instrument specification."""
    name: str
    body: BodyDimensions
    features: Optional[FeatureRoutes] = None
    note: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# BODY DIMENSIONS — from body_dimension_reference.json
# ─────────────────────────────────────────────────────────────────────────────

BODY_DIMENSIONS: Dict[str, BodyDimensions] = {
    "stratocaster": BodyDimensions(
        body_length_mm=406,
        upper_bout_width_mm=311,
        waist_width_mm=308,
        lower_bout_width_mm=408,
        waist_y_norm=0.47,
        family="solid_body",
    ),
    "telecaster": BodyDimensions(
        body_length_mm=406,
        upper_bout_width_mm=311,
        waist_width_mm=310,
        lower_bout_width_mm=398,
        waist_y_norm=0.46,
        family="solid_body",
    ),
    "les_paul": BodyDimensions(
        body_length_mm=450,
        upper_bout_width_mm=283,
        waist_width_mm=266,
        lower_bout_width_mm=340,
        waist_y_norm=0.44,
        family="solid_body",
    ),
    "es335": BodyDimensions(
        body_length_mm=500,
        upper_bout_width_mm=375,
        waist_width_mm=295,
        lower_bout_width_mm=420,
        waist_y_norm=0.43,
        family="archtop",
    ),
    "dreadnought": BodyDimensions(
        body_length_mm=520,
        upper_bout_width_mm=292,
        waist_width_mm=241,
        lower_bout_width_mm=381,
        waist_y_norm=0.43,
        family="acoustic",
    ),
    "om_000": BodyDimensions(
        body_length_mm=476,
        upper_bout_width_mm=274,
        waist_width_mm=228,
        lower_bout_width_mm=341,
        waist_y_norm=0.44,
        family="acoustic",
    ),
    "jumbo": BodyDimensions(
        body_length_mm=521,
        upper_bout_width_mm=320,
        waist_width_mm=272,
        lower_bout_width_mm=419,
        waist_y_norm=0.43,
        family="acoustic",
    ),
    "smart_guitar": BodyDimensions(
        body_length_mm=444.5,
        upper_bout_width_mm=310,
        waist_width_mm=307,
        lower_bout_width_mm=368.3,
        waist_y_norm=0.46,
        family="solid_body",
    ),
    "jumbo_archtop": BodyDimensions(
        body_length_mm=520,
        upper_bout_width_mm=340,
        waist_width_mm=248,
        lower_bout_width_mm=432,
        waist_y_norm=0.42,
        family="archtop",
    ),
    "classical": BodyDimensions(
        body_length_mm=481,
        upper_bout_width_mm=280,
        waist_width_mm=225,
        lower_bout_width_mm=365,
        waist_y_norm=0.45,
        family="acoustic",
    ),
    "j45": BodyDimensions(
        body_length_mm=506,
        upper_bout_width_mm=295,
        waist_width_mm=248,
        lower_bout_width_mm=394,
        waist_y_norm=0.44,
        family="acoustic",
    ),
    "flying_v": BodyDimensions(
        body_length_mm=450,
        upper_bout_width_mm=380,
        waist_width_mm=200,
        lower_bout_width_mm=410,
        waist_y_norm=0.52,
        family="solid_body",
    ),
    "bass_4string": BodyDimensions(
        body_length_mm=430,
        upper_bout_width_mm=310,
        waist_width_mm=280,
        lower_bout_width_mm=370,
        waist_y_norm=0.45,
        family="bass",
    ),
    "gibson_sg": BodyDimensions(
        body_length_mm=444,
        upper_bout_width_mm=330,
        waist_width_mm=180,
        lower_bout_width_mm=330,
        waist_y_norm=0.35,
        family="solid_body",
    ),
    "benedetto_17": BodyDimensions(
        body_length_mm=482.6,
        upper_bout_width_mm=279.4,
        waist_width_mm=228.6,
        lower_bout_width_mm=431.8,
        waist_y_norm=0.42,
        family="archtop",
    ),
    "gibson_explorer": BodyDimensions(
        body_length_mm=460,
        upper_bout_width_mm=410,
        waist_width_mm=200,
        lower_bout_width_mm=475,
        waist_y_norm=0.50,
        family="solid_body",
    ),
    "cuatro": BodyDimensions(
        body_length_mm=375,
        upper_bout_width_mm=180,
        waist_width_mm=155,
        lower_bout_width_mm=260,
        waist_y_norm=0.44,
        family="acoustic",
    ),
    "melody_maker": BodyDimensions(
        body_length_mm=440,
        upper_bout_width_mm=280,
        waist_width_mm=260,
        lower_bout_width_mm=330,
        waist_y_norm=0.45,
        family="solid_body",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ROUTES — from INSTRUMENT_SPECS in photo_vectorizer_v2.py
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_ROUTES: Dict[str, FeatureRoutes] = {
    "stratocaster": FeatureRoutes(
        neck_pocket=(56.0, 76.0),
        pickup_routes=[(85.0, 35.0)],
        bridge_route=(89.0, 42.0),
        control_cavity=(120.0, 80.0),
    ),
    "telecaster": FeatureRoutes(
        neck_pocket=(56.0, 76.0),
        pickup_routes=[(85.0, 35.0), (71.5, 38.0)],
        bridge_route=(92.0, 25.0),
        control_cavity=(100.0, 70.0),
    ),
    "les_paul": FeatureRoutes(
        neck_pocket=(62.0, 82.0),
        pickup_routes=[(71.5, 38.0), (71.5, 38.0)],
        bridge_route=(120.0, 25.0),
        control_cavity=(130.0, 90.0),
    ),
    "es335": FeatureRoutes(
        pickup_routes=[(71.5, 38.0)],
        f_holes=[(160.0, 45.0)],
        bridge_route=(120.0, 25.0),
        control_cavity=(120.0, 80.0),
    ),
    "dreadnought": FeatureRoutes(
        soundhole=(100.0, 100.0),
        bridge_route=(180.0, 30.0),
    ),
    "smart_guitar": FeatureRoutes(
        neck_pocket=(56.0, 76.0),
        pickup_routes=[(85.0, 35.0)],
        bridge_route=(100.0, 40.0),
        control_cavity=(120.0, 80.0),
    ),
    "jumbo_archtop": FeatureRoutes(
        f_holes=[(160.0, 45.0)],
        bridge_route=(130.0, 30.0),
        pickup_routes=[(71.5, 38.0)],
        control_cavity=(120.0, 80.0),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE OBJECTS — for photo calibration
# ─────────────────────────────────────────────────────────────────────────────

REFERENCE_OBJECTS: Dict[str, Tuple[float, float]] = {
    "us_quarter": (24.26, 24.26),
    "credit_card": (85.6, 53.98),
    "business_card": (88.9, 50.8),
}


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE ACCESSORS
# ─────────────────────────────────────────────────────────────────────────────

def get_body_dimensions(spec_name: str) -> Optional[BodyDimensions]:
    """
    Get body dimensions for an instrument spec.

    Args:
        spec_name: Instrument name (case-insensitive, underscores accepted)

    Returns:
        BodyDimensions or None if not found
    """
    key = spec_name.lower().replace("-", "_").replace(" ", "_")
    return BODY_DIMENSIONS.get(key)


def get_feature_routes(spec_name: str) -> Optional[FeatureRoutes]:
    """
    Get feature routes for an instrument spec.

    Returns None for instruments without defined routes.
    """
    key = spec_name.lower().replace("-", "_").replace(" ", "_")
    return FEATURE_ROUTES.get(key)


def get_spec(spec_name: str) -> Optional[InstrumentSpec]:
    """
    Get complete instrument spec (body + features).
    """
    body = get_body_dimensions(spec_name)
    if body is None:
        return None
    features = get_feature_routes(spec_name)
    return InstrumentSpec(
        name=spec_name.lower().replace("-", "_").replace(" ", "_"),
        body=body,
        features=features,
    )


def list_specs() -> List[str]:
    """Return list of all available spec names."""
    return sorted(BODY_DIMENSIONS.keys())


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY COMPAT — for photo_vectorizer_v2.py transition
# ─────────────────────────────────────────────────────────────────────────────

def get_legacy_instrument_specs() -> Dict[str, Dict[str, Any]]:
    """
    Return INSTRUMENT_SPECS in the legacy format expected by photo_vectorizer_v2.py.

    Format: {"name": {"body": (length_mm, width_mm), "features": {...}}}

    This function allows photo_vectorizer_v2.py to import from this module
    instead of maintaining a separate INSTRUMENT_SPECS dict.
    """
    specs: Dict[str, Dict[str, Any]] = {}

    for name, body in BODY_DIMENSIONS.items():
        entry: Dict[str, Any] = {
            "body": (body.body_length_mm, body.lower_bout_width_mm),
        }

        features = FEATURE_ROUTES.get(name)
        if features:
            feat_dict: Dict[str, Any] = {}
            if features.neck_pocket:
                feat_dict["neck_pocket"] = features.neck_pocket
            if features.pickup_routes:
                feat_dict["pickup_route"] = features.pickup_routes
            if features.bridge_route:
                feat_dict["bridge_route"] = features.bridge_route
            if features.control_cavity:
                feat_dict["control_cavity"] = features.control_cavity
            if features.soundhole:
                feat_dict["soundhole"] = features.soundhole
            if features.f_holes:
                feat_dict["f_hole"] = features.f_holes
            if feat_dict:
                entry["features"] = feat_dict

        specs[name] = entry

    # Add reference objects
    specs["reference_objects"] = dict(REFERENCE_OBJECTS)

    return specs


# Legacy alias
INSTRUMENT_SPECS = get_legacy_instrument_specs()
