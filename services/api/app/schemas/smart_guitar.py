"""
Smart Guitar Pydantic Models
============================

Re-exports from sg-spec canonical package.
All schema definitions are now owned by sg-spec.

Install sg-spec:
    pip install git+https://github.com/HanzoRazer/sg-spec.git

Version: 1.0.0
"""

# Re-export all schemas from sg-spec (canonical source of truth)
from sg_spec.schemas.smart_guitar import (
    # Enums
    SmartGuitarStatus,
    MidiProtocol,
    AudioOutput,
    ToolpathType,
    SmartGuitarComponent,
    # IoT subsystems
    SmartGuitarIoT,
    SmartGuitarConnectivity,
    SmartGuitarAudio,
    SmartGuitarSensors,
    SmartGuitarPower,
    # Core models
    SmartGuitarSpec,
    SmartGuitarCamFeatures,
    SmartGuitarToolpath,
    SmartGuitarDawIntegration,
    DawPartner,
    SmartGuitarArchitecture,
    SmartGuitarInfo,
    SmartGuitarRegistryEntry,
    # API responses
    SmartGuitarHealthResponse,
    SmartGuitarToolpathsResponse,
    SmartGuitarResource,
    SmartGuitarBundleResponse,
)

__all__ = [
    "SmartGuitarStatus",
    "MidiProtocol",
    "AudioOutput",
    "ToolpathType",
    "SmartGuitarComponent",
    "SmartGuitarIoT",
    "SmartGuitarConnectivity",
    "SmartGuitarAudio",
    "SmartGuitarSensors",
    "SmartGuitarPower",
    "SmartGuitarSpec",
    "SmartGuitarCamFeatures",
    "SmartGuitarToolpath",
    "SmartGuitarDawIntegration",
    "DawPartner",
    "SmartGuitarArchitecture",
    "SmartGuitarInfo",
    "SmartGuitarRegistryEntry",
    "SmartGuitarHealthResponse",
    "SmartGuitarToolpathsResponse",
    "SmartGuitarResource",
    "SmartGuitarBundleResponse",
]
