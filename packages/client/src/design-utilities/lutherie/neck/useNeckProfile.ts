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

import { reactive, computed, readonly, type ComputedRef } from 'vue'
import {
  radiusAtFret, boardWidthAtFret, sagittaHeight, stepoverMm, passCount,
  type FretboardSpec, type FretStation,
} from './useFretboard'

const INCH = 25.4

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * All 16 profile shapes across 4 families:
 *
 * Pure (9)     — constant cross-section nut to body
 *   C, C-soft, D, D-flat, U, U-deep, V-hard, V-soft, slim
 *
 * Compound (5) — shape morphs nut→body across a configurable blend window
 *   C→V, U→C, V→C, C→D, D→U
 *   Each is encoded as "nutShape→bodyShape".
 *   blendStartFret + blendEndFret in NeckProfileSpec define the window.
 *   smoothstep with blendTension (0=linear, 100=full S-curve).
 *
 * Asymmetric (2) — bass and treble sides differ
 *   asymC (bass-heavy, favours thumb-over), asymV (harder treble keel)
 */
export type ProfileShape =
  | 'C' | 'C-soft' | 'D' | 'D-flat' | 'U' | 'U-deep'
  | 'V-hard' | 'V-soft' | 'slim'
  | 'C→V' | 'U→C' | 'V→C' | 'C→D' | 'D→U'
  | 'asymC' | 'asymV'

export interface NeckProfileSpec {
  shape:          ProfileShape
  depth1mm:       number    // target total neck depth at 1st fret
  depth12mm:      number    // target total neck depth at 12th fret
  shoulderWidthMm:number    // neck width at first fret (≈ fretboard nut width)
  asymBassAddMm:  number    // extra depth on bass side (asymC only)

  // Fretboard coupling inputs (must match useFretboard spec)
  fbThicknessMm:  number
  fretWireHeightMm: number

  // Compound taper blend window (only used for C→V, U→C etc.)
  blendStartFret: number   // fret where shape transition begins (default 1)
  blendEndFret:   number   // fret where shape transition completes (default 12)
  blendTension:   number   // 0=linear, 100=full smoothstep

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

// ─── Shape exponent table for pure shapes ────────────────────────────────────

const SHAPE_EXP: Record<string, { exp: number; flat?: number; vFraction?: number }> = {
  'C':       { exp: 1.6 },
  'C-soft':  { exp: 2.0,  flat: 0.05 },
  'D':       { exp: 2.4,  flat: 0.10 },
  'D-flat':  { exp: 3.2,  flat: 0.15 },
  'U':       { exp: 1.1 },
  'U-deep':  { exp: 0.9 },
  'V-hard':  { exp: 1.0,  vFraction: 0.9 },
  'V-soft':  { exp: 1.0,  vFraction: 0.5 },
  'slim':    { exp: 4.0,  flat: 0.25 },
}

/** Compound taper routing table: "A→B" → [nutShape, bodyShape] */
const COMPOUND_SHAPES: Record<string, [string, string]> = {
  'C→V':  ['C',      'V-soft'],
  'U→C':  ['U',      'C'],
  'V→C':  ['V-soft', 'C'],
  'C→D':  ['C',      'D'],
  'D→U':  ['D',      'U'],
}

/**
 * Pure shape Y offset — negative = into the neck back.
 * Handles all 9 pure shapes via the exponent table.
 */
function pureShapeY(xNorm: number, depth: number, shape: string, asymAdd = 0): number {
  const a = Math.abs(xNorm)
  const cfg = SHAPE_EXP[shape]
  if (!cfg) return -depth * (1 - Math.pow(a, 1.6))

  if (cfg.vFraction !== undefined) {
    // V-blend: linear keel mixed with curved back
    const vPart = -depth * (1 - a * 0.95)
    const cPart = -depth * (1 - Math.pow(a, 1.6))
    return vPart * cfg.vFraction + cPart * (1 - cfg.vFraction)
  }

  const flat = cfg.flat ?? 0
  return -depth * (1 - Math.pow(a, cfg.exp) * (1 - flat))
}

/**
 * shapeY — evaluates the back profile Z at a given normalised X position.
 *
 * For compound tapers (C→V, U→C, etc.) the blend fraction is interpolated
 * from `blendT` (0=nut shape, 1=body shape) via smoothstep with `tension`.
 * The caller computes blendT from the fret position and blend window.
 *
 * For asymmetric shapes the bass side (xNorm < 0) gets `asymAdd` depth.
 */
export function shapeY(
  xNorm:   number,
  depth:   number,
  shape:   ProfileShape,
  asymAdd = 0,
  blendT  = 0,     // 0=nut shape, 1=body shape (compound only)
  tension = 50,    // 0=linear, 100=full smoothstep
): number {
  const a = Math.abs(xNorm)

  // ── Asymmetric shapes ─────────────────────────────────────────────────────
  if (shape === 'asymC') {
    const boost = xNorm < 0 ? asymAdd : 0
    return -(depth + boost) * (1 - Math.pow(a, 1.6))
  }
  if (shape === 'asymV') {
    const vFrac = xNorm < 0 ? 0.7 : 0.4   // harder keel on treble side
    const vPart = -depth * (1 - a * 0.95)
    const cPart = -depth * (1 - Math.pow(a, 1.6))
    return vPart * vFrac + cPart * (1 - vFrac)
  }

  // ── Compound taper shapes ─────────────────────────────────────────────────
  if (shape in COMPOUND_SHAPES) {
    const [nutShape, bodyShape] = COMPOUND_SHAPES[shape]
    const k = tension / 100
    const ts = blendT * blendT * (3 - 2 * blendT) * k + blendT * (1 - k)
    const yNut  = pureShapeY(xNorm, depth, nutShape,  asymAdd)
    const yBody = pureShapeY(xNorm, depth, bodyShape, asymAdd)
    return yNut * (1 - ts) + yBody * ts
  }

  // ── Pure shapes ───────────────────────────────────────────────────────────
  return pureShapeY(xNorm, depth, shape, asymAdd)
}

/** Sample the back profile curve into [x, y] mm points, with compound taper blend */
export function sampleProfile(
  backDepth: number,
  halfWidth: number,
  shape: ProfileShape,
  asymAdd = 0,
  blendT  = 0,
  tension = 50,
  steps = 64,
): [number, number][] {
  return Array.from({ length: steps + 1 }, (_, i) => {
    const t = i / steps
    const x = (t - 0.5) * halfWidth * 2
    const xn = x / halfWidth
    const y = shapeY(xn, backDepth, shape, asymAdd, blendT, tension)
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
  // Compound taper blend window
  blendStartFret:   1,
  blendEndFret:     12,
  blendTension:     50,
  ballNoseMm:       12,
  stepoverPct:      20,
  feedMmMin:        1500,
  depthOfCutMm:     0.5,
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useNeckProfile(
  fbSpec: FretboardSpec,
  fretStations: ComputedRef<FretStation[]>,  // ComputedRef — stays live when fretboard spec changes
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


  // ── Blend fraction at fret n (for compound taper shapes) ─────────────────
  // Returns 0 at nut end of blend window, 1 at body end.
  // Pure shapes and asymmetric shapes ignore this value (blendT=0).
  function blendTAtFret(n: number): number {
    const isCompound = spec.shape in {
      'C→V': 1, 'U→C': 1, 'V→C': 1, 'C→D': 1, 'D→U': 1,
    }
    if (!isCompound) return 0
    const start = spec.blendStartFret
    const end   = spec.blendEndFret
    if (end <= start) return n >= end ? 1 : 0
    return Math.max(0, Math.min(1, (n - start) / (end - start)))
  }

  // ── Profile stations ───────────────────────────────────────────────────────

  const profileStations = computed<ProfileStation[]>(() =>
    fretStations.value.map(st => {
      const bd  = backDepth(st.fret)
      const hw  = neckWidthAt(st.fret) / 2
      const pts = sampleProfile(bd, hw, spec.shape, spec.asymBassAddMm, blendTAtFret(st.fret), spec.blendTension)
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
      const blendT = blendTAtFret(n)
      const zBack = shapeY(xn, bd, spec.shape, spec.asymBassAddMm, blendT, spec.blendTension)
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
