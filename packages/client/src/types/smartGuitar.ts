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

// =============================================================================
// FEATURE FLAGS
// =============================================================================

export const SMART_GUITAR_FEATURES = [
  'Real-time pitch detection',
  'Alternative temperament support (19+ systems)',
  'LED fret markers (RGB addressable)',
  'Onboard effects processing',
  'DAW integration (Giglad, Band-in-a-Box)',
  'Chord recognition',
  'Looper (60s stereo)',
  'Metronome with tap tempo',
  'Tuner (chromatic + temperament-aware)',
  'Wireless audio streaming',
  'MIDI controller mode',
  'Firmware OTA updates',
] as const;

export type SmartGuitarFeature = (typeof SMART_GUITAR_FEATURES)[number];

// =============================================================================
// DEFAULT VALUES
// =============================================================================

export const SMART_GUITAR_DEFAULTS: Partial<SmartGuitarSpec> = {
  model_id: 'smart_guitar',
  display_name: 'Smart Guitar',
  category: 'electric_guitar',
  scale_length_mm: 648.0,
  fret_count: 24,
  string_count: 6,
  manufacturer: "Luthier's ToolBox",
  year_introduced: 2025,
};
