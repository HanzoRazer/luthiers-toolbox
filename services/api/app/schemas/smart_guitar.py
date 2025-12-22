"""
Smart Guitar Pydantic Models
============================

Generated from instrument_model_registry.json schema.
Use these models for backend API development.

Version: 1.0.0
Generated: December 22, 2025
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class SmartGuitarStatus(str, Enum):
    COMPLETE = "COMPLETE"
    STUB = "STUB"
    ASSETS_ONLY = "ASSETS_ONLY"


class MidiProtocol(str, Enum):
    USB_MIDI = "USB MIDI"
    BLE_MIDI = "BLE MIDI"
    DIN_MIDI = "DIN MIDI (optional)"


class AudioOutput(str, Enum):
    TRS = '1/4" TRS'
    USB_AUDIO = "USB Audio"
    BLUETOOTH = "Bluetooth A2DP"


class ToolpathType(str, Enum):
    POCKET = "pocket"
    DRILL = "drill"
    CONTOUR = "contour"


class SmartGuitarComponent(str, Enum):
    ELECTRONICS_CAVITY = "electronics_cavity"
    BATTERY = "battery"
    LED_CHANNEL = "led_channel"
    USB_PORT = "usb_port"
    ANTENNA = "antenna"


# =============================================================================
# IoT SUBSYSTEMS
# =============================================================================

class SmartGuitarIoT(BaseModel):
    """IoT hardware specifications."""
    processor: str = "Raspberry Pi 5"
    memory_gb: int = 8
    storage_gb: int = 64
    os: str = "Linux (custom Buildroot)"


class SmartGuitarConnectivity(BaseModel):
    """Connectivity options."""
    bluetooth: str = "BLE 5.0"
    wifi: str = "Wi-Fi 6 (802.11ax)"
    usb: str = "USB-C 3.1"
    midi: List[MidiProtocol] = Field(default_factory=lambda: [
        MidiProtocol.USB_MIDI,
        MidiProtocol.BLE_MIDI,
        MidiProtocol.DIN_MIDI,
    ])


class SmartGuitarAudio(BaseModel):
    """Audio subsystem specifications."""
    adc_bits: Literal[24] = 24
    sample_rate_khz: Literal[48, 96, 192] = 96
    latency_ms: float = 3.0
    dsp: str = "Real-time pitch detection, effects processing"
    outputs: List[AudioOutput] = Field(default_factory=lambda: [
        AudioOutput.TRS,
        AudioOutput.USB_AUDIO,
        AudioOutput.BLUETOOTH,
    ])


class SmartGuitarSensors(BaseModel):
    """Sensor specifications."""
    piezo_pickups: int = 6
    accelerometer: bool = True
    gyroscope: bool = True
    capacitive_touch_frets: bool = True
    pressure_sensitive_strings: bool = False


class SmartGuitarPower(BaseModel):
    """Power system specifications."""
    battery_type: str = "Li-ion 18650"
    capacity_mah: int = 6000
    runtime_hours: int = 8
    charging: str = "USB-C PD 20W"


# =============================================================================
# DAW INTEGRATION
# =============================================================================

class DawPartner(BaseModel):
    """DAW partner integration details."""
    status: Literal["OEM partnership", "integration planned", "community"]
    features: List[str]


class SmartGuitarDawIntegration(BaseModel):
    """DAW integration partnerships."""
    giglad: DawPartner = Field(default_factory=lambda: DawPartner(
        status="OEM partnership",
        features=["Live backing tracks", "AI accompaniment"],
    ))
    pgmusic: DawPartner = Field(default_factory=lambda: DawPartner(
        status="OEM partnership",
        features=["Band-in-a-Box integration", "Chord recognition"],
    ))


# =============================================================================
# CAM FEATURES
# =============================================================================

class SmartGuitarCamFeatures(BaseModel):
    """CAM manufacturing features."""
    electronics_cavity: str = "Custom routed for Pi 5 + battery"
    control_panel: str = "3D printed or CNC aluminum"
    pcb_mounting: str = "M2.5 standoffs, vibration dampened"


class SmartGuitarToolpath(BaseModel):
    """Toolpath definition for CAM operations."""
    name: str
    type: ToolpathType
    description: str
    component: SmartGuitarComponent


# =============================================================================
# CORE MODELS
# =============================================================================

class SmartGuitarSpec(BaseModel):
    """Smart Guitar base specifications."""
    model_id: Literal["smart_guitar"] = "smart_guitar"
    display_name: str = "Smart Guitar"
    category: Literal["electric_guitar"] = "electric_guitar"
    status: SmartGuitarStatus = SmartGuitarStatus.COMPLETE
    scale_length_mm: float = 648.0
    scale_length_inches: float = 25.51
    fret_count: int = 24
    string_count: int = 6
    manufacturer: str = "Luthier's ToolBox"
    year_introduced: int = 2025
    description: str = (
        "IoT-enabled electric guitar with embedded computing, "
        "real-time DSP, and DAW integration"
    )
    features: List[str] = Field(default_factory=lambda: [
        "24-fret neck",
        "6 strings",
        '648.0mm scale (25.51")',
    ])


class SmartGuitarArchitecture(BaseModel):
    """Full architecture specification."""
    hardware: dict = Field(default_factory=lambda: {
        "processor": "Raspberry Pi 5",
        "connectivity": ["Bluetooth LE 5.0", "USB-C", "Wi-Fi 6"],
        "audio": "24-bit ADC with real-time DSP",
        "power": "Li-ion battery with USB-C charging",
    })
    software: dict = Field(default_factory=lambda: {
        "os": "Linux (headless)",
        "daw_integration": ["MIDI over BLE", "OSC", "USB Audio"],
        "temperament_engine": "/api/music/temperament/*",
    })


class SmartGuitarInfo(BaseModel):
    """Full Smart Guitar info response."""
    ok: bool = True
    model_id: Literal["smart"] = "smart"
    display_name: str = "Smart Guitar"
    category: str = "electric_guitar"
    concept: str = "Smart Guitar DAW Bundle"
    description: str = ""
    architecture: SmartGuitarArchitecture = Field(
        default_factory=SmartGuitarArchitecture
    )
    status: str = "Development - requires custom implementation"
    related_endpoints: dict = Field(default_factory=lambda: {
        "spec": "/api/instruments/guitar/smart/spec",
        "bundle": "/api/instruments/guitar/smart/bundle",
        "temperament": "/api/music/temperament/health",
        "cam": "/api/cam/guitar/smart/health",
    })


# =============================================================================
# FULL REGISTRY ENTRY
# =============================================================================

class SmartGuitarRegistryEntry(BaseModel):
    """Complete registry entry matching JSON schema."""
    id: Literal["smart_guitar"] = "smart_guitar"
    display_name: str = "Smart Guitar"
    status: SmartGuitarStatus = SmartGuitarStatus.COMPLETE
    category: Literal["electric_guitar"] = "electric_guitar"
    scale_length_mm: float = 648.0
    fret_count: int = 24
    string_count: int = 6
    description: str = (
        "IoT-enabled electric guitar with embedded computing, "
        "real-time DSP, and DAW integration"
    )
    manufacturer: str = "Luthier's ToolBox"
    year_introduced: int = 2025
    body_style: str = "stratocaster_derivative"
    iot: SmartGuitarIoT = Field(default_factory=SmartGuitarIoT)
    connectivity: SmartGuitarConnectivity = Field(
        default_factory=SmartGuitarConnectivity
    )
    audio: SmartGuitarAudio = Field(default_factory=SmartGuitarAudio)
    sensors: SmartGuitarSensors = Field(default_factory=SmartGuitarSensors)
    power: SmartGuitarPower = Field(default_factory=SmartGuitarPower)
    features: List[str] = Field(default_factory=lambda: [
        "Real-time pitch detection",
        "Alternative temperament support (19+ systems)",
        "LED fret markers (RGB addressable)",
        "Onboard effects processing",
        "DAW integration (Giglad, Band-in-a-Box)",
        "Chord recognition",
        "Looper (60s stereo)",
        "Metronome with tap tempo",
        "Tuner (chromatic + temperament-aware)",
        "Wireless audio streaming",
        "MIDI controller mode",
        "Firmware OTA updates",
    ])
    daw_integration: SmartGuitarDawIntegration = Field(
        default_factory=SmartGuitarDawIntegration
    )
    cam_features: SmartGuitarCamFeatures = Field(
        default_factory=SmartGuitarCamFeatures
    )
    assets: List[str] = Field(default_factory=lambda: [
        "smart_guitar/body_outline.dxf",
        "smart_guitar/electronics_cavity.dxf",
        "smart_guitar/control_panel.dxf",
        "smart_guitar/pcb_mounting.dxf",
    ])


# =============================================================================
# API RESPONSE MODELS
# =============================================================================

class SmartGuitarHealthResponse(BaseModel):
    """CAM health check response."""
    ok: bool = True
    subsystem: Literal["smart_guitar_cam"] = "smart_guitar_cam"
    model_id: Literal["smart"] = "smart"
    capabilities: List[str] = Field(default_factory=lambda: [
        "toolpaths",
        "preview",
        "electronics_routing",
    ])
    status: str = "Development - toolpath generation in progress"
    instrument_spec: str = "/api/instruments/guitar/smart/spec"
    temperament_api: str = "/api/music/temperament/health"


class SmartGuitarToolpathsResponse(BaseModel):
    """Toolpath list response."""
    ok: bool = True
    toolpaths: List[SmartGuitarToolpath] = Field(default_factory=list)


class SmartGuitarResource(BaseModel):
    """DAW bundle resource."""
    name: str
    type: Literal["documentation", "oem_correspondence", "instructions", "pdf"]
    path: Optional[str] = None
    description: Optional[str] = None


class SmartGuitarBundleResponse(BaseModel):
    """DAW bundle info response."""
    ok: bool = True
    bundle_version: str = "1.0"
    build_date: str = "2025-10-14"
    resources: List[SmartGuitarResource] = Field(default_factory=list)
    status: str = "Documentation bundle - requires custom implementation"


# =============================================================================
# CONSTANTS
# =============================================================================

SMART_GUITAR_FEATURES: List[str] = [
    "Real-time pitch detection",
    "Alternative temperament support (19+ systems)",
    "LED fret markers (RGB addressable)",
    "Onboard effects processing",
    "DAW integration (Giglad, Band-in-a-Box)",
    "Chord recognition",
    "Looper (60s stereo)",
    "Metronome with tap tempo",
    "Tuner (chromatic + temperament-aware)",
    "Wireless audio streaming",
    "MIDI controller mode",
    "Firmware OTA updates",
]

SMART_GUITAR_COMPONENTS: List[SmartGuitarComponent] = [
    SmartGuitarComponent.ELECTRONICS_CAVITY,
    SmartGuitarComponent.BATTERY,
    SmartGuitarComponent.LED_CHANNEL,
    SmartGuitarComponent.USB_PORT,
    SmartGuitarComponent.ANTENNA,
]

DEFAULT_TOOLPATHS: List[SmartGuitarToolpath] = [
    SmartGuitarToolpath(
        name="Electronics Cavity",
        type=ToolpathType.POCKET,
        description="Pocket for Raspberry Pi 5 and electronics board",
        component=SmartGuitarComponent.ELECTRONICS_CAVITY,
    ),
    SmartGuitarToolpath(
        name="Battery Pocket",
        type=ToolpathType.POCKET,
        description="Li-ion battery compartment",
        component=SmartGuitarComponent.BATTERY,
    ),
    SmartGuitarToolpath(
        name="LED Channel",
        type=ToolpathType.CONTOUR,
        description="Channel for LED strip along fretboard edge",
        component=SmartGuitarComponent.LED_CHANNEL,
    ),
    SmartGuitarToolpath(
        name="USB-C Port Hole",
        type=ToolpathType.DRILL,
        description="Mounting hole for USB-C charging port",
        component=SmartGuitarComponent.USB_PORT,
    ),
    SmartGuitarToolpath(
        name="Antenna Recess",
        type=ToolpathType.POCKET,
        description="Recess for BLE/WiFi antenna",
        component=SmartGuitarComponent.ANTENNA,
    ),
]
