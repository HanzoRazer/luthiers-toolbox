/**
 * Timing constants used across the client application.
 *
 * Replaces scattered magic-number literals with named, documented values.
 * All values in milliseconds unless otherwise noted.
 */

// ---------------------------------------------------------------------------
// Animation & Transitions
// ---------------------------------------------------------------------------

/** Standard CSS transition / animation duration (ms). */
export const ANIMATION_DURATION_MS = 300

/** Short shake / pulse feedback animation (ms). */
export const SHAKE_DURATION_MS = 260

/** Ring-focus highlight duration (ms). */
export const RING_FOCUS_DURATION_MS = 1200

// ---------------------------------------------------------------------------
// Debounce & Throttle
// ---------------------------------------------------------------------------

/** Default debounce delay for user input (ms). */
export const DEBOUNCE_DELAY_MS = 500

/** Short debounce for bulk-decision prevention of flicker (ms). */
export const DECISION_DEBOUNCE_MS = 250

/** Batch throttle delay for bulk operations (ms). */
export const BATCH_THROTTLE_MS = 40

/** Delay before revoking an object URL after download (ms). */
export const REVOKE_URL_DELAY_MS = 100

// ---------------------------------------------------------------------------
// Toast / Status Indicator Durations
// ---------------------------------------------------------------------------

/** Default toast notification display time (ms). */
export const DEFAULT_TOAST_MS = 4500

/** Success feedback auto-dismiss (ms). */
export const SUCCESS_TOAST_MS = 1600

/** Error feedback auto-dismiss (ms). */
export const ERROR_TOAST_MS = 2200

/** "Saved" indicator auto-dismiss (ms). */
export const SAVED_INDICATOR_MS = 3000

/** Bulk-progress indicator auto-dismiss (ms). */
export const BULK_PROGRESS_DISMISS_MS = 900

/** Bulk-export object-URL revoke delay (ms). */
export const EXPORT_REVOKE_DELAY_MS = 2500

// ---------------------------------------------------------------------------
// Polling & Retry
// ---------------------------------------------------------------------------

/** One second in milliseconds — base unit for intervals. */
export const SECOND_MS = 1000

/** Performance tracking delay after page load (ms). */
export const PERF_TRACK_DELAY_MS = 1000

/** Delay between batch export items (ms). */
export const BATCH_EXPORT_ITEM_DELAY_MS = 250

/** Short canvas/DOM render tick (ms). */
export const RENDER_TICK_MS = 100
