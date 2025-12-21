/**
 * RMOS Strip Family Models (MM-0)
 * 
 * TypeScript models for mixed-material rosette strip families.
 */

export type MaterialType =
  | 'wood'
  | 'metal'
  | 'shell'
  | 'paper'
  | 'foil'
  | 'charred'
  | 'resin'
  | 'composite'

export interface MaterialVisual {
  base_color?: string
  reflectivity?: number
  iridescence?: boolean
  texture_map?: string
  grain_angle_deg?: number
  burn_gradient?: boolean
  repeat_pattern?: boolean
}confirm 

export interface MaterialSpec {
  key: string
  type: MaterialType
  species?: string
  thickness_mm?: number
  finish?: string
  cam_profile?: string
  visual?: MaterialVisual
}

export interface StripFamily {
  id: string
  name: string
  description?: string
  default_width_mm?: number
  sequence: number[]
  materials: MaterialSpec[]
  notes?: string
  lane?: string
  
  // Legacy fields for compatibility
  color_hex?: string
  default_tile_length_mm?: number
  default_slice_angle_deg?: number
}
