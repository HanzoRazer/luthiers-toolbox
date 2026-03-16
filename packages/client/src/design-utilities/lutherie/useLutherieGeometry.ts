/**
 * useLutherieGeometry — Lutherie-specific geometry calculations
 *
 * The Production Shop — Scientific Calculator / Woodwork tab
 *
 * Three calculation families:
 *
 * 1. RIGHT TRIANGLE / COMPOUND ANGLES
 *    Dovetail neck joints, scarf joints, headstock angles, binding miters.
 *    Given any two of: rise, run, hypotenuse, angle → solve the full triangle.
 *    Compound angle mode: combines two planes (e.g. dovetail cheek + bed angle).
 *
 * 2. PITCH / BRACE GEOMETRY
 *    Rafter-style rise/run adapted for fan bracing and curved brace layouts.
 *    Given rise + run → pitch angle, brace length, cut angle at heel/foot.
 *    Supports multiple braces with shared rise and individual run values.
 *
 * 3. ARC / CIRCLE TOOLS
 *    Rosette radii, purfling bend radius, binding curve on body outline.
 *    Circle: radius, diameter, circumference, arc length for given central angle.
 *    Chord: chord length and sagitta (rise) from radius + arc angle — used for
 *    radius dish depth, fretboard radius, brace camber.
 *    Bend allowance: minimum bend radius for purfling/binding stock by thickness.
 */

import { ref, computed } from 'vue'

const DEG = Math.PI / 180
const RAD = 180 / Math.PI

// ============================================================================
// TYPES
// ============================================================================

export type RightTriangleSolveMode =
  | 'rise_run'       // given rise + run → angle, hyp
  | 'angle_run'      // given angle + run → rise, hyp
  | 'angle_rise'     // given angle + rise → run, hyp
  | 'angle_hyp'      // given angle + hyp → rise, run
  | 'rise_hyp'       // given rise + hyp → angle, run

export interface RightTriangleInput {
  mode: RightTriangleSolveMode
  rise: number     // mm or inches
  run: number      // mm or inches
  hyp: number      // hypotenuse
  angleDeg: number // degrees
}

export interface RightTriangleResult {
  rise: number
  run: number
  hyp: number
  angleDeg: number          // angle at base (between run and hypotenuse)
  complementDeg: number     // 90 - angleDeg
  slopeRatio: string        // e.g. "1:12"
  pitchPercent: number      // rise/run × 100
  valid: boolean
  error?: string
}

export interface CompoundAngleInput {
  /** Primary angle — e.g. neck angle in the longitudinal plane (degrees) */
  primaryDeg: number
  /** Secondary angle — e.g. neck angle in the lateral plane (degrees) */
  secondaryDeg: number
}

export interface CompoundAngleResult {
  /** True compound angle between the two planes */
  compoundDeg: number
  /** Miter angle for the saw (blade tilted to compoundDeg, fence at 0°) */
  miterDeg: number
  /** Bevel angle for the saw (blade vertical, fence at miterDeg) */
  bevelDeg: number
  valid: boolean
}

export interface BraceGeometryInput {
  /** Rise of the brace (height at crown, mm) */
  riseMm: number
  /** Run values for each brace (horizontal span, mm) */
  runsMm: number[]
  /** Optional: cap radius for curved braces (mm, 0 = straight) */
  radiusMm: number
}

export interface BraceResult {
  runMm: number
  braceLength: number       // hypotenuse = actual brace length needed
  pitchAngleDeg: number     // angle at foot
  cutAngleDeg: number       // 90 - pitchAngleDeg = cut angle at table saw
  heightAtCenter: number    // height at midpoint of span (for curved braces)
}

export interface BraceGeometryResult {
  braces: BraceResult[]
  valid: boolean
  error?: string
}

export interface ArcCircleInput {
  radiusMm: number
  /** Central angle subtended by the arc (degrees) */
  centralAngleDeg: number
}

export interface ArcCircleResult {
  radiusMm: number
  diameterMm: number
  circumferenceMm: number
  arcLengthMm: number       // arc for given central angle
  chordLengthMm: number     // straight-line chord
  sagittaMm: number         // rise from chord to arc crown
  valid: boolean
  error?: string
}

export interface BendAllowanceInput {
  thicknessMm: number
  /** Material type — affects minimum bend radius multiplier */
  material: BendMaterial
}

export type BendMaterial = 'abs_plastic' | 'maple_veneer' | 'purfling_bwb' | 'solid_binding' | 'custom'

export interface BendAllowanceResult {
  minRadiusMm: number       // minimum safe bend radius
  minRadiusIn: number
  /** Kerf spacing for kerfed lining (mm between kerfs for this radius) */
  kerfSpacingMm: number
  /** Number of kerfs needed for a full 360° bend */
  kerfsPerCircle: number
  warning?: string
}

// ============================================================================
// BEND MATERIAL REFERENCE
// ============================================================================

export const BEND_MATERIALS: Record<BendMaterial, { label: string; minRadiusMultiplier: number }> = {
  abs_plastic:    { label: 'ABS plastic binding',     minRadiusMultiplier: 5  },
  maple_veneer:   { label: 'Maple veneer (0.6mm)',     minRadiusMultiplier: 30 },
  purfling_bwb:   { label: 'B/W/B purfling strip',    minRadiusMultiplier: 20 },
  solid_binding:  { label: 'Solid wood binding strip', minRadiusMultiplier: 50 },
  custom:         { label: 'Custom',                   minRadiusMultiplier: 25 },
}

// ============================================================================
// PURE CALCULATION FUNCTIONS
// ============================================================================

export function solveRightTriangle(input: RightTriangleInput): RightTriangleResult {
  let { rise, run, hyp, angleDeg } = input
  let valid = true
  let error: string | undefined

  try {
    switch (input.mode) {
      case 'rise_run':
        if (run <= 0) throw new Error('Run must be > 0')
        angleDeg = Math.atan2(rise, run) * RAD
        hyp = Math.sqrt(rise * rise + run * run)
        break
      case 'angle_run':
        if (run <= 0) throw new Error('Run must be > 0')
        if (angleDeg <= 0 || angleDeg >= 90) throw new Error('Angle must be 0–90°')
        rise = run * Math.tan(angleDeg * DEG)
        hyp = run / Math.cos(angleDeg * DEG)
        break
      case 'angle_rise':
        if (rise <= 0) throw new Error('Rise must be > 0')
        if (angleDeg <= 0 || angleDeg >= 90) throw new Error('Angle must be 0–90°')
        run = rise / Math.tan(angleDeg * DEG)
        hyp = rise / Math.sin(angleDeg * DEG)
        break
      case 'angle_hyp':
        if (hyp <= 0) throw new Error('Hypotenuse must be > 0')
        if (angleDeg <= 0 || angleDeg >= 90) throw new Error('Angle must be 0–90°')
        rise = hyp * Math.sin(angleDeg * DEG)
        run = hyp * Math.cos(angleDeg * DEG)
        break
      case 'rise_hyp':
        if (hyp <= 0) throw new Error('Hypotenuse must be > 0')
        if (rise >= hyp) throw new Error('Rise must be less than hypotenuse')
        angleDeg = Math.asin(rise / hyp) * RAD
        run = Math.sqrt(hyp * hyp - rise * rise)
        break
    }
  } catch (e) {
    valid = false
    error = e instanceof Error ? e.message : 'Invalid input'
  }

  const slopeBase = run > 0 ? Math.round(run / (rise || 1)) : 0
  const pitchPercent = run > 0 ? (rise / run) * 100 : 0

  return {
    rise: +rise.toFixed(4),
    run: +run.toFixed(4),
    hyp: +hyp.toFixed(4),
    angleDeg: +angleDeg.toFixed(4),
    complementDeg: +(90 - angleDeg).toFixed(4),
    slopeRatio: `1:${slopeBase}`,
    pitchPercent: +pitchPercent.toFixed(2),
    valid,
    error,
  }
}

export function solveCompoundAngle(input: CompoundAngleInput): CompoundAngleResult {
  const { primaryDeg, secondaryDeg } = input
  if (primaryDeg <= 0 || secondaryDeg <= 0) {
    return { compoundDeg: 0, miterDeg: 0, bevelDeg: 0, valid: false }
  }

  const p = primaryDeg * DEG
  const s = secondaryDeg * DEG

  // True compound angle
  const compound = Math.acos(Math.cos(p) * Math.cos(s)) * RAD

  // Miter and bevel for compound cuts (standard woodworking formula)
  const miter = Math.atan(Math.sin(p) / Math.tan(s)) * RAD
  const bevel = Math.atan(Math.sin(s) / Math.tan(p)) * RAD

  return {
    compoundDeg: +compound.toFixed(3),
    miterDeg: +miter.toFixed(3),
    bevelDeg: +bevel.toFixed(3),
    valid: true,
  }
}

export function solveBraceGeometry(input: BraceGeometryInput): BraceGeometryResult {
  if (input.riseMm <= 0) {
    return { braces: [], valid: false, error: 'Rise must be > 0' }
  }
  if (input.runsMm.length === 0) {
    return { braces: [], valid: false, error: 'At least one run value required' }
  }

  const braces: BraceResult[] = input.runsMm.map(runMm => {
    const braceLength = Math.sqrt(input.riseMm ** 2 + runMm ** 2)
    const pitchAngleDeg = Math.atan2(input.riseMm, runMm) * RAD
    const cutAngleDeg = 90 - pitchAngleDeg

    // Height at midpoint for curved braces (parabolic approximation)
    const heightAtCenter = input.radiusMm > 0
      ? input.radiusMm - Math.sqrt(Math.max(0, input.radiusMm ** 2 - (runMm / 2) ** 2))
      : input.riseMm / 2

    return {
      runMm: +runMm.toFixed(2),
      braceLength: +braceLength.toFixed(2),
      pitchAngleDeg: +pitchAngleDeg.toFixed(3),
      cutAngleDeg: +cutAngleDeg.toFixed(3),
      heightAtCenter: +heightAtCenter.toFixed(2),
    }
  })

  return { braces, valid: true }
}

export function solveArcCircle(input: ArcCircleInput): ArcCircleResult {
  const { radiusMm, centralAngleDeg } = input
  if (radiusMm <= 0) {
    return { radiusMm: 0, diameterMm: 0, circumferenceMm: 0, arcLengthMm: 0, chordLengthMm: 0, sagittaMm: 0, valid: false, error: 'Radius must be > 0' }
  }
  if (centralAngleDeg <= 0 || centralAngleDeg > 360) {
    return { radiusMm, diameterMm: radiusMm * 2, circumferenceMm: 2 * Math.PI * radiusMm, arcLengthMm: 0, chordLengthMm: 0, sagittaMm: 0, valid: false, error: 'Central angle must be 0–360°' }
  }

  const theta = centralAngleDeg * DEG
  const diameter = radiusMm * 2
  const circumference = 2 * Math.PI * radiusMm
  const arcLength = radiusMm * theta
  const chordLength = 2 * radiusMm * Math.sin(theta / 2)
  const sagitta = radiusMm * (1 - Math.cos(theta / 2))

  return {
    radiusMm: +radiusMm.toFixed(3),
    diameterMm: +diameter.toFixed(3),
    circumferenceMm: +circumference.toFixed(3),
    arcLengthMm: +arcLength.toFixed(3),
    chordLengthMm: +chordLength.toFixed(3),
    sagittaMm: +sagitta.toFixed(3),
    valid: true,
  }
}

export function solveBendAllowance(input: BendAllowanceInput): BendAllowanceResult {
  const mat = BEND_MATERIALS[input.material]
  const multiplier = mat?.minRadiusMultiplier ?? 25
  const minRadiusMm = input.thicknessMm * multiplier
  const minRadiusIn = minRadiusMm / 25.4

  // Kerf spacing: for a given radius, kerf spacing = 2 × sqrt(r² - (r-t)²)
  // where t = thickness of material being bent
  // Simplified: kerfSpacing ≈ 2 × sqrt(2 × r × t) for thin material
  const kerfSpacingMm = 2 * Math.sqrt(2 * minRadiusMm * input.thicknessMm)
  const kerfsPerCircle = Math.ceil((2 * Math.PI * minRadiusMm) / kerfSpacingMm)

  const warning = minRadiusMm < 50
    ? `Tight radius (${minRadiusMm.toFixed(1)} mm) — steam bending or kerfing required`
    : undefined

  return {
    minRadiusMm: +minRadiusMm.toFixed(1),
    minRadiusIn: +minRadiusIn.toFixed(3),
    kerfSpacingMm: +kerfSpacingMm.toFixed(1),
    kerfsPerCircle,
    warning,
  }
}

// ============================================================================
// LUTHERIE PRESETS
// ============================================================================

export const RIGHT_TRIANGLE_PRESETS = [
  { label: 'LP neck joint (4°)',    mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 4,    run: 100, rise: 0, hyp: 0 },
  { label: 'Scarf joint (13°)',     mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 13,   run: 100, rise: 0, hyp: 0 },
  { label: 'Headstock (14°)',       mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 14,   run: 100, rise: 0, hyp: 0 },
  { label: 'Headstock (17°)',       mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 17,   run: 100, rise: 0, hyp: 0 },
  { label: 'Dovetail neck (3.5°)',  mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 3.5,  run: 100, rise: 0, hyp: 0 },
  { label: 'Binding miter (45°)',   mode: 'angle_run' as RightTriangleSolveMode, angleDeg: 45,   run: 100, rise: 0, hyp: 0 },
]

export const ARC_PRESETS = [
  { label: 'Rosette inner (25mm r)',    radiusMm: 25,   centralAngleDeg: 360 },
  { label: 'Rosette outer (55mm r)',    radiusMm: 55,   centralAngleDeg: 360 },
  { label: 'Soundhole (50mm r)',        radiusMm: 50,   centralAngleDeg: 360 },
  { label: 'Lower bout (200mm r)',      radiusMm: 200,  centralAngleDeg: 180 },
  { label: 'Fretboard 12" radius',      radiusMm: 304.8,centralAngleDeg: 10  },
  { label: 'Fretboard 16" radius',      radiusMm: 406.4,centralAngleDeg: 10  },
  { label: 'Radius dish 15ft',          radiusMm: 4572, centralAngleDeg: 5   },
]

export const BRACE_PRESETS = [
  { label: 'X-brace top (12mm rise)', riseMm: 12, runsMm: [120, 110, 90], radiusMm: 0 },
  { label: 'Fan brace (8mm rise)',    riseMm: 8,  runsMm: [160, 130, 100, 80, 60], radiusMm: 0 },
  { label: 'Tone bar (6mm rise)',     riseMm: 6,  runsMm: [180, 150], radiusMm: 0 },
]

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useLutherieGeometry() {

  // --- Right triangle ---
  const triInput = ref<RightTriangleInput>({
    mode: 'angle_run',
    rise: 0,
    run: 100,
    hyp: 0,
    angleDeg: 4,
  })
  const triResult = computed(() => solveRightTriangle(triInput.value))

  // --- Compound angle ---
  const compInput = ref<CompoundAngleInput>({ primaryDeg: 4, secondaryDeg: 2 })
  const compResult = computed(() => solveCompoundAngle(compInput.value))

  // --- Brace geometry ---
  const braceInput = ref<BraceGeometryInput>({ riseMm: 12, runsMm: [120, 110, 90], radiusMm: 0 })
  const braceResult = computed(() => solveBraceGeometry(braceInput.value))

  // Add / remove brace runs
  function addBraceRun() {
    const last = braceInput.value.runsMm[braceInput.value.runsMm.length - 1] ?? 100
    braceInput.value.runsMm = [...braceInput.value.runsMm, Math.max(20, last - 20)]
  }
  function removeBraceRun(idx: number) {
    if (braceInput.value.runsMm.length > 1) {
      braceInput.value.runsMm = braceInput.value.runsMm.filter((_, i) => i !== idx)
    }
  }

  // --- Arc / circle ---
  const arcInput = ref<ArcCircleInput>({ radiusMm: 55, centralAngleDeg: 360 })
  const arcResult = computed(() => solveArcCircle(arcInput.value))

  // --- Bend allowance ---
  const bendInput = ref<BendAllowanceInput>({ thicknessMm: 2.0, material: 'solid_binding' })
  const bendResult = computed(() => solveBendAllowance(bendInput.value))

  function loadTriPreset(p: typeof RIGHT_TRIANGLE_PRESETS[number]) {
    triInput.value = { ...p }
  }
  function loadArcPreset(p: typeof ARC_PRESETS[number]) {
    arcInput.value = { ...p }
  }
  function loadBracePreset(p: typeof BRACE_PRESETS[number]) {
    braceInput.value = { ...p }
  }

  return {
    // Right triangle
    triInput, triResult,
    // Compound angle
    compInput, compResult,
    // Brace geometry
    braceInput, braceResult, addBraceRun, removeBraceRun,
    // Arc / circle
    arcInput, arcResult,
    // Bend allowance
    bendInput, bendResult,
    // Presets
    RIGHT_TRIANGLE_PRESETS, ARC_PRESETS, BRACE_PRESETS,
    BEND_MATERIALS,
    // Solve modes
    SOLVE_MODES: [
      { id: 'rise_run',    label: 'Rise + Run' },
      { id: 'angle_run',   label: 'Angle + Run' },
      { id: 'angle_rise',  label: 'Angle + Rise' },
      { id: 'angle_hyp',   label: 'Angle + Hyp' },
      { id: 'rise_hyp',    label: 'Rise + Hyp' },
    ] as const,
  }
}
