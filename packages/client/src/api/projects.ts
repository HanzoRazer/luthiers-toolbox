// packages/client/src/api/projects.ts
/**
 * Projects API Client (HUB-001)
 *
 * Typed functions for GET/PUT /api/projects/{id}/design-state.
 *
 * This is the transport layer between the frontend and Layer 0.
 * All project state reads and writes go through these functions.
 *
 * Usage (inside useInstrumentProject.ts — do not call directly from components):
 *   const state = await getDesignState(projectId)
 *   await putDesignState(projectId, updatedState, 'Updated bridge geometry')
 *
 * See docs/PLATFORM_ARCHITECTURE.md — Layer 0.
 */

import { api } from '@/services/apiBase'

// ---------------------------------------------------------------------------
// Mirror types from backend schemas/instrument_project.py
// Single source of truth is the Python schema — keep these in sync.
// ---------------------------------------------------------------------------

export type InstrumentCategory =
  | 'acoustic_guitar'
  | 'electric_guitar'
  | 'bass'
  | 'violin'
  | 'mandolin'
  | 'ukulele'
  | 'banjo'
  | 'classical'
  | 'archtop'
  | 'custom'

export type NeckJointType = 'bolt_on' | 'set_neck' | 'neck_through' | 'dovetail'
export type TremoloStyle = 'vintage_6screw' | '2point' | 'floyd_rose' | 'hardtail' | 'none'
export type HeadstockType = 'angled' | 'flat' | 'scarf'
export type ManufacturingStatus = 'draft' | 'design_complete' | 'cam_approved' | 'in_production' | 'complete'
export type BlueprintSource = 'photo' | 'dxf' | 'manual'
export type BodySymmetry = 'symmetric' | 'asymmetric' | 'offset' | 'unknown'

export interface InstrumentSpec {
  scale_length_mm: number
  fret_count: number
  string_count: number
  nut_width_mm: number
  heel_width_mm: number
  neck_angle_degrees: number
  neck_joint_type: NeckJointType
  body_join_fret: number
  tremolo_style: TremoloStyle
  bass_scale_length_mm?: number | null
  perpendicular_fret?: number | null
}

export interface BlueprintDerivedGeometry {
  source: BlueprintSource
  confidence: number
  body_outline_mm?: Array<[number, number]> | null
  centerline_x_mm?: number | null
  axis_angle_deg: number
  symmetry: BodySymmetry
  symmetry_score: number
  body_length_mm?: number | null
  lower_bout_mm?: number | null
  upper_bout_mm?: number | null
  waist_mm?: number | null
  scale_length_detected_mm?: number | null
  instrument_classification?: string | null
  captured_at?: string | null
  notes: string[]
  blueprint_original?: Record<string, unknown> | null
}

export interface BridgeState {
  saddle_line_from_nut_mm?: number | null
  string_spread_mm: number
  compensation_treble_mm: number
  compensation_bass_mm: number
  saddle_slot_width_mm: number
  saddle_slot_depth_mm: number
  saddle_projection_mm: number
  pin_to_saddle_center_mm: number
  slot_offset_mm: number
  preset_id?: string | null
  last_committed_at?: string | null
}

export interface NeckState {
  heel_length_mm?: number | null
  heel_depth_mm?: number | null
  headstock_type: HeadstockType
  headstock_angle_deg: number
  nut_radius_inches: number
  heel_radius_inches: number
  profile_shape: 'c' | 'd' | 'v' | 'u' | 'asymmetric'
  thickness_at_1st_mm?: number | null
  thickness_at_12th_mm?: number | null
}

export interface MaterialSelection {
  top?: string | null
  back_sides?: string | null
  neck?: string | null
  fretboard?: string | null
  bridge?: string | null
  brace_stock?: string | null
  binding?: string | null
  selection_notes?: string | null
}

export interface AnalyzerObservation {
  run_id: string
  specimen_id: string
  observed_at: string
  primary_modes_hz: number[]
  wsi?: number | null
  tonal_character?: string | null
  findings: string[]
  reference_instrument?: string | null
  interpretation_confidence: number
}

export interface ManufacturingState {
  status: ManufacturingStatus
  approved_at?: string | null
  approved_by?: string | null
  operations_completed: string[]
  notes?: string | null
}

export interface InstrumentProjectData {
  schema_version: string
  instrument_type: InstrumentCategory
  spec?: InstrumentSpec | null
  blueprint_geometry?: BlueprintDerivedGeometry | null
  bridge_state?: BridgeState | null
  neck_state?: NeckState | null
  material_selection?: MaterialSelection | null
  analyzer_observations: AnalyzerObservation[]
  manufacturing_state?: ManufacturingState | null
  custom_data?: Record<string, unknown> | null
}

export interface DesignStateResponse {
  project_id: string
  name: string
  instrument_type: string | null
  design_state: InstrumentProjectData | null
  created_at: string
  updated_at: string
}

export interface ProjectSummaryResponse {
  project_id: string
  name: string
  instrument_type: string | null
  has_design_state: boolean
  is_cam_ready: boolean
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Default spec by instrument type — mirrors project_service.py defaults
// ---------------------------------------------------------------------------

export const INSTRUMENT_DEFAULTS: Record<InstrumentCategory, Partial<InstrumentSpec>> = {
  acoustic_guitar: { scale_length_mm: 645.0, fret_count: 20, nut_width_mm: 43.0, heel_width_mm: 56.0, neck_angle_degrees: 1.0, body_join_fret: 14, string_count: 6, neck_joint_type: 'dovetail', tremolo_style: 'none' },
  electric_guitar:  { scale_length_mm: 648.0, fret_count: 22, nut_width_mm: 42.0, heel_width_mm: 56.0, neck_angle_degrees: 0.0, body_join_fret: 14, string_count: 6, neck_joint_type: 'bolt_on',  tremolo_style: 'hardtail' },
  bass:             { scale_length_mm: 864.0, fret_count: 21, nut_width_mm: 38.0, heel_width_mm: 60.0, neck_angle_degrees: 0.0, body_join_fret: 14, string_count: 4, neck_joint_type: 'bolt_on',  tremolo_style: 'none' },
  classical:        { scale_length_mm: 650.0, fret_count: 19, nut_width_mm: 52.0, heel_width_mm: 56.0, neck_angle_degrees: 1.5, body_join_fret: 12, string_count: 6, neck_joint_type: 'dovetail', tremolo_style: 'none' },
  violin:           { scale_length_mm: 328.0, fret_count: 0,  nut_width_mm: 24.0, heel_width_mm: 30.0, neck_angle_degrees: 0.0, body_join_fret: 0,  string_count: 4, neck_joint_type: 'set_neck', tremolo_style: 'none' },
  ukulele:          { scale_length_mm: 349.0, fret_count: 15, nut_width_mm: 35.0, heel_width_mm: 42.0, neck_angle_degrees: 0.0, body_join_fret: 12, string_count: 4, neck_joint_type: 'bolt_on', tremolo_style: 'none' },
  mandolin:         { scale_length_mm: 356.0, fret_count: 19, nut_width_mm: 27.0, heel_width_mm: 33.0, neck_angle_degrees: 0.0, body_join_fret: 12, string_count: 8, neck_joint_type: 'dovetail', tremolo_style: 'none' },
  archtop:          { scale_length_mm: 648.0, fret_count: 20, nut_width_mm: 43.0, heel_width_mm: 58.0, neck_angle_degrees: 3.0, body_join_fret: 14, string_count: 6, neck_joint_type: 'set_neck', tremolo_style: 'none' },
  banjo:            { scale_length_mm: 660.0, fret_count: 22, nut_width_mm: 28.0, heel_width_mm: 35.0, neck_angle_degrees: 0.0, body_join_fret: 17, string_count: 5, neck_joint_type: 'bolt_on', tremolo_style: 'none' },
  custom:           { scale_length_mm: 648.0, fret_count: 22, nut_width_mm: 42.0, heel_width_mm: 56.0, neck_angle_degrees: 0.0, body_join_fret: 14, string_count: 6, neck_joint_type: 'bolt_on',  tremolo_style: 'hardtail' },
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** GET /api/projects/{id}/design-state */
export async function getDesignState(projectId: string): Promise<DesignStateResponse> {
  const response = await api(`/api/projects/${projectId}/design-state`)
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(err.detail ?? `Failed to load project state`)
  }
  return response.json()
}

/** PUT /api/projects/{id}/design-state */
export async function putDesignState(
  projectId: string,
  state: InstrumentProjectData,
  commitMessage?: string,
): Promise<DesignStateResponse> {
  const response = await api(`/api/projects/${projectId}/design-state`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ design_state: state, commit_message: commitMessage }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(err.detail ?? `Failed to save project state`)
  }
  return response.json()
}

/** GET /api/projects/{id} — lightweight summary without design state blob */
export async function getProjectSummary(projectId: string): Promise<ProjectSummaryResponse> {
  const response = await api(`/api/projects/${projectId}`)
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(err.detail ?? `Failed to load project`)
  }
  return response.json()
}
