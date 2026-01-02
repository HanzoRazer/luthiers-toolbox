# Smart Guitar Specification

> **Version**: 1.0.0  
> **Last Updated**: December 22, 2025  
> **Status**: Active Development  
> **Model ID**: `smart_guitar` (canonical), `smart` (short form)

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Architecture](#hardware-architecture)
3. [Registry Schema](#registry-schema)
4. [API Contracts](#api-contracts)
5. [TypeScript Interfaces](#typescript-interfaces)
6. [Python Models](#python-models)
7. [Code Generation Instructions](#code-generation-instructions)
8. [DXF Assets](#dxf-assets)
9. [DAW Integration](#daw-integration)
10. [Related Endpoints](#related-endpoints)

---

## Overview

The Smart Guitar is an IoT-enabled electric guitar with embedded computing, real-time DSP, and DAW integration. It combines traditional lutherie CNC manufacturing with modern electronics for a connected musical instrument.

### Key Features

| Category | Specification |
|----------|---------------|
| **Processor** | Raspberry Pi 5 (8GB RAM, 64GB storage) |
| **OS** | Linux (custom Buildroot) |
| **Audio** | 24-bit ADC, 96kHz, 3ms latency |
| **Connectivity** | BLE 5.0, Wi-Fi 6, USB-C 3.1, MIDI |
| **Power** | 18650 Li-ion, 6000mAh, 8hr runtime |
| **Temperaments** | 19+ systems (12-TET, just intonation, meantone, etc.) |

---

## Hardware Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART GUITAR ELECTRONICS BAY                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │         RASPBERRY PI 5               │                       │
│  │  ┌────────────────────────────────┐  │                       │
│  │  │ • 8GB RAM                      │  │                       │
│  │  │ • 64GB eMMC                    │  │                       │
│  │  │ • Custom Buildroot Linux       │  │                       │
│  │  └────────────────────────────────┘  │                       │
│  │                                      │                       │
│  │  INTERFACES:                         │                       │
│  │  ├── USB MIDI (Type-C)               │                       │
│  │  ├── Bluetooth 5.0 (BLE MIDI)        │                       │
│  │  ├── Wi-Fi 6 (802.11ax)              │                       │
│  │  ├── I2S Audio (24-bit/96kHz)        │                       │
│  │  └── GPIO (sensors, LEDs)            │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │         POWER SYSTEM                 │                       │
│  │  ├── 4×18650 cells (2S2P)            │                       │
│  │  ├── 6000mAh total capacity          │                       │
│  │  ├── BMS with balancing              │                       │
│  │  ├── USB-C PD charging (20W)         │                       │
│  │  └── 8hr runtime @ typical use       │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │         AUDIO SUBSYSTEM              │                       │
│  │  ├── 24-bit ADC (6 channels)         │                       │
│  │  ├── 96kHz sample rate               │                       │
│  │  ├── 3ms end-to-end latency          │                       │
│  │  ├── Onboard DSP (effects)           │                       │
│  │  └── Outputs: 1/4" TRS, USB, BT A2DP │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │         SENSORS                      │                       │
│  │  ├── 6× Piezo pickups                │                       │
│  │  ├── 3-axis accelerometer            │                       │
│  │  ├── 3-axis gyroscope                │                       │
│  │  ├── Capacitive touch frets          │                       │
│  │  └── RGB LED fret markers            │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Registry Schema

The canonical schema lives in `services/api/app/instrument_geometry/instrument_model_registry.json`:

```json
{
  "smart_guitar": {
    "id": "smart_guitar",
    "display_name": "Smart Guitar",
    "status": "COMPLETE",
    "category": "electric_guitar",
    "scale_length_mm": 648.0,
    "fret_count": 24,
    "string_count": 6,
    "description": "IoT-enabled electric guitar with embedded computing, real-time DSP, and DAW integration",
    "manufacturer": "Luthier's ToolBox",
    "year_introduced": 2025,
    "body_style": "stratocaster_derivative",
    
    "iot": {
      "processor": "Raspberry Pi 5",
      "memory_gb": 8,
      "storage_gb": 64,
      "os": "Linux (custom Buildroot)"
    },
    
    "connectivity": {
      "bluetooth": "BLE 5.0",
      "wifi": "Wi-Fi 6 (802.11ax)",
      "usb": "USB-C 3.1",
      "midi": ["USB MIDI", "BLE MIDI", "DIN MIDI (optional)"]
    },
    
    "audio": {
      "adc_bits": 24,
      "sample_rate_khz": 96,
      "latency_ms": 3,
      "dsp": "Real-time pitch detection, effects processing",
      "outputs": ["1/4\" TRS", "USB Audio", "Bluetooth A2DP"]
    },
    
    "sensors": {
      "piezo_pickups": 6,
      "accelerometer": true,
      "gyroscope": true,
      "capacitive_touch_frets": true,
      "pressure_sensitive_strings": false
    },
    
    "power": {
      "battery_type": "Li-ion 18650",
      "capacity_mah": 6000,
      "runtime_hours": 8,
      "charging": "USB-C PD 20W"
    },
    
    "features": [
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
      "Firmware OTA updates"
    ],
    
    "daw_integration": {
      "giglad": {
        "status": "OEM partnership",
        "features": ["Live backing tracks", "AI accompaniment"]
      },
      "pgmusic": {
        "status": "OEM partnership",
        "features": ["Band-in-a-Box integration", "Chord recognition"]
      }
    },
    
    "cam_features": {
      "electronics_cavity": "Custom routed for Pi 5 + battery",
      "control_panel": "3D printed or CNC aluminum",
      "pcb_mounting": "M2.5 standoffs, vibration dampened"
    },
    
    "assets": [
      "smart_guitar/body_outline.dxf",
      "smart_guitar/electronics_cavity.dxf",
      "smart_guitar/control_panel.dxf",
      "smart_guitar/pcb_mounting.dxf"
    ]
  }
}
```

---

## API Contracts

### Instrument Axis: `/api/instruments/guitar/smart/*`

#### GET `/api/instruments/guitar/smart/spec`

Returns base specifications for the Smart Guitar.

**Response:**
```json
{
  "model_id": "smart_guitar",
  "display_name": "Smart Guitar",
  "category": "electric_guitar",
  "status": "COMPLETE",
  "scale_length_mm": 648.0,
  "scale_length_inches": 25.51,
  "fret_count": 24,
  "string_count": 6,
  "manufacturer": "Luthier's ToolBox",
  "year_introduced": 2025,
  "description": "IoT-enabled electric guitar...",
  "features": ["24-fret neck", "6 strings", "648.0mm scale (25.51\")"]
}
```

#### GET `/api/instruments/guitar/smart/info`

Returns full integration overview including IoT architecture.

**Response:**
```json
{
  "ok": true,
  "model_id": "smart",
  "display_name": "Smart Guitar",
  "category": "electric_guitar",
  "concept": "Smart Guitar DAW Bundle",
  "description": "...",
  "architecture": {
    "hardware": {
      "processor": "Raspberry Pi 5",
      "connectivity": ["Bluetooth LE 5.0", "USB-C", "Wi-Fi 6"],
      "audio": "24-bit ADC with real-time DSP",
      "power": "Li-ion battery with USB-C charging"
    },
    "software": {
      "os": "Linux (headless)",
      "daw_integration": ["MIDI over BLE", "OSC", "USB Audio"],
      "temperament_engine": "/api/music/temperament/*"
    }
  },
  "status": "Development - requires custom implementation",
  "related_endpoints": {
    "spec": "/api/instruments/guitar/smart/spec",
    "bundle": "/api/instruments/guitar/smart/bundle",
    "temperament": "/api/music/temperament/health",
    "cam": "/api/cam/guitar/smart/health"
  }
}
```

#### GET `/api/instruments/guitar/smart/bundle`

Returns DAW bundle resources and documentation.

---

### CAM Axis: `/api/cam/guitar/smart/*`

#### GET `/api/cam/guitar/smart/health`

**Response:**
```json
{
  "ok": true,
  "subsystem": "smart_guitar_cam",
  "model_id": "smart",
  "capabilities": ["toolpaths", "preview", "electronics_routing"],
  "status": "Development - toolpath generation in progress",
  "instrument_spec": "/api/instruments/guitar/smart/spec",
  "temperament_api": "/api/music/temperament/health"
}
```

#### GET `/api/cam/guitar/smart/toolpaths`

Lists available toolpath generators for Smart Guitar components.

**Response:**
```json
{
  "ok": true,
  "toolpaths": [
    {
      "name": "Electronics Cavity",
      "type": "pocket",
      "description": "Pocket for Raspberry Pi 5 and electronics board",
      "component": "electronics_cavity"
    },
    {
      "name": "Battery Pocket",
      "type": "pocket",
      "description": "Li-ion battery compartment",
      "component": "battery"
    },
    {
      "name": "LED Channel",
      "type": "contour",
      "description": "Channel for LED strip along fretboard edge",
      "component": "led_channel"
    },
    {
      "name": "USB-C Port Hole",
      "type": "drill",
      "description": "Mounting hole for USB-C charging port",
      "component": "usb_port"
    },
    {
      "name": "Antenna Recess",
      "type": "pocket",
      "description": "Recess for BLE/WiFi antenna",
      "component": "antenna"
    }
  ]
}
```

---

### Music Axis: `/api/music/temperament/*`

The Smart Guitar uses the global temperament API for alternative tuning systems.

#### GET `/api/music/temperament/health`

**Response:**
```json
{
  "ok": true,
  "subsystem": "music_temperament",
  "version": "2.0.0",
  "wave": "Wave 15 (Option C)",
  "capabilities": ["temperament_comparison", "key_optimization", "tuning_reference"],
  "supported_temperaments": ["12-TET", "just_major", "just_minor", "pythagorean", "meantone_1/4"],
  "supported_keys": ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#"],
  "note": "Global temperament API - not model-locked"
}
```

---

## TypeScript Interfaces

Save to: `packages/client/src/types/smartGuitar.ts`

```typescript
/**
 * Smart Guitar TypeScript Interfaces
 * ===================================
 * 
 * Generated from instrument_model_registry.json schema.
 * Use these types for frontend development.
 * 
 * @version 1.0.0
 * @generated December 22, 2025
 */

// =============================================================================
// CORE TYPES
// =============================================================================

export interface SmartGuitarSpec {
  model_id: 'smart_guitar';
  display_name: string;
  category: 'electric_guitar';
  status: 'COMPLETE' | 'STUB' | 'ASSETS_ONLY';
  scale_length_mm: number;
  scale_length_inches: number;
  fret_count: number;
  string_count: number;
  manufacturer: string;
  year_introduced: number;
  description: string;
  features: string[];
}

export interface SmartGuitarInfo {
  ok: boolean;
  model_id: 'smart';
  display_name: string;
  category: string;
  concept: string;
  description: string;
  architecture: SmartGuitarArchitecture;
  status: string;
  related_endpoints: SmartGuitarEndpoints;
}

// =============================================================================
// IoT SUBSYSTEMS
// =============================================================================

export interface SmartGuitarIoT {
  processor: 'Raspberry Pi 5';
  memory_gb: number;
  storage_gb: number;
  os: string;
}

export interface SmartGuitarConnectivity {
  bluetooth: string;
  wifi: string;
  usb: string;
  midi: MidiProtocol[];
}

export type MidiProtocol = 'USB MIDI' | 'BLE MIDI' | 'DIN MIDI (optional)';

export interface SmartGuitarAudio {
  adc_bits: 24;
  sample_rate_khz: 48 | 96 | 192;
  latency_ms: number;
  dsp: string;
  outputs: AudioOutput[];
}

export type AudioOutput = '1/4" TRS' | 'USB Audio' | 'Bluetooth A2DP';

export interface SmartGuitarSensors {
  piezo_pickups: number;
  accelerometer: boolean;
  gyroscope: boolean;
  capacitive_touch_frets: boolean;
  pressure_sensitive_strings: boolean;
}

export interface SmartGuitarPower {
  battery_type: 'Li-ion 18650';
  capacity_mah: number;
  runtime_hours: number;
  charging: string;
}

// =============================================================================
// ARCHITECTURE
// =============================================================================

export interface SmartGuitarArchitecture {
  hardware: {
    processor: string;
    connectivity: string[];
    audio: string;
    power: string;
  };
  software: {
    os: string;
    daw_integration: string[];
    temperament_engine: string;
  };
}

export interface SmartGuitarEndpoints {
  spec: string;
  bundle: string;
  temperament: string;
  cam: string;
}

// =============================================================================
// DAW INTEGRATION
// =============================================================================

export interface DawPartner {
  status: 'OEM partnership' | 'integration planned' | 'community';
  features: string[];
}

export interface SmartGuitarDawIntegration {
  giglad: DawPartner;
  pgmusic: DawPartner;
}

// =============================================================================
// CAM FEATURES
// =============================================================================

export interface SmartGuitarCamFeatures {
  electronics_cavity: string;
  control_panel: string;
  pcb_mounting: string;
}

export interface SmartGuitarToolpath {
  name: string;
  type: 'pocket' | 'drill' | 'contour';
  description: string;
  component: SmartGuitarComponent;
}

export type SmartGuitarComponent =
  | 'electronics_cavity'
  | 'battery'
  | 'led_channel'
  | 'usb_port'
  | 'antenna';

// =============================================================================
// FULL REGISTRY ENTRY
// =============================================================================

export interface SmartGuitarRegistryEntry {
  id: 'smart_guitar';
  display_name: string;
  status: 'COMPLETE';
  category: 'electric_guitar';
  scale_length_mm: number;
  fret_count: number;
  string_count: number;
  description: string;
  manufacturer: string;
  year_introduced: number;
  body_style: string;
  iot: SmartGuitarIoT;
  connectivity: SmartGuitarConnectivity;
  audio: SmartGuitarAudio;
  sensors: SmartGuitarSensors;
  power: SmartGuitarPower;
  features: string[];
  daw_integration: SmartGuitarDawIntegration;
  cam_features: SmartGuitarCamFeatures;
  assets: string[];
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface SmartGuitarHealthResponse {
  ok: boolean;
  subsystem: 'smart_guitar_cam';
  model_id: 'smart';
  capabilities: string[];
  status: string;
  instrument_spec: string;
  temperament_api: string;
}

export interface SmartGuitarToolpathsResponse {
  ok: boolean;
  toolpaths: SmartGuitarToolpath[];
}

export interface SmartGuitarBundleResponse {
  ok: boolean;
  bundle_version: string;
  build_date: string;
  resources: SmartGuitarResource[];
  status: string;
}

export interface SmartGuitarResource {
  name: string;
  type: 'documentation' | 'oem_correspondence' | 'instructions' | 'pdf';
  path?: string;
  description?: string;
}
```

---

## Python Models

Save to: `services/api/app/schemas/smart_guitar.py`

```python
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
    midi: List[MidiProtocol] = [
        MidiProtocol.USB_MIDI,
        MidiProtocol.BLE_MIDI,
        MidiProtocol.DIN_MIDI,
    ]


class SmartGuitarAudio(BaseModel):
    """Audio subsystem specifications."""
    adc_bits: Literal[24] = 24
    sample_rate_khz: Literal[48, 96, 192] = 96
    latency_ms: float = 3.0
    dsp: str = "Real-time pitch detection, effects processing"
    outputs: List[AudioOutput] = [
        AudioOutput.TRS,
        AudioOutput.USB_AUDIO,
        AudioOutput.BLUETOOTH,
    ]


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
    giglad: DawPartner = DawPartner(
        status="OEM partnership",
        features=["Live backing tracks", "AI accompaniment"],
    )
    pgmusic: DawPartner = DawPartner(
        status="OEM partnership",
        features=["Band-in-a-Box integration", "Chord recognition"],
    )


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
        "648.0mm scale (25.51\")",
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
    description: str = ""
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
    features: List[str] = Field(default_factory=list)
    daw_integration: SmartGuitarDawIntegration = Field(
        default_factory=SmartGuitarDawIntegration
    )
    cam_features: SmartGuitarCamFeatures = Field(
        default_factory=SmartGuitarCamFeatures
    )
    assets: List[str] = Field(default_factory=list)


# =============================================================================
# API RESPONSE MODELS
# =============================================================================

class SmartGuitarHealthResponse(BaseModel):
    """CAM health check response."""
    ok: bool = True
    subsystem: Literal["smart_guitar_cam"] = "smart_guitar_cam"
    model_id: Literal["smart"] = "smart"
    capabilities: List[str] = ["toolpaths", "preview", "electronics_routing"]
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
```

---

## Code Generation Instructions

### Frontend (TypeScript)

1. **Copy interfaces** to `packages/client/src/types/smartGuitar.ts`

2. **Import in components:**
   ```typescript
   import type { 
     SmartGuitarSpec, 
     SmartGuitarInfo,
     SmartGuitarToolpath 
   } from '@/types/smartGuitar';
   ```

3. **Use with API service:**
   ```typescript
   // In packages/client/src/services/smartGuitarApi.ts
   import { apiFetch, buildUrl } from './apiBase';
   import type { SmartGuitarSpec, SmartGuitarInfo } from '@/types/smartGuitar';

   export async function fetchSmartGuitarSpec(): Promise<SmartGuitarSpec> {
     return apiFetch<SmartGuitarSpec>(buildUrl('api', 'instruments', 'guitar', 'smart', 'spec'));
   }

   export async function fetchSmartGuitarInfo(): Promise<SmartGuitarInfo> {
     return apiFetch<SmartGuitarInfo>(buildUrl('api', 'instruments', 'guitar', 'smart', 'info'));
   }
   ```

### Backend (Python)

1. **Copy models** to `services/api/app/schemas/smart_guitar.py`

2. **Import in routers:**
   ```python
   from app.schemas.smart_guitar import (
       SmartGuitarSpec,
       SmartGuitarInfo,
       SmartGuitarHealthResponse,
       SmartGuitarToolpathsResponse,
   )
   ```

3. **Use in endpoints:**
   ```python
   @router.get("/spec", response_model=SmartGuitarSpec)
   def get_smart_guitar_spec() -> SmartGuitarSpec:
       return SmartGuitarSpec()
   ```

### Validation

```bash
# Python: Validate models load
cd services/api
python -c "from app.schemas.smart_guitar import SmartGuitarRegistryEntry; print('✓ Models OK')"

# TypeScript: Check types compile
cd packages/client
npx tsc --noEmit src/types/smartGuitar.ts
```

---

## DXF Assets

| Asset | Path | Purpose |
|-------|------|---------|
| Body Outline | `smart_guitar/body_outline.dxf` | Main body profile |
| Electronics Cavity | `smart_guitar/electronics_cavity.dxf` | Pi 5 + battery routing |
| Control Panel | `smart_guitar/control_panel.dxf` | Knob/switch layout |
| PCB Mounting | `smart_guitar/pcb_mounting.dxf` | Standoff positions |

**DXF Requirements:**
- Format: R12 (AC1009)
- Units: Millimeters
- Geometry: Closed LWPolylines
- Tolerance: ±0.12mm

---

## DAW Integration

### Giglad Partnership
- **Status**: OEM partnership
- **Features**: Live backing tracks, AI accompaniment
- **Protocol**: BLE MIDI, USB Audio

### PGMusic Partnership
- **Status**: OEM partnership  
- **Features**: Band-in-a-Box integration, chord recognition
- **Protocol**: USB MIDI, OSC

---

## Related Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/instruments/guitar/smart/spec` | GET | Base specifications |
| `/api/instruments/guitar/smart/info` | GET | Full architecture info |
| `/api/instruments/guitar/smart/bundle` | GET | DAW bundle resources |
| `/api/cam/guitar/smart/health` | GET | CAM subsystem health |
| `/api/cam/guitar/smart/toolpaths` | GET | Available toolpaths |
| `/api/music/temperament/health` | GET | Temperament API health |
| `/api/music/temperament/systems` | GET | List all temperaments |
| `/api/music/temperament/compare` | POST | Compare temperaments |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-22 | Initial specification document |

---

**Document Maintainer**: Luthier's ToolBox Team  
**Source of Truth**: `services/api/app/instrument_geometry/instrument_model_registry.json`
