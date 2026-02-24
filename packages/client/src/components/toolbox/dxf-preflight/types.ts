/**
 * DXF Preflight Validator types.
 */

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info'
  category: string
  message: string
  details?: string
  fix_available: boolean
  fix_description?: string
}

export interface GeometrySummary {
  lines: number
  arcs: number
  circles: number
  polylines: number
  lwpolylines: number
  splines: number
  ellipses: number
  text: number
  other: number
  total: number
}

export interface LayerInfo {
  name: string
  entity_count: number
  geometry_types: string[]
  color?: number
  frozen: boolean
  locked: boolean
}

export interface ValidationReport {
  filename: string
  filesize_bytes: number
  dxf_version: string
  units: string
  issues: ValidationIssue[]
  errors_count: number
  warnings_count: number
  info_count: number
  geometry: GeometrySummary
  layers: LayerInfo[]
  cam_ready: boolean
  recommended_actions: string[]
}

export interface FixOptions {
  convert_to_r12: boolean
  close_open_polylines: boolean
  set_units_mm: boolean
  explode_splines: boolean
}
