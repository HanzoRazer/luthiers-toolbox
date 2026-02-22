/**
 * DrillingLab types.
 */

export interface Hole {
  x: number
  y: number
  enabled: boolean
}

export interface DrillParams {
  toolType: string
  toolDiameter: number
  spindleRpm: number
  feedRate: number
  cycle: string
  depth: number
  retract: number
  safeZ: number
  peckDepth: number
  threadPitch: number
  postId: string
}

export interface LinearPattern {
  direction: string
  startX: number
  startY: number
  spacing: number
  count: number
}

export interface CircularPattern {
  centerX: number
  centerY: number
  radius: number
  count: number
  startAngle: number
}

export interface GridPattern {
  startX: number
  startY: number
  spacingX: number
  spacingY: number
  countX: number
  countY: number
}

export const DEFAULT_PARAMS: DrillParams = {
  toolType: 'drill',
  toolDiameter: 6.0,
  spindleRpm: 3000,
  feedRate: 300,
  cycle: 'G81',
  depth: -15,
  retract: 2,
  safeZ: 10,
  peckDepth: 5,
  threadPitch: 1.0,
  postId: 'GRBL'
}

export const DEFAULT_LINEAR_PATTERN: LinearPattern = {
  direction: 'x',
  startX: 10,
  startY: 10,
  spacing: 20,
  count: 3
}

export const DEFAULT_CIRCULAR_PATTERN: CircularPattern = {
  centerX: 50,
  centerY: 50,
  radius: 30,
  count: 6,
  startAngle: 0
}

export const DEFAULT_GRID_PATTERN: GridPattern = {
  startX: 10,
  startY: 10,
  spacingX: 20,
  spacingY: 20,
  countX: 3,
  countY: 2
}
