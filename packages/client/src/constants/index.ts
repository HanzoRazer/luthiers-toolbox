/**
 * Constants barrel export.
 *
 * Domain-specific named constants extracted from magic numbers across the
 * client codebase.  Import from here:
 *
 *   import { DEBOUNCE_DELAY_MS, DEFAULT_SCALE_LENGTH_MM } from '@/constants'
 */

export {
  // Animation & Transitions
  ANIMATION_DURATION_MS,
  SHAKE_DURATION_MS,
  RING_FOCUS_DURATION_MS,

  // Debounce & Throttle
  DEBOUNCE_DELAY_MS,
  DECISION_DEBOUNCE_MS,
  BATCH_THROTTLE_MS,
  REVOKE_URL_DELAY_MS,

  // Toast / Status
  DEFAULT_TOAST_MS,
  SUCCESS_TOAST_MS,
  ERROR_TOAST_MS,
  SAVED_INDICATOR_MS,
  BULK_PROGRESS_DISMISS_MS,
  EXPORT_REVOKE_DELAY_MS,

  // Polling & Retry
  SECOND_MS,
  PERF_TRACK_DELAY_MS,
  BATCH_EXPORT_ITEM_DELAY_MS,
  RENDER_TICK_MS,
} from './timing'

export {
  // Scale Lengths (mm)
  CLASSICAL_SCALE_LENGTH_MM,
  GIBSON_SCALE_LENGTH_MM,
  FENDER_SCALE_LENGTH_MM,
  PRS_SCALE_LENGTH_MM,
  DEFAULT_SCALE_LENGTH_MM,

  // Scale Lengths (inches)
  GIBSON_SCALE_LENGTH_INCHES,
  FENDER_SCALE_LENGTH_INCHES,

  // Frets
  DEFAULT_FRET_COUNT,
  MAX_FRETS,
  EXTENDED_FRET_COUNT,

  // Layout
  GRID_COLUMNS,

  // Instrument Geometry
  CLASSICAL_NUT_WIDTH_MM,
  CLASSICAL_HEEL_WIDTH_MM,
} from './dimensions'
