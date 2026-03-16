/**
 * Stratocaster Neck Generator - Utility Functions
 * Generates parametric neck geometry for Stratocaster style guitars
 * Supports C, V, and Modern C profiles with flat headstock
 */

// Unit conversion constants
const MM_PER_INCH = 25.4
const INCH_PER_MM = 0.03937007874015748

export type StratNeckProfile = 'C' | 'V' | 'modern_C' | 'soft_V' | 'D'

export interface StratNeckParameters {
  // Blank dimensions
  blank_length: number
  blank_width: number
  blank_thickness: number

  // Scale and dimensions
  scale_length: number
  nut_width: number
  heel_width: number
  neck_length: number

  // Fretboard
  fretboard_radius: number
  fretboard_offset: number
  compound_radius: boolean
  fretboard_radius_heel: number // For compound radius
  include_fretboard: boolean
  fret_count: 21 | 22 | 24

  // Profile shape
  profile_type: StratNeckProfile
  thickness_1st_fret: number
  thickness_12th_fret: number
  shoulder_width: number // V-profile shoulder sharpness

  // Headstock (flat, 6-in-line)
  headstock_length: number
  headstock_thickness: number
  headstock_taper: number // Width taper from nut
  tuner_spacing: number
  tuner_diameter: number
  string_tree_positions: number[] // Distance from nut

  // Truss rod
  truss_rod_channel_width: number
  truss_rod_channel_depth: number
  truss_rod_access: 'headstock' | 'heel'

  // Options
  alignment_pin_holes: boolean
  skunk_stripe: boolean // Single-piece maple indicator

  // Units (optional, defaults to inches)
  units?: 'mm' | 'inch'
}

export interface StratValidationWarning {
  field: string
  message: string
  severity: 'error' | 'warning'
}

export interface StratValidationResult {
  valid: boolean
  warnings: StratValidationWarning[]
}

export interface StratNeckGeometry {
  profile: Point3D[]
  fretboard?: Point3D[]
  headstock: Point3D[]
  tuner_holes: Circle[]
  centerline: Point3D[]
  truss_rod_channel: Point3D[]
  fret_slots: FretSlot[]
}

interface Point3D {
  x: number
  y: number
  z: number
}

interface Circle {
  center: Point3D
  diameter: number
}

interface FretSlot {
  fret_number: number
  distance_from_nut: number
  width: number
}

/**
 * Generate Stratocaster neck geometry from parameters
 */
export function generateStratNeck(params: StratNeckParameters): StratNeckGeometry {
  const geometry: StratNeckGeometry = {
    profile: [],
    headstock: [],
    tuner_holes: [],
    centerline: [],
    truss_rod_channel: [],
    fret_slots: []
  }

  // Generate centerline (spine of neck)
  geometry.centerline = generateCenterline(params)

  // Generate neck profile based on profile type
  geometry.profile = generateNeckProfile(params)

  // Generate flat headstock geometry (6-in-line)
  geometry.headstock = generateHeadstock(params)

  // Generate tuner holes (6-in-line configuration)
  geometry.tuner_holes = generateTunerHoles(params)

  // Generate truss rod channel
  geometry.truss_rod_channel = generateTrussRodChannel(params)

  // Generate fret slot positions
  geometry.fret_slots = generateFretSlots(params)

  // Optionally generate fretboard
  if (params.include_fretboard) {
    geometry.fretboard = generateFretboard(params)
  }

  return geometry
}

/**
 * Generate centerline from nut to heel
 */
function generateCenterline(params: StratNeckParameters): Point3D[] {
  const points: Point3D[] = []
  const steps = 100

  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const distance = t * params.neck_length

    // Strat necks are typically flat (no neck angle like Les Paul)
    points.push({
      x: distance,
      y: 0, // Center of neck
      z: 0 // Reference plane
    })
  }

  return points
}

/**
 * Generate neck profile based on profile type
 */
function generateNeckProfile(params: StratNeckParameters): Point3D[] {
  const points: Point3D[] = []
  const lengthSteps = 24 // Number of cross-sections along length
  const widthSteps = 40 // Points per cross-section (more for accurate profile)

  for (let i = 0; i <= lengthSteps; i++) {
    const t = i / lengthSteps
    const x = t * params.neck_length

    // Interpolate width from nut to heel
    const width = params.nut_width + t * (params.heel_width - params.nut_width)

    // Interpolate thickness
    const fret_t = t * params.fret_count
    const thickness = interpolateThickness(fret_t, params)

    // Generate cross-section based on profile type
    for (let j = 0; j <= widthSteps; j++) {
      const w_t = j / widthSteps
      const y = (w_t - 0.5) * width

      // Profile-specific Z calculation
      const z = calculateProfileZ(w_t, thickness, params)

      points.push({ x, y, z })
    }
  }

  return points
}

/**
 * Calculate Z coordinate based on profile type
 */
function calculateProfileZ(
  t: number,
  thickness: number,
  params: StratNeckParameters
): number {
  const centerOffset = 0.5
  const dist = Math.abs(t - centerOffset)
  const normalizedDist = dist * 2 // 0 at center, 1 at edges

  switch (params.profile_type) {
    case 'C':
      // Classic C: Rounded, comfortable
      return -thickness * (1 - Math.pow(normalizedDist, 1.6))

    case 'modern_C':
      // Modern C: Slightly flatter than classic C
      return -thickness * (1 - Math.pow(normalizedDist, 1.4))

    case 'V':
      // V-shape: Angular with sharp spine
      const vPeak = 1 - normalizedDist
      const shoulderFactor = params.shoulder_width || 0.7
      return -thickness * Math.pow(vPeak, shoulderFactor)

    case 'soft_V':
      // Soft V: Rounded V, less angular
      const softVPeak = 1 - normalizedDist
      return -thickness * Math.pow(softVPeak, 1.2)

    case 'D':
      // D-shape: Flatter back, sharp edges
      const dCurve = Math.cos((normalizedDist * Math.PI) / 2)
      return -thickness * dCurve * 0.8

    default:
      // Default to C profile
      return -thickness * (1 - Math.pow(normalizedDist, 1.6))
  }
}

/**
 * Interpolate thickness between 1st and 12th fret
 */
function interpolateThickness(
  fret: number,
  params: StratNeckParameters
): number {
  if (fret <= 1) return params.thickness_1st_fret
  if (fret >= 12) return params.thickness_12th_fret

  const t = (fret - 1) / 11 // Normalize between 1st and 12th
  return (
    params.thickness_1st_fret +
    t * (params.thickness_12th_fret - params.thickness_1st_fret)
  )
}

/**
 * Generate flat headstock geometry (Fender style)
 */
function generateHeadstock(params: StratNeckParameters): Point3D[] {
  const points: Point3D[] = []
  const steps = 20

  // Strat headstock is FLAT (no angle) - key difference from Gibson
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const x = -t * params.headstock_length // Negative X

    // Headstock tapers outward from nut (asymmetric)
    // Bass side is wider than treble side
    const bassTaper = params.headstock_taper * t
    const trebleTaper = params.headstock_taper * t * 0.6

    // Generate cross-section
    for (let j = 0; j <= 10; j++) {
      const w_t = j / 10
      let y: number

      // Asymmetric width (bass side wider)
      if (w_t < 0.5) {
        // Treble side
        y = -(w_t * 2) * (params.nut_width / 2 + trebleTaper)
      } else {
        // Bass side
        y = ((w_t - 0.5) * 2) * (params.nut_width / 2 + bassTaper)
      }

      // Flat headstock - Z stays constant (no angle)
      points.push({ x, y, z: -params.headstock_thickness })
    }
  }

  return points
}

/**
 * Generate tuner hole locations (6-in-line configuration for Strat)
 */
function generateTunerHoles(params: StratNeckParameters): Circle[] {
  const holes: Circle[] = []

  // 6-in-line configuration: all on bass side
  const startX = -params.headstock_length * 0.15
  const endX = -params.headstock_length * 0.85
  const xSpan = endX - startX

  for (let i = 0; i < 6; i++) {
    const t = i / 5
    const x = startX + t * xSpan

    // Y position on bass side (staggered for string angle)
    const yOffset = params.nut_width * 0.3 + t * params.headstock_taper * 0.5

    holes.push({
      center: { x, y: yOffset, z: 0 },
      diameter: params.tuner_diameter
    })
  }

  return holes
}

/**
 * Generate truss rod channel geometry
 */
function generateTrussRodChannel(params: StratNeckParameters): Point3D[] {
  const points: Point3D[] = []
  const steps = 50

  // Truss rod runs from nut to approximately fret 12
  const channelLength = params.scale_length * 0.4

  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const x = t * channelLength

    // Channel is centered, fixed width and depth
    const halfWidth = params.truss_rod_channel_width / 2

    // Left edge
    points.push({
      x,
      y: -halfWidth,
      z: -params.truss_rod_channel_depth
    })

    // Right edge
    points.push({
      x,
      y: halfWidth,
      z: -params.truss_rod_channel_depth
    })
  }

  return points
}

/**
 * Generate fret slot positions using equal temperament
 */
function generateFretSlots(params: StratNeckParameters): FretSlot[] {
  const slots: FretSlot[] = []
  const fretWire = 0.095 // Standard medium fret wire width in inches

  for (let fret = 1; fret <= params.fret_count; fret++) {
    // Distance from nut using equal temperament formula
    const distance =
      params.scale_length - params.scale_length / Math.pow(2, fret / 12)

    slots.push({
      fret_number: fret,
      distance_from_nut: distance,
      width: fretWire
    })
  }

  return slots
}

/**
 * Generate fretboard geometry with optional compound radius
 */
function generateFretboard(params: StratNeckParameters): Point3D[] {
  const points: Point3D[] = []

  // Generate at each fret position
  for (let fret = 0; fret <= params.fret_count; fret++) {
    const distance =
      fret === 0
        ? 0
        : params.scale_length - params.scale_length / Math.pow(2, fret / 12)

    // Fretboard width tapers from nut to heel
    const t = distance / params.neck_length
    const width = params.nut_width + t * (params.heel_width - params.nut_width)

    // Calculate radius (compound if enabled)
    let radius: number
    if (params.compound_radius) {
      // Interpolate between nut radius and heel radius
      radius =
        params.fretboard_radius +
        t * (params.fretboard_radius_heel - params.fretboard_radius)
    } else {
      radius = params.fretboard_radius
    }

    // Generate cross-section with radius
    for (let j = 0; j <= 10; j++) {
      const w_t = j / 10
      const y = (w_t - 0.5) * width
      const z = calculateFretboardZ(w_t, radius)

      points.push({
        x: distance,
        y,
        z: z + params.fretboard_offset
      })
    }
  }

  return points
}

/**
 * Calculate Z for fretboard with cylindrical radius
 */
function calculateFretboardZ(t: number, radius: number): number {
  const centerOffset = 0.5
  const dist = Math.abs(t - centerOffset)

  // Circular arc formula
  const chord = dist * 2
  const sagitta =
    radius - Math.sqrt(Math.pow(radius, 2) - Math.pow(chord * radius, 2))

  return sagitta
}

/**
 * Unit Conversion Utilities
 */
export function mmToInch(mm: number): number {
  return mm * INCH_PER_MM
}

export function inchToMm(inch: number): number {
  return inch * MM_PER_INCH
}

/**
 * Convert all dimensional parameters between units
 */
export function convertStratParameters(
  params: Partial<StratNeckParameters>,
  fromUnits: 'mm' | 'inch',
  toUnits: 'mm' | 'inch'
): Partial<StratNeckParameters> {
  if (fromUnits === toUnits) {
    return { ...params, units: toUnits }
  }

  const convert = fromUnits === 'mm' ? mmToInch : inchToMm

  // List of dimensional fields to convert
  const dimensionalFields: (keyof StratNeckParameters)[] = [
    'blank_length',
    'blank_width',
    'blank_thickness',
    'scale_length',
    'nut_width',
    'heel_width',
    'neck_length',
    'fretboard_radius',
    'fretboard_offset',
    'fretboard_radius_heel',
    'thickness_1st_fret',
    'thickness_12th_fret',
    'shoulder_width',
    'headstock_length',
    'headstock_thickness',
    'headstock_taper',
    'tuner_spacing',
    'tuner_diameter',
    'truss_rod_channel_width',
    'truss_rod_channel_depth'
  ]

  const converted: Partial<StratNeckParameters> = { ...params, units: toUnits }

  dimensionalFields.forEach((field) => {
    const value = params[field]
    if (value !== undefined && typeof value === 'number') {
      ;(converted as Record<string, unknown>)[field] = convert(value)
    }
  })

  // Convert string tree positions array
  if (params.string_tree_positions) {
    converted.string_tree_positions = params.string_tree_positions.map(convert)
  }

  return converted
}

/**
 * Parameter Validation Rules (in inches)
 */
interface ValidationRule {
  min: number
  max: number
  unit: string
  critical?: boolean
}

const STRAT_VALIDATION_RULES: Record<string, ValidationRule> = {
  scale_length: { min: 24, max: 26, unit: 'inch', critical: true }, // Fender range
  nut_width: { min: 1.5, max: 1.875, unit: 'inch' }, // 1.65" to 1.875" typical
  heel_width: { min: 2.0, max: 2.75, unit: 'inch' },
  blank_length: { min: 24, max: 36, unit: 'inch' },
  blank_width: { min: 2.5, max: 4.0, unit: 'inch' },
  blank_thickness: { min: 0.75, max: 1.5, unit: 'inch' },
  neck_length: { min: 15, max: 22, unit: 'inch' }, // Longer than Gibson
  fretboard_radius: { min: 7.25, max: 16, unit: 'inch' }, // 7.25" vintage to 16" modern
  fretboard_offset: { min: 0, max: 0.375, unit: 'inch' },
  thickness_1st_fret: { min: 0.75, max: 1.0, unit: 'inch' },
  thickness_12th_fret: { min: 0.8, max: 1.1, unit: 'inch' },
  shoulder_width: { min: 0.3, max: 1.0, unit: 'ratio' }, // V-profile shoulder factor
  headstock_length: { min: 6, max: 10, unit: 'inch' },
  headstock_thickness: { min: 0.375, max: 0.625, unit: 'inch' },
  headstock_taper: { min: 0.5, max: 1.5, unit: 'inch' },
  tuner_spacing: { min: 0.75, max: 1.25, unit: 'inch' },
  tuner_diameter: { min: 0.25, max: 0.5, unit: 'inch' },
  truss_rod_channel_width: { min: 0.25, max: 0.5, unit: 'inch' },
  truss_rod_channel_depth: { min: 0.25, max: 0.5, unit: 'inch' }
}

/**
 * Validate Stratocaster neck parameters
 */
export function validateStratParameters(
  params: Partial<StratNeckParameters>
): StratValidationResult {
  const warnings: StratValidationWarning[] = []
  let hasErrors = false

  Object.keys(STRAT_VALIDATION_RULES).forEach((field) => {
    const value = params[field as keyof StratNeckParameters]
    if (value === undefined || typeof value !== 'number') return

    const rule = STRAT_VALIDATION_RULES[field]

    // Convert value to inches for validation if params are in mm
    let valueInInches = value
    if (params.units === 'mm' && rule.unit === 'inch') {
      valueInInches = mmToInch(value)
    }

    if (valueInInches < rule.min || valueInInches > rule.max) {
      const severity = rule.critical ? 'error' : 'warning'
      if (rule.critical) hasErrors = true

      warnings.push({
        field,
        message: `${field}: ${value.toFixed(3)} ${params.units || 'inch'} is outside valid range (${rule.min}-${rule.max} ${rule.unit})`,
        severity
      })
    }
  })

  // Strat-specific validations
  // 1. Compound radius: heel radius should be >= nut radius
  if (params.compound_radius && params.fretboard_radius && params.fretboard_radius_heel) {
    if (params.fretboard_radius_heel < params.fretboard_radius) {
      warnings.push({
        field: 'fretboard_radius_heel',
        message:
          'Compound radius: heel radius should be >= nut radius (flatter at high frets)',
        severity: 'warning'
      })
    }
  }

  // 2. Neck thickness should increase from 1st to 12th fret
  if (params.thickness_1st_fret && params.thickness_12th_fret) {
    if (params.thickness_12th_fret < params.thickness_1st_fret) {
      warnings.push({
        field: 'thickness_12th_fret',
        message: 'Neck thickness should increase toward heel',
        severity: 'warning'
      })
    }
  }

  // 3. Heel width should be >= nut width
  if (params.nut_width && params.heel_width) {
    if (params.heel_width < params.nut_width) {
      warnings.push({
        field: 'heel_width',
        message: 'Heel width should be >= nut width for proper taper',
        severity: 'warning'
      })
    }
  }

  // 4. V-profile needs shoulder width
  if (
    (params.profile_type === 'V' || params.profile_type === 'soft_V') &&
    !params.shoulder_width
  ) {
    warnings.push({
      field: 'shoulder_width',
      message: 'V-profile needs shoulder_width parameter (0.3-1.0)',
      severity: 'warning'
    })
  }

  return {
    valid: !hasErrors,
    warnings
  }
}

/**
 * Export neck geometry as JSON
 */
export function exportStratNeckAsJSON(geometry: StratNeckGeometry): string {
  return JSON.stringify(geometry, null, 2)
}

/**
 * Get default Stratocaster parameters (Modern C profile)
 */
export function getDefaultStratParams(): StratNeckParameters {
  return {
    // Blank dimensions
    blank_length: 28,
    blank_width: 3.0,
    blank_thickness: 1.0,

    // Scale and dimensions (Standard Strat)
    scale_length: 25.5, // KEY DIFFERENCE: 25.5" vs 24.75" Les Paul
    nut_width: 1.65, // Standard Strat nut
    heel_width: 2.25,
    neck_length: 19, // Longer than Les Paul due to 25.5" scale

    // Fretboard (Modern Strat specs)
    fretboard_radius: 9.5, // Modern Strat (vintage was 7.25")
    fretboard_offset: 0.25,
    compound_radius: false,
    fretboard_radius_heel: 14, // If compound enabled
    include_fretboard: true,
    fret_count: 22, // Standard modern Strat

    // Profile
    profile_type: 'modern_C',
    thickness_1st_fret: 0.82,
    thickness_12th_fret: 0.92,
    shoulder_width: 0.7, // For V profiles

    // Headstock (flat, 6-in-line)
    headstock_length: 7.25,
    headstock_thickness: 0.5,
    headstock_taper: 1.0,
    tuner_spacing: 0.875,
    tuner_diameter: 0.375,
    string_tree_positions: [2.5, 5.0], // Two string trees

    // Truss rod
    truss_rod_channel_width: 0.375,
    truss_rod_channel_depth: 0.375,
    truss_rod_access: 'headstock',

    // Options
    alignment_pin_holes: false,
    skunk_stripe: true // Maple neck indicator
  }
}

/**
 * Get vintage Stratocaster parameters (1950s-60s specs)
 */
export function getVintageStratParams(): StratNeckParameters {
  return {
    ...getDefaultStratParams(),
    fretboard_radius: 7.25, // Vintage radius
    nut_width: 1.625, // Narrower vintage nut
    profile_type: 'V', // 50s style V
    fret_count: 21, // Vintage fret count
    thickness_1st_fret: 0.85,
    thickness_12th_fret: 0.95,
    shoulder_width: 0.8, // Sharper V
    compound_radius: false
  }
}

/**
 * Get 24-fret Strat parameters (extended range)
 */
export function get24FretStratParams(): StratNeckParameters {
  return {
    ...getDefaultStratParams(),
    fret_count: 24,
    neck_length: 20.5, // Extended for 24 frets
    fretboard_radius: 12, // Flatter for shredding
    compound_radius: true,
    fretboard_radius_heel: 16, // Very flat at high frets
    profile_type: 'modern_C',
    thickness_1st_fret: 0.78, // Thinner for speed
    thickness_12th_fret: 0.88
  }
}
