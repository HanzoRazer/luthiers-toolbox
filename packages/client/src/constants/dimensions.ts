/**
 * Guitar / lutherie dimension constants.
 *
 * Domain-specific numeric values used across calculators, previews, and
 * generators.  All lengths in mm unless the constant name includes a
 * different unit suffix (e.g. `_INCHES`).
 */

// ---------------------------------------------------------------------------
// Scale Lengths (mm)
// ---------------------------------------------------------------------------

/** Classical guitar scale length (mm). */
export const CLASSICAL_SCALE_LENGTH_MM = 650

/** Gibson-style scale length (mm). */
export const GIBSON_SCALE_LENGTH_MM = 628.65 // 24.75 inches

/** Fender-style scale length (mm). */
export const FENDER_SCALE_LENGTH_MM = 647.7 // 25.5 inches

/** PRS-style scale length (mm). */
export const PRS_SCALE_LENGTH_MM = 635 // 25 inches

/** Default scale length used when none is specified (mm). */
export const DEFAULT_SCALE_LENGTH_MM = 650

// ---------------------------------------------------------------------------
// Scale Lengths (inches) — for unit-converter defaults
// ---------------------------------------------------------------------------

/** Gibson-style scale length (inches). */
export const GIBSON_SCALE_LENGTH_INCHES = 24.75

/** Fender-style scale length (inches). */
export const FENDER_SCALE_LENGTH_INCHES = 25.5

// ---------------------------------------------------------------------------
// Frets
// ---------------------------------------------------------------------------

/** Standard fret count for most guitars. */
export const DEFAULT_FRET_COUNT = 12

/** Maximum number of frets supported by the calculator. */
export const MAX_FRETS = 22

/** Extended fret range (24-fret guitars). */
export const EXTENDED_FRET_COUNT = 24

// ---------------------------------------------------------------------------
// Layout & Grid
// ---------------------------------------------------------------------------

/** Default grid column count for responsive layouts. */
export const GRID_COLUMNS = 12

// ---------------------------------------------------------------------------
// Instrument Geometry Presets (mm)
// ---------------------------------------------------------------------------

/** Classical guitar nut width (mm). */
export const CLASSICAL_NUT_WIDTH_MM = 52

/** Classical guitar heel width (mm). */
export const CLASSICAL_HEEL_WIDTH_MM = 62
