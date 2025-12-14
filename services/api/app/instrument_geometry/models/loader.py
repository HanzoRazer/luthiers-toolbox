"""
loader.py

Instrument model loader for ToolBox / RMOS.

Responsibilities:
- Discover available instrument model JSON files.
- Load a preset by model_id (e.g. "benedetto_17").
- Convert inches (JSON) → mm (via specs.py helpers).
- Produce a typed GuitarModelSpec instance.

Wave 19 Module - Fan-Fret CAM Foundation
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .specs import (
    GuitarModelSpec,
    ScaleSpec,
    MultiScaleSpec,
    NeckJointSpec,
    BridgeSpec,
    StringSpec,
    StringSetSpec,
    DXFMappingSpec,
    inch_to_mm,
)

# Constants for __init__.py re-export
INCH_TO_MM = 25.4
MM_TO_INCH = 1.0 / 25.4


# ---------------------------------------------------------------------------
# Paths / discovery
# ---------------------------------------------------------------------------


MODELS_DIR = Path(__file__).parent  # directory containing *.json presets
REGISTRY_FILE = MODELS_DIR / "instrument_models.json"


def list_model_files() -> List[Path]:
    """
    Discover all .json preset files in models directory.
    
    Returns:
        List of Path objects for .json files (excluding registry)
    """
    if not MODELS_DIR.exists():
        return []
    
    return [
        p for p in MODELS_DIR.glob("*.json")
        if p.name != "instrument_models.json"  # Exclude registry
    ]


def list_available_model_ids() -> List[str]:
    """
    List all available model IDs from JSON presets.
    
    Returns:
        List of model_id strings (e.g., ["benedetto_17", "strat_25_5"])
    """
    model_files = list_model_files()
    model_ids = []
    
    for path in model_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "model_id" in data:
                    model_ids.append(data["model_id"])
        except (json.JSONDecodeError, KeyError):
            continue  # Skip malformed files
    
    return sorted(model_ids)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_model_json(model_id: str) -> Dict:
    """
    Load raw JSON data for a model.
    
    Args:
        model_id: Model identifier (e.g., "benedetto_17")
        
    Returns:
        Dict of raw JSON data
        
    Raises:
        FileNotFoundError: If model JSON doesn't exist
    """
    json_path = MODELS_DIR / f"{model_id}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Model preset not found: {model_id}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_multiscale_spec(scale_data: Dict) -> Optional[MultiScaleSpec]:
    """Load multiscale specification if present."""
    ms_data = scale_data.get("multiscale")
    if not ms_data:
        return None

    return MultiScaleSpec(
        bass_scale_length_in=float(ms_data["bass_scale_length_in"]),
        treble_scale_length_in=float(ms_data["treble_scale_length_in"]),
        fan_start_fret=int(ms_data["fan_start_fret"]),
    )


def _load_scale_spec(scale_data: Dict) -> ScaleSpec:
    """Load scale specification."""
    ms = _load_multiscale_spec(scale_data)

    return ScaleSpec(
        scale_length_in=float(scale_data["scale_length_in"]),
        num_frets=int(scale_data["num_frets"]),
        joint_fret=(
            int(scale_data["joint_fret"])
            if "joint_fret" in scale_data and scale_data["joint_fret"] is not None
            else None
        ),
        fingerboard_overhang_frets=int(scale_data.get("fingerboard_overhang_frets", 0)),
        multiscale=ms,
    )


def _load_neck_joint_spec(data: Dict) -> Optional[NeckJointSpec]:
    """Load neck joint specification if present."""
    nj = data.get("neck_joint")
    if not nj:
        return None

    return NeckJointSpec(
        type=str(nj["type"]),
        body_join_fret=int(nj["body_join_fret"]),
        pocket_depth_in=float(nj["pocket_depth_in"]),
        pocket_length_in=float(nj["pocket_length_in"]),
        pocket_width_in=float(nj["pocket_width_in"]),
        heel_thickness_in=float(nj["heel_thickness_in"]),
        neck_angle_degrees=float(nj["neck_angle_degrees"]),
    )


def _load_bridge_spec(data: Dict) -> Optional[BridgeSpec]:
    """Load bridge specification if present."""
    b = data.get("bridge")
    if not b:
        return None

    return BridgeSpec(
        type=str(b["type"]),
        reference_line=str(b.get("reference_line", "theoretical_scale_length")),
        saddle_profile=b.get("saddle_profile"),
        base_offset_in=float(b.get("base_offset_in", 0.0)),
    )


def _load_string_set_spec(data: Dict) -> Optional[StringSetSpec]:
    """Load string set specification if present."""
    ss = data.get("string_set")
    if not ss:
        return None

    strings: List[StringSpec] = []
    for s in ss.get("strings", []):
        strings.append(
            StringSpec(
                index=int(s["index"]),
                name=str(s["name"]),
                gauge_in=float(s["gauge_in"]),
                wound=bool(s.get("wound", False)),
            )
        )

    return StringSetSpec(
        string_set_id=str(ss["string_set_id"]),
        description=str(ss.get("description", "")),
        strings=strings,
    )


def _load_dxf_mapping_spec(data: Dict) -> Optional[DXFMappingSpec]:
    """Load DXF mapping specification if present."""
    d = data.get("dxf_mappings")
    if not d:
        return None

    return DXFMappingSpec(
        body_outline_id=d.get("body_outline_id"),
        fretboard_outline_id=d.get("fretboard_outline_id"),
        bridge_footprint_id=d.get("bridge_footprint_id"),
    )


def _load_reference_comp_mm(
    data: Dict, scale_length_in: float
) -> Dict[int, float]:
    """
    Convert reference_compensation from inches to mm if present.

    JSON:
        "reference_compensation_in": { "1": 0.048, "2": 0.060, ... }

    Loader:
        converts to mm and stores as Dict[int, float].
    """
    result: Dict[int, float] = {}
    comp_in = data.get("reference_compensation_in") or {}
    for key, value in comp_in.items():
        try:
            idx = int(key)
            comp_mm = inch_to_mm(float(value))
            result[idx] = comp_mm
        except (ValueError, TypeError):
            continue
    return result


def load_model_spec(model_id: str) -> GuitarModelSpec:
    """
    High-level loader: JSON → GuitarModelSpec.

    JSON is assumed to be inches-only for linear dimensions.
    This function handles all inch→mm conversion via the
    dataclass properties and helper functions.
    """
    raw = load_model_json(model_id)

    model_id_value = str(raw["model_id"])
    display_name = str(raw.get("display_name", model_id_value))
    description = str(raw.get("description", ""))

    scale_data = raw["scale"]
    scale_spec = _load_scale_spec(scale_data)

    neck_joint_spec = _load_neck_joint_spec(raw)
    bridge_spec = _load_bridge_spec(raw)
    string_set_spec = _load_string_set_spec(raw)
    dxf_spec = _load_dxf_mapping_spec(raw)

    reference_comp_mm = _load_reference_comp_mm(
        raw,
        scale_length_in=scale_spec.scale_length_in,
    )

    notes = [str(n) for n in raw.get("notes", [])]

    return GuitarModelSpec(
        model_id=model_id_value,
        display_name=display_name,
        description=description,
        scale=scale_spec,
        neck_joint=neck_joint_spec,
        bridge=bridge_spec,
        string_set=string_set_spec,
        reference_compensation_mm=reference_comp_mm,
        dxf_mappings=dxf_spec,
        notes=notes,
    )
