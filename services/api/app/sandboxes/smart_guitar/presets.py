"""
Smart Guitar Presets (SG-SBX-0.1)
=================================

Standard component configurations for headed and headless variants.
"""

from __future__ import annotations

from .schemas import (
    BBox3D,
    Clearance,
    ElectronicsComponent,
    ModelVariant,
    Mounting,
    SmartGuitarSpec,
)


def _standard_components() -> list[ElectronicsComponent]:
    """
    Standard electronics stack: Pi5 + Arduino Uno R4 + DAC+ADC + Battery + Fan.
    
    These are the required components for the v0.1 Smart Guitar.
    """
    return [
        ElectronicsComponent(
            id="pi5",
            name="Raspberry Pi 5",
            bbox=BBox3D(w_mm=85.0, d_mm=56.0, h_mm=18.0),
            clearance=Clearance(margin_mm=4.0, cable_bend_mm=10.0),
            mounting=Mounting(plane="pod_floor", fastener="m3", standoff_mm=6.0),
            notes=["Keep USB/HDMI clearance; prefer side access via pod lid."],
        ),
        ElectronicsComponent(
            id="arduino_uno_r4",
            name="Arduino Uno R4",
            bbox=BBox3D(w_mm=68.6, d_mm=53.4, h_mm=18.0),
            clearance=Clearance(margin_mm=3.0, cable_bend_mm=8.0),
            mounting=Mounting(plane="pod_floor", fastener="m3", standoff_mm=6.0),
            notes=["Treat as I/O coprocessor; isolate from audio traces."],
        ),
        ElectronicsComponent(
            id="hifiberry_dac_adc",
            name="HiFiBerry DAC+ADC (HAT)",
            bbox=BBox3D(w_mm=65.0, d_mm=56.0, h_mm=24.0),
            clearance=Clearance(margin_mm=4.0, cable_bend_mm=10.0),
            mounting=Mounting(plane="pod_floor", fastener="standoff", standoff_mm=10.0),
            notes=["Account for stacking height; ensure lid clearance."],
        ),
        ElectronicsComponent(
            id="battery_pack",
            name="Battery Pack + BMS",
            bbox=BBox3D(w_mm=80.0, d_mm=45.0, h_mm=18.0),
            clearance=Clearance(margin_mm=5.0, cable_bend_mm=12.0),
            mounting=Mounting(plane="body_floor", fastener="wood_screw", standoff_mm=0.0),
            notes=["Default placement: bass chamber; route power via spine channel."],
        ),
        ElectronicsComponent(
            id="fan_40mm",
            name="40mm Fan (lid mount)",
            bbox=BBox3D(w_mm=40.0, d_mm=40.0, h_mm=10.0),
            clearance=Clearance(margin_mm=2.0, cable_bend_mm=6.0),
            mounting=Mounting(plane="pod_lid", fastener="m3", standoff_mm=0.0),
            notes=["Requires vents; otherwise warn (v0.1)."],
        ),
    ]


def standard_headed() -> SmartGuitarSpec:
    """Create a standard headed Smart Guitar spec with all required components."""
    spec = SmartGuitarSpec()
    spec.model_variant = ModelVariant.headed
    spec.electronics = _standard_components()
    return spec


def standard_headless() -> SmartGuitarSpec:
    """
    Create a standard headless Smart Guitar spec with all required components.
    
    Note: Headless-specific notes (bridge hardware keep-outs, etc.) to be added later.
    """
    spec = SmartGuitarSpec()
    spec.model_variant = ModelVariant.headless
    spec.electronics = _standard_components()
    return spec


def standard_all() -> dict[str, SmartGuitarSpec]:
    """Get all standard preset variants."""
    return {
        "headed": standard_headed(),
        "headless": standard_headless(),
    }
