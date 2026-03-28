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

/** Form state for the “Add machine” modal (mapped to MachineProfile on create). */
export interface NewMachineDraft {
  id: string
  title: string
  controller: string
  x_travel: number
  y_travel: number
  z_travel: number
  max_feed_xy: number
  max_feed_z: number
  rapid: number
  max_rpm: number
  min_rpm: number
}

export function defaultNewMachineDraft(): NewMachineDraft {
  return {
    id: '',
    title: '',
    controller: 'GRBL',
    x_travel: 300,
    y_travel: 300,
    z_travel: 100,
    max_feed_xy: 5000,
    max_feed_z: 2000,
    rapid: 10000,
    max_rpm: 24000,
    min_rpm: 5000,
  }
}

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

export function machineProfileFromNewDraft(d: NewMachineDraft): MachineProfile {
  return {
    id: d.id.toLowerCase().replace(/\s+/g, '_'),
    title: d.title,
    controller: d.controller,
    axes: {
      x: { travel: d.x_travel },
      y: { travel: d.y_travel },
      z: { travel: d.z_travel },
    },
    limits: {
      max_feed_xy: d.max_feed_xy,
      max_feed_z: d.max_feed_z,
      rapid: d.rapid,
    },
    spindle: {
      max_rpm: d.max_rpm,
      min_rpm: d.min_rpm,
    },
  }
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
