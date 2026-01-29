"""
Smart Guitar DXF Templates Registry (SG-SBX-0.1)
=================================================

This module provides access to Smart Guitar cavity templates.
Each template is a DXF file with LWPOLYLINE geometry.

Template Categories:
- Hollow chambers (bass, treble, tail)
- Electronics pod (RH/LH variants)
- Component brackets (pi5, arduino, hifiberry, battery, fan)
- Wire channels (routes, drill passages)
- Pickup cavities (humbucker neck/bridge)
- Control cavity
"""

from pathlib import Path
from typing import Dict, Any

TEMPLATES_DIR = Path(__file__).parent

# Template registry with dimensions and metadata
SMART_GUITAR_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # Hollow chambers
    "cavity_bass_main_v1": {
        "file": "cavity_bass_main_v1.dxf",
        "layer": "CAVITY_BASS",
        "width_mm": 120.0,
        "height_mm": 180.0,
        "corner_radius_mm": 15.0,
        "category": "hollow_chamber",
        "notes": "Bass-side main hollow chamber",
    },
    "cavity_treble_main_v1": {
        "file": "cavity_treble_main_v1.dxf",
        "layer": "CAVITY_TREBLE",
        "width_mm": 120.0,
        "height_mm": 180.0,
        "corner_radius_mm": 15.0,
        "category": "hollow_chamber",
        "notes": "Treble-side main hollow chamber",
    },
    "cavity_tail_wing_v1": {
        "file": "cavity_tail_wing_v1.dxf",
        "layer": "CAVITY_TAIL",
        "width_mm": 80.0,
        "height_mm": 100.0,
        "corner_radius_mm": 10.0,
        "category": "hollow_chamber",
        "notes": "Tail wing hollow chamber",
    },

    # Electronics pod
    "pod_rh_v1": {
        "file": "pod_rh_v1.dxf",
        "layer": "POD_CAVITY",
        "width_mm": 100.0,
        "height_mm": 140.0,
        "corner_radius_mm": 8.0,
        "category": "electronics_pod",
        "handedness": "RH",
        "notes": "Right-handed electronics bay",
    },
    "pod_lh_v1": {
        "file": "pod_lh_v1.dxf",
        "layer": "POD_CAVITY",
        "width_mm": 100.0,
        "height_mm": 140.0,
        "corner_radius_mm": 8.0,
        "category": "electronics_pod",
        "handedness": "LH",
        "notes": "Left-handed electronics bay",
    },

    # Component brackets
    "bracket_pi5_v1": {
        "file": "bracket_pi5_v1.dxf",
        "layer": "BRACKET",
        "width_mm": 93.0,
        "height_mm": 64.0,
        "category": "bracket",
        "component": "pi5",
        "notes": "Raspberry Pi 5 mounting bracket (85x56 + 8mm clearance)",
    },
    "bracket_arduino_uno_r4_v1": {
        "file": "bracket_arduino_uno_r4_v1.dxf",
        "layer": "BRACKET",
        "width_mm": 75.0,
        "height_mm": 60.0,
        "category": "bracket",
        "component": "arduino_uno_r4",
        "notes": "Arduino Uno R4 mounting bracket (68.6x53.4 + clearance)",
    },
    "bracket_hifiberry_dac_adc_v1": {
        "file": "bracket_hifiberry_dac_adc_v1.dxf",
        "layer": "BRACKET",
        "width_mm": 73.0,
        "height_mm": 64.0,
        "category": "bracket",
        "component": "hifiberry_dac_adc",
        "notes": "HiFiBerry DAC+ADC mounting bracket (65x56 + clearance)",
    },
    "bracket_battery_pack_v1": {
        "file": "bracket_battery_pack_v1.dxf",
        "layer": "BRACKET",
        "width_mm": 90.0,
        "height_mm": 55.0,
        "category": "bracket",
        "component": "battery_pack",
        "notes": "Battery pack mounting bracket (80x45 + clearance)",
    },
    "bracket_fan_40mm_v1": {
        "file": "bracket_fan_40mm_v1.dxf",
        "layer": "BRACKET",
        "width_mm": 44.0,
        "height_mm": 44.0,
        "category": "bracket",
        "component": "fan_40mm",
        "notes": "40mm fan mounting bracket",
    },

    # Wire channels
    "wire_routes_rh_v1": {
        "file": "wire_routes_rh_v1.dxf",
        "layer": "WIRE_CHANNEL",
        "width_mm": 6.35,
        "height_mm": 150.0,
        "category": "wire_channel",
        "handedness": "RH",
        "notes": "Right-handed wire routing channel (1/4 inch wide)",
    },
    "wire_routes_lh_v1": {
        "file": "wire_routes_lh_v1.dxf",
        "layer": "WIRE_CHANNEL",
        "width_mm": 6.35,
        "height_mm": 150.0,
        "category": "wire_channel",
        "handedness": "LH",
        "notes": "Left-handed wire routing channel (1/4 inch wide)",
    },
    "drill_passages_rh_v1": {
        "file": "drill_passages_rh_v1.dxf",
        "layer": "DRILL_PASSAGE",
        "width_mm": 6.35,
        "height_mm": 80.0,
        "category": "drill_passage",
        "handedness": "RH",
        "notes": "Right-handed drill passage template",
    },
    "drill_passages_lh_v1": {
        "file": "drill_passages_lh_v1.dxf",
        "layer": "DRILL_PASSAGE",
        "width_mm": 6.35,
        "height_mm": 80.0,
        "category": "drill_passage",
        "handedness": "LH",
        "notes": "Left-handed drill passage template",
    },

    # Pickup cavities
    "pickup_humbucker_neck_v1": {
        "file": "pickup_humbucker_neck_v1.dxf",
        "layer": "PICKUP_CAVITY",
        "width_mm": 82.0,
        "height_mm": 38.0,
        "corner_radius_mm": 4.0,
        "category": "pickup_cavity",
        "position": "neck",
        "notes": "Standard humbucker neck pickup cavity",
    },
    "pickup_humbucker_bridge_v1": {
        "file": "pickup_humbucker_bridge_v1.dxf",
        "layer": "PICKUP_CAVITY",
        "width_mm": 82.0,
        "height_mm": 38.0,
        "corner_radius_mm": 4.0,
        "category": "pickup_cavity",
        "position": "bridge",
        "notes": "Standard humbucker bridge pickup cavity",
    },

    # Control cavity
    "control_cavity_lp_v1": {
        "file": "control_cavity_lp_v1.dxf",
        "layer": "CONTROL_CAVITY",
        "width_mm": 85.0,
        "height_mm": 55.0,
        "corner_radius_mm": 6.0,
        "category": "control_cavity",
        "notes": "Les Paul style control cavity",
    },
}


def get_template_path(template_id: str) -> Path:
    """Get the full path to a template DXF file."""
    if template_id not in SMART_GUITAR_TEMPLATES:
        raise KeyError(f"Unknown template: {template_id}")
    return TEMPLATES_DIR / SMART_GUITAR_TEMPLATES[template_id]["file"]


def get_template_info(template_id: str) -> Dict[str, Any]:
    """Get metadata for a template."""
    if template_id not in SMART_GUITAR_TEMPLATES:
        raise KeyError(f"Unknown template: {template_id}")
    return SMART_GUITAR_TEMPLATES[template_id].copy()


def list_templates(category: str = None) -> Dict[str, Dict[str, Any]]:
    """List all templates, optionally filtered by category."""
    if category is None:
        return SMART_GUITAR_TEMPLATES.copy()
    return {
        k: v for k, v in SMART_GUITAR_TEMPLATES.items()
        if v.get("category") == category
    }
