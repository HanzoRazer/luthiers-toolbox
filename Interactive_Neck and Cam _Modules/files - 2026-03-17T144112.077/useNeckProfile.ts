/**
 * useNeckProfile
 *
 * Reactive composable for neck back profile geometry.
 * Tightly coupled to useFretboard — back depth at every station
 * is computed as:
 *
 *   back_depth(n) = target_depth(n) - fret_wire_height
 *                  - fretboard_thickness - crown_compensation(n)
 *
 * where crown_compensation(n) = sagittaHeight(radiusAtFret(n), boardWidthAtFret(n))
 *
 * This means a compound radius fretboard produces a varying back depth
 * even with constant target total depth — the back profile must account
 * for the changing crown height along the length.
 *
 * Profile shapes: C, D, U, V, asymC (asymmetric bass-heavy), slim (Wizard)
 * Each shape is a parametric curve: y(x) = -depth × f(x/halfWidth)
 * where f() is the shape function, defined analytically.
 *
 * Produces:
 *   - profileStations[]    — cross-section at every key fret
 *   - couplingBreakdown()  — the compensation equation per fret
 *   - toolpasses()         — ball-nose X/Z coordinates per station
 *   - G-code               — back profile sweep program
 *   - DXF payload          — merges into neck_profile_export.py
 */

import { reactive, computed, readonly } from 'vue'
import {
  radiusAtFret, boardWidthAtFret, sagittaHeight, stepoverMm, passCount,
  type FretboardSpec, type FretStation,
} from './useFretboard'

const INCH = 25.4

// ─── Types ────────────────────────────────────────────────────────────────────

export type ProfileShape = 'C' | 'D' | 'U' | 'V' | 'asymC' | 'slim'

export interface NeckProfileSpec {
  shape:          ProfileShape
  depth1mm:       number    // target total neck depth at 1st fret
  depth12mm:      number    // target total neck depth at 12th fret
  shoulderWidthMm:number    // neck width at first fret (≈ fretboard nut width)
  asymBassAddMm:  number    // extra depth on bass side (asymC only)

  // Fretboard coupling inputs (must match useFretboard spec)
  fbThicknessMm:  number
  fretWireHeightMm: number

  // CNC
  ballNoseMm:     number
  stepoverPct:    number
  feedMmMin:      number
  depthOfCutMm:   number
}

export interface ProfileStation {
  fret:           number
  positionMm:     number
  targetDepthMm:  number    // total depth nut→fret top
  crownCompMm:    number    // fretboard crown compensation
  backDepthMm:    number    // wood behind fretboard centre
  widthMm:        number    // neck width at this station
  radiusInch:     number    // fretboard radius at this station
  profilePoints:  [number, number][]  // [x, y] mm relative to spine
}

export interface CouplingBreakdown {
  fret:              number
  targetTotal:       number
  minusFretWire:     number
  minusFBThickness:  number
  minusCrownComp:    number
  equalsBackDepth:   number
}

export interface NeckProfileGate {
  key:    string
  status: 'pass' | 'warn' | 'fail'
  label:  string
}

// ─── Shape functions ──────────────────────────────────────────────────────────

/**
 * Returns y-offset (negative = into the neck) for a given normalised x (-1..1).
 * y = 0 at edges, y = -depth at spine.
 */
export function shapeY(
  xNorm: number,
  depth: number,
  shape: ProfileShape,
  asymAdd = 0,
): number {
  const a = Math.abs(xNorm)
  switch (shape) {
    case 'C':     return -depth * (1 - Math.pow(a, 1.6))
    case 'D':     return -depth * (1 - Math.pow(a, 2.4))
    case 'U':     return -depth * (1 - Math.pow(a, 1.1))
    case 'V':     return -depth * (1 - a * 0.85)
    case 'asymC': {
      const boost = xNorm < 0 ? asymAdd : 0
      return -(depth + boost) * (1 - Math.pow(a, 1.6))
    }
    case 'slim':  return -depth * (1 - Math.pow(a, 3.2))
    default:      return -depth * (1 - Math.pow(a, 1.6))
  }
}

/** Sample the back profile curve into [x, y] mm points */
export function sampleProfile(
  backDepth: number,
  halfWidth: number,
  shape: ProfileShape,
  asymAdd = 0,
  steps = 64,
): [number, number][] {
  return Array.from({ length: steps + 1 }, (_, i) => {
    const t = i / steps
    const x = (t - 0.5) * halfWidth * 2
    const xn = x / halfWidth
    const y = shapeY(xn, backDepth, shape, asymAdd)
    return [x, y] as [number, number]
  })
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_SPEC: NeckProfileSpec = {
  shape:            'C',
  depth1mm:         21,
  depth12mm:        23,
  shoulderWidthMm:  43,
  asymBassAddMm:    0,
  fbThicknessMm:    6,
  fretWireHeightMm: 1.0,
  ballNoseMm:       12,
  stepoverPct:      20,
  feedMmMin:        1500,
  depthOfCutMm:     0.5,
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useNeckProfile(
  fbSpec: FretboardSpec,
  fretStations: FretStation[],
) {
  const spec = reactive<NeckProfileSpec>({ ...DEFAULT_SPEC })

  // ── Target depth interpolation (linear nut→12th, held flat 12th→last) ──────
  function targetDepth(n: number): number {
    if (n <= 12) return spec.depth1mm + (spec.depth12mm - spec.depth1mm) * (n / 12)
    return spec.depth12mm
  }

  // ── Crown compensation from fretboard geometry ─────────────────────────────
  function crownComp(n: number): number {
    const r = radiusAtFret(n, fbSpec.fretCount, fbSpec.r1Inch, fbSpec.r2Inch, fbSpec.radiusType)
    const w = boardWidthAtFret(n, fbSpec.fretCount, fbSpec.nutWidthMm, fbSpec.width12Mm)
    return sagittaHeight(r, w)
  }

  // ── Back depth after all compensation ─────────────────────────────────────
  function backDepth(n: number): number {
    return targetDepth(n)
      - spec.fretWireHeightMm
      - spec.fbThicknessMm
      - crownComp(n)
  }

  // ── Width at fret n (linear taper nut → last) ──────────────────────────────
  function neckWidthAt(n: number): number {
    const wLast = spec.shoulderWidthMm + (56 - spec.shoulderWidthMm) * 2
    return spec.shoulderWidthMm + (wLast - spec.shoulderWidthMm) * (n / fbSpec.fretCount)
  }

  // ── Profile stations ───────────────────────────────────────────────────────

  const profileStations = computed<ProfileStation[]>(() =>
    fretStations.map(st => {
      const bd  = backDepth(st.fret)
      const hw  = neckWidthAt(st.fret) / 2
      const pts = sampleProfile(bd, hw, spec.shape, spec.asymBassAddMm)
      return {
        fret:          st.fret,
        positionMm:    st.positionMm,
        targetDepthMm: targetDepth(st.fret),
        crownCompMm:   crownComp(st.fret),
        backDepthMm:   bd,
        widthMm:       hw * 2,
        radiusInch:    st.radiusInch,
        profilePoints: pts,
      }
    })
  )

  // ── Coupling breakdown (for UI display) ───────────────────────────────────

  function couplingBreakdown(n: number): CouplingBreakdown {
    return {
      fret:             n,
      targetTotal:      targetDepth(n),
      minusFretWire:    spec.fretWireHeightMm,
      minusFBThickness: spec.fbThicknessMm,
      minusCrownComp:   crownComp(n),
      equalsBackDepth:  backDepth(n),
    }
  }

  // ── Ball-nose toolpath passes for back profile at fret n ──────────────────

  function backProfilePasses(n: number) {
    const st  = profileStations.value.find(s => s.fret === n)
    if (!st) return []
    const hw   = st.widthMm / 2
    const bd   = st.backDepthMm
    const bnR  = spec.ballNoseMm / 2
    const step = stepoverMm(spec.ballNoseMm, spec.stepoverPct)
    const n2   = passCount(st.widthMm, spec.ballNoseMm, spec.stepoverPct)
    const y    = st.positionMm

    return Array.from({ length: n2 }, (_, i) => {
      const x   = -(hw + bnR) + i * step
      const xn  = Math.abs(x) <= hw ? x / hw : Math.sign(x)
      const zBack = shapeY(xn, bd, spec.shape, spec.asymBassAddMm)
      // Tool centre sits above the back surface by ball radius
      const zTool = zBack - bnR   // negative = below workpiece top face
      return {
        pass: i + 1,
        x:    +x.toFixed(3),
        z:    +zTool.toFixed(4),
        gcode: `G01 X${x.toFixed(3)} Y${y.toFixed(3)} Z${zTool.toFixed(4)} F${spec.feedMmMin}`,
      }
    })
  }

  // ── Full back profile G-code ───────────────────────────────────────────────

  function generateBackGCode(): string {
    const lines = [
      `; Production Shop — Neck back profile sweep`,
      `; Shape: ${spec.shape}  depth 1st=${spec.depth1mm}mm  12th=${spec.depth12mm}mm`,
      `; Ball-nose Ø${spec.ballNoseMm}mm  step ${stepoverMm(spec.ballNoseMm, spec.stepoverPct).toFixed(2)}mm`,
      `; Fretboard coupling: thickness=${spec.fbThicknessMm}mm  fret wire=${spec.fretWireHeightMm}mm`,
      `; Crown compensation: ${fbSpec.radiusType} radius ${fbSpec.r1Inch}"${fbSpec.radiusType === 'compound' ? `→${fbSpec.r2Inch}"` : ''}`,
      ``,
      `G21  ; mm`,
      `G90  ; absolute`,
      `G00 Z5.000`,
      ``,
    ]

    for (const st of profileStations.value) {
      const passes = backProfilePasses(st.fret)
      if (!passes.length) continue

      lines.push(
        `; === ${st.fret === 0 ? 'NUT' : `Fret ${st.fret}`}  Y=${st.positionMm.toFixed(3)}mm ===`,
        `; back=${st.backDepthMm.toFixed(3)}mm  crown_comp=${st.crownCompMm.toFixed(4)}mm  w=${st.widthMm.toFixed(2)}mm`,
        `; ${passes.length} passes  step=${stepoverMm(spec.ballNoseMm, spec.stepoverPct).toFixed(2)}mm`,
        `G00 Y${st.positionMm.toFixed(3)}`,
      )

      passes.forEach((p, i) => {
        if (i === 0) {
          lines.push(
            `G00 X${p.x} Z${(p.z + 5).toFixed(4)}`,
            `G01 Z${p.z} F${(spec.feedMmMin * 0.4).toFixed(0)}  ; plunge`,
          )
        } else {
          lines.push(p.gcode)
        }
      })

      lines.push(`G00 Z5.000`, ``)
    }

    lines.push(`M30  ; end of program`)
    return lines.join('\n')
  }

  // ── Gates ──────────────────────────────────────────────────────────────────

  const gates = computed<NeckProfileGate[]>(() => {
    const G: NeckProfileGate[] = []
    const bd0  = backDepth(0)
    const bd12 = backDepth(12)

    if (bd0 < 8)
      G.push({ key:'bd0',  status:'fail', label:`Back depth at nut ${bd0.toFixed(2)}mm — below 8mm minimum` })
    else
      G.push({ key:'bd0',  status:'pass', label:`Back depth at nut ${bd0.toFixed(2)}mm OK` })

    if (bd12 < 9)
      G.push({ key:'bd12', status:'fail', label:`Back depth at 12th ${bd12.toFixed(2)}mm — below 9mm minimum` })
    else
      G.push({ key:'bd12', status:'pass', label:`Back depth at 12th ${bd12.toFixed(2)}mm OK` })

    if (spec.depth12mm <= spec.depth1mm)
      G.push({ key:'taper', status:'warn', label:`12th depth ≤ 1st — most necks taper thicker toward body` })
    else
      G.push({ key:'taper', status:'pass', label:`Depth taper ${spec.depth1mm}→${spec.depth12mm}mm valid` })

    // Crown variation check
    const crownDelta = Math.abs(crownComp(0) - crownComp(fbSpec.fretCount))
    if (fbSpec.radiusType === 'compound' && crownDelta > 0.3)
      G.push({ key:'crown', status:'warn', label:`Crown Δ ${crownDelta.toFixed(3)}mm nut→body — back depth varies by same amount` })
    else
      G.push({ key:'crown', status:'pass', label:`Crown variation ${crownDelta.toFixed(3)}mm accounted for in back depth` })

    return G
  })

  // ── DXF / export payload ──────────────────────────────────────────────────

  const exportPayload = computed(() => ({
    shape:             spec.shape,
    depth_1st_mm:      spec.depth1mm,
    depth_12th_mm:     spec.depth12mm,
    shoulder_width_mm: spec.shoulderWidthMm,
    asym_bass_add_mm:  spec.asymBassAddMm,
    fb_thickness_mm:   spec.fbThicknessMm,
    fret_wire_mm:      spec.fretWireHeightMm,
    ball_nose_mm:      spec.ballNoseMm,
    stepover_pct:      spec.stepoverPct,
    feed_mm_min:       spec.feedMmMin,
    profile_stations:  profileStations.value.map(st => ({
      fret:           st.fret,
      position_mm:    +st.positionMm.toFixed(3),
      target_mm:      +st.targetDepthMm.toFixed(3),
      crown_comp_mm:  +st.crownCompMm.toFixed(4),
      back_depth_mm:  +st.backDepthMm.toFixed(4),
      width_mm:       +st.widthMm.toFixed(3),
    })),
  }))

  function setSpec<K extends keyof NeckProfileSpec>(key: K, value: NeckProfileSpec[K]) {
    (spec as any)[key] = value
  }

  return {
    spec:             readonly(spec),
    profileStations,
    gates,
    exportPayload,
    setSpec,
    backDepth,
    crownComp,
    targetDepth,
    neckWidthAt,
    couplingBreakdown,
    backProfilePasses,
    generateBackGCode,
    sampleProfile,
    shapeY,
  }
}
