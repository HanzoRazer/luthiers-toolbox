/**
 * TypeScript type definitions for Luthier's Tool Box API
 */

// ==================== Rosette Types ====================

export interface RosetteParams {
  soundhole_diameter_mm: number
  exposure_mm?: number
  glue_clearance_mm?: number
  central_band: {
    width_mm: number
    thickness_mm: number
  }
  inner_purfling?: PurflingStrip[]
  outer_purfling?: PurflingStrip[]
}

export interface PurflingStrip {
  material?: string
  width_mm: number
  thickness_mm: number
}

export interface RosetteResult {
  soundhole_diameter_mm: number
  channel_width_mm: number
  channel_depth_mm: number
  stack: {
    inner_purfling: PurflingStrip[]
    central_band: {
      width_mm: number
      thickness_mm: number
    }
    outer_purfling: PurflingStrip[]
  }
}

// ==================== Bracing Types ====================

export interface BracingParams {
  model_name: string
  units?: string
  top_radius_mm?: number
  back_radius_mm?: number
  top_thickness_mm?: number
  back_thickness_mm?: number
  soundhole_diameter_mm?: number
  braces: Brace[]
}

export interface Brace {
  name: string
  material?: string
  density_kg_m3?: number
  profile: {
    type: 'rectangular' | 'triangular' | 'parabolic'
    height_mm: number
    width_mm: number
    taper_mm?: number
  }
  path: {
    points_mm: [number, number][]
  }
  glue_area_extra_mm?: number
}

export interface BracingResult {
  model_name: string
  units: string
  top_radius_mm?: number
  back_radius_mm?: number
  braces: {
    name: string
    length_mm: number
    section_area_mm2: number
    mass_g: number
    glue_edge_extra_mm2: number
  }[]
  totals: {
    mass_g: number
    glue_edge_extra_mm2: number
  }
}

// ==================== Hardware Types ====================

export interface HardwareParams {
  model_name: string
  units?: string
  components: HardwareComponent[]
}

export interface HardwareComponent {
  name: string
  type: 'cavity' | 'hole' | 'pocket'
  position_mm: [number, number]
  depth_mm?: number
  radius_mm?: number
  size_mm?: [number, number]
}

export interface HardwareResult {
  model_name: string
  count: number
  items: {
    name: string
    type: string
    position_mm: [number, number]
    depth_mm?: number
    radius_mm?: number
    size_mm?: [number, number]
  }[]
}

// ==================== Export Queue Types ====================

export interface ExportItem {
  id: string
  type: string
  model: string
  file: string
  status: 'queued' | 'processing' | 'ready' | 'downloaded'
  queued_at: string
}

// ==================== API Response Types ====================

export interface APIError {
  detail: string
}

export interface HealthCheck {
  status: string
  timestamp: string
}
