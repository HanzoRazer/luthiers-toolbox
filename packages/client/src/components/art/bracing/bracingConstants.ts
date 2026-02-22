/**
 * Constants for bracing calculator.
 */
import type { ProfileTypeInfo } from './bracingTypes'

// ============================================================================
// Profile Types
// ============================================================================

export const PROFILE_TYPES: ProfileTypeInfo[] = [
  {
    value: 'rectangular',
    label: 'Rectangular',
    desc: 'Standard rectangular cross-section'
  },
  {
    value: 'triangular',
    label: 'Triangular',
    desc: 'Peaked top for stiffness'
  },
  {
    value: 'parabolic',
    label: 'Parabolic',
    desc: 'Curved top, classic design'
  },
  {
    value: 'scalloped',
    label: 'Scalloped',
    desc: 'Tapered ends for flexibility'
  }
]

// ============================================================================
// Default Values
// ============================================================================

export const DEFAULT_WIDTH = 12.0
export const DEFAULT_HEIGHT = 8.0
export const DEFAULT_LENGTH = 300.0
export const DEFAULT_DENSITY = 420.0
