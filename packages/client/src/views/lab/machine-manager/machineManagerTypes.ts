/**
 * Shared types and constants for Machine Manager panels.
 */

export const MACHINES_API = '/api/machines'
export const POSTS_API = '/api/posts'

export const CONTROLLER_TYPES = [
  'GRBL',
  'Mach3',
  'Mach4',
  'LinuxCNC',
  'PathPilot',
  'MASSO',
  'Carbide Motion',
  'OnefinityOS',
] as const

export const TOOL_TYPES = ['EM', 'BALL', 'VBIT', 'DRILL', 'CHAMFER', 'SLOT', 'FACE'] as const

export interface MachineProfile {
  id: string
  title: string
  controller: string
  axes: {
    x?: { travel: number }
    y?: { travel: number }
    z?: { travel: number }
  }
  limits: {
    max_feed_xy?: number
    max_feed_z?: number
    rapid?: number
  }
  spindle?: {
    max_rpm?: number
    min_rpm?: number
  }
  post_id_default?: string
}

export interface Tool {
  t: number
  name: string
  type: string
  dia_mm: number
  len_mm: number
  holder?: string
  spindle_rpm?: number
  feed_mm_min?: number
  plunge_mm_min?: number
}

export interface Post {
  id: string
  name: string
  builtin: boolean
  description: string
}
