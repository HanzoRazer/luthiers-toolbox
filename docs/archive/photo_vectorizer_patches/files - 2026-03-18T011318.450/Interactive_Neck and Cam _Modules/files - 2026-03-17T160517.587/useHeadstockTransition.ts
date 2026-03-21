/**
 * useHeadstockTransition
 *
 * Models the zone where the neck back profile meets the headstock face —
 * the most structurally critical region of the instrument.
 *
 * Three surfaces interact:
 *   1. Neck back  — curved (C/D/U/V profile), runs from body toward nut
 *   2. Headstock plane — flat, pitched at angle α (0° Fender, 13–17° Gibson)
 *   3. Volute (optional) — convex Gaussian bump on the back, adds material
 *      at the weakest grain point where the pitch break creates short grain
 *
 * Coordinate convention (VINE-05 — matches repo cam/neck/):
 *   Y = 0   at nut centreline
 *   +Y      toward bridge/body
 *   -Y      toward headstock tip
 *   X = 0   centreline
 *   Z = 0   top face of neck (fretboard surface)
 *   -Z      into the neck back
 *
 * Blend geometry:
 *   The transition uses a Hermite smoothstep across a configurable
 *   window centred at blendCentreMm from the nut.  A tension parameter
 *   0-100 controls the sharpness: 0 = linear, 100 = full smoothstep.
 *
 * Volute geometry:
 *   Z_volute(y) = height × exp(-(y − y_centre)² / (2σ²))
 *   For scallop style: inverted, creates a concave decorative shape.
 *
 * Relationship to useCamSpec / useNeckProfile:
 *   This composable consumes headstock pitch angle from useCamSpec and
 *   neck back depth from useNeckProfile.  It produces the 3D surface
 *   patch that bridges between them for the BCAM finishing pass.
 */

import { reactive, computed, readonly } from 'vue'

// ─── Types ────────────────────────────────────────────────────────────────────

export type VoluteType = 'none' | 'gibson' | 'martin' | 'custom' | 'scallop'

export interface TransitionSpec {
  // Headstock
  headstockType:    'angled' | 'flat'
  pitchAngleDeg:    number    // 0° Fender → 17° Gibson
  hsThicknessMm:    number    // headstock face thickness at nut (~14mm)

  // Neck at nut
  neckDepthMm:      number    // total neck depth at 1st fret
  nutWidthMm:       number    // neck width at nut

  // Blend zone
  blendLengthMm:    number    // total span of the transition zone
  blendCentreMm:    number    // offset from nut (+ve=body side, -ve=HS side)
  blendTension:     number    // 0=linear, 100=full smoothstep

  // Volute
  voluteType:       VoluteType
  voluteHeightMm:   number    // peak height above back surface (mm)
  volutePositionMm: number    // Y offset from nut (negative = HS side, ~-12mm)
  volSigmaMm:       number    // Gaussian σ — controls width for gibson/custom/scallop
  volHalfWidthMm:   number    // tent half-width for martin (mm each side of peak)
  volSharpness:     number    // tent face sharpness: 1.0=linear pyramid, <1=flared, >1=steep

  // CNC
  ballNoseMm:       number    // finishing ball-nose diameter
  stepoverPct:      number
  feedMmMin:        number
}

export interface TransitionPoint {
  yMm:    number    // position along neck (VINE-05: Y=0 at nut)
  xMm:    number    // width position (X=0 centreline)
  zMm:    number    // depth (negative = into neck)
  region: 'neck' | 'blend' | 'headstock'
  voluteContrib: number  // mm added by volute at this point
}

export interface TransitionGate {
  key:    string
  status: 'pass' | 'warn' | 'fail'
  label:  string
}

// ─── Presets ──────────────────────────────────────────────────────────────────

export const TRANSITION_PRESETS: Record<string, Partial<TransitionSpec>> = {
  'Gibson 59 LP': {
    headstockType: 'angled', pitchAngleDeg: 17, hsThicknessMm: 14,
    neckDepthMm: 21.8, nutWidthMm: 43,
    blendLengthMm: 20, blendCentreMm: 4, blendTension: 65,
    voluteType: 'gibson', voluteHeightMm: 5, volutePositionMm: -14, volSigmaMm: 13,
    volHalfWidthMm: 14, volSharpness: 1.0,
  },
  'PRS Modern': {
    headstockType: 'angled', pitchAngleDeg: 10, hsThicknessMm: 13,
    neckDepthMm: 21, nutWidthMm: 43,
    blendLengthMm: 24, blendCentreMm: 6, blendTension: 55,
    voluteType: 'none', voluteHeightMm: 0, volutePositionMm: -10, volSigmaMm: 10,
    volHalfWidthMm: 10, volSharpness: 1.0,
  },
  'Fender Strat': {
    headstockType: 'flat', pitchAngleDeg: 0, hsThicknessMm: 14,
    neckDepthMm: 21, nutWidthMm: 42,
    blendLengthMm: 15, blendCentreMm: 3, blendTension: 40,
    voluteType: 'none', voluteHeightMm: 0, volutePositionMm: 0, volSigmaMm: 10,
    volHalfWidthMm: 10, volSharpness: 1.0,
  },
  'Martin OM': {
    // Traditional Martin acoustic — uses the faceted diamond/pyramid volute
    headstockType: 'angled', pitchAngleDeg: 15, hsThicknessMm: 14,
    neckDepthMm: 21.5, nutWidthMm: 44.5,
    blendLengthMm: 18, blendCentreMm: 3, blendTension: 60,
    voluteType: 'martin', voluteHeightMm: 6, volutePositionMm: -15,
    volSigmaMm: 11, volHalfWidthMm: 14, volSharpness: 0.8,
  },
  'Martin Pre-War D-28': {
    // Pre-war Martin — more pronounced diamond volute, higher pitch angle
    // h=6mm, half_width=14mm, sharpness=0.8 per classic D-28 measurements
    headstockType: 'angled', pitchAngleDeg: 15, hsThicknessMm: 14.5,
    neckDepthMm: 22, nutWidthMm: 44.5,
    blendLengthMm: 16, blendCentreMm: 2, blendTension: 58,
    voluteType: 'martin', voluteHeightMm: 6, volutePositionMm: -15,
    volSigmaMm: 11, volHalfWidthMm: 14, volSharpness: 0.8,
  },
}

// ─── Default ──────────────────────────────────────────────────────────────────

const DEFAULT_SPEC: TransitionSpec = {
  headstockType:    'angled',
  pitchAngleDeg:    14,
  hsThicknessMm:    14,
  neckDepthMm:      21,
  nutWidthMm:       43,
  blendLengthMm:    22,
  blendCentreMm:    5,
  blendTension:     50,
  voluteType:       'none',
  voluteHeightMm:   4,
  volutePositionMm: -12,
  volSigmaMm:       12,
  volHalfWidthMm:   14,
  volSharpness:     0.8,
  ballNoseMm:       9.525,   // 3/8" — repo T3 finish ball
  stepoverPct:      12,
  feedMmMin:        1200,
}

// ─── Pure geometry functions ──────────────────────────────────────────────────

/** Z of the headstock plane at Y position (VINE-05: Y=0 at nut, -Y toward HS) */
export function headstockPlaneZ(y: number, spec: TransitionSpec): number {
  const angR = spec.pitchAngleDeg * Math.PI / 180
  return -spec.hsThicknessMm + (-y) * Math.tan(angR)
}

/** Z of the neck back surface far from transition (constant at -neckDepthMm) */
export function neckBackZ(spec: TransitionSpec): number {
  return -spec.neckDepthMm
}

/** Hermite blend Z across the transition window */
export function blendZ(y: number, spec: TransitionSpec): number {
  const start = spec.blendCentreMm - spec.blendLengthMm / 2
  const end   = spec.blendCentreMm + spec.blendLengthMm / 2
  const t = Math.max(0, Math.min(1, (y - start) / spec.blendLengthMm))
  const k = spec.blendTension / 100
  // Hermite smoothstep with tension control
  const ts = t * t * (3 - 2 * t) * k + t * (1 - k)
  return neckBackZ(spec) * (1 - ts) + headstockPlaneZ(y, spec) * ts
}

/**
 * Volute contribution Z at position Y.
 *
 * Shape functions by type:
 *
 *   gibson / custom  — Gaussian bell curve: smooth swell, typical of Gibson
 *     Z = h × exp(-(y - y_c)² / 2σ²)
 *
 *   martin           — Faceted tent / truncated pyramid: the classic pre-war
 *     Martin diamond volute.  Two straight (or slightly curved) faces meeting
 *     at a ridge.  Shape controlled by half_width and sharpness:
 *       t = max(0, 1 - |y - y_c| / half_width)      ← normalised 0→1
 *       Z = h × t^sharpness
 *     sharpness = 1.0  → true linear pyramid (flat faces)
 *     sharpness < 1.0  → flared base, softer transition at edges (typical 0.7–0.9)
 *     sharpness > 1.0  → steep sides, narrow crown
 *
 *   scallop          — Inverted Gaussian: concave decorative hollow
 *     Z = -h × 0.6 × exp(-(y - y_c)² / 2σ²)
 */
export function voluteZ(y: number, spec: TransitionSpec): number {
  if (spec.voluteType === 'none') return 0

  const dy = y - spec.volutePositionMm

  if (spec.voluteType === 'martin') {
    // Tent / truncated pyramid — the Martin diamond volute
    const t = Math.max(0, 1 - Math.abs(dy) / spec.volHalfWidthMm)
    return spec.voluteHeightMm * Math.pow(t, spec.volSharpness)
  }

  // Gaussian — gibson, custom, scallop
  const g = Math.exp(-dy * dy / (2 * spec.volSigmaMm * spec.volSigmaMm))
  if (spec.voluteType === 'scallop') return -spec.voluteHeightMm * g * 0.6
  return spec.voluteHeightMm * g
}

/** Total back surface Z at Y — determines which region we're in */
export function surfaceZ(y: number, spec: TransitionSpec): number {
  const start = spec.blendCentreMm - spec.blendLengthMm / 2
  const end   = spec.blendCentreMm + spec.blendLengthMm / 2

  let base: number
  if (y < start)      base = headstockPlaneZ(y, spec)
  else if (y <= end)  base = blendZ(y, spec)
  else                base = neckBackZ(spec)

  return base + voluteZ(y, spec)
}

/** Region classification at Y */
export function regionAt(y: number, spec: TransitionSpec): 'neck' | 'blend' | 'headstock' {
  const start = spec.blendCentreMm - spec.blendLengthMm / 2
  const end   = spec.blendCentreMm + spec.blendLengthMm / 2
  if (y < start) return 'headstock'
  if (y <= end)  return 'blend'
  return 'neck'
}

/** Thickness of material at the geometrically weakest point (short grain zone) */
export function thinPointMm(spec: TransitionSpec): number {
  // The thin point is at the volute position (or ~-10mm if no volute)
  const y = spec.voluteType !== 'none' ? spec.volutePositionMm : -10
  return -headstockPlaneZ(y, spec)   // positive thickness
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useHeadstockTransition() {
  const spec = reactive<TransitionSpec>({ ...DEFAULT_SPEC })

  // ── Sample surface for canvas / 3D export ─────────────────────────────────

  const surfaceSamples = computed<TransitionPoint[]>(() => {
    const samples: TransitionPoint[] = []
    const yMin = -55, yMax = 60, yStep = 1
    const xSteps = 12

    for (let y = yMin; y <= yMax; y += yStep) {
      const hw = spec.nutWidthMm / 2 + (y > 0 ? y * 0.07 : 0)
      for (let xi = 0; xi <= xSteps; xi++) {
        const xn = (xi / xSteps) * 2 - 1
        const x  = xn * hw
        const zBase = surfaceZ(y, spec)
        const vContrib = voluteZ(y, spec)
        samples.push({
          yMm:   y,
          xMm:   x,
          zMm:   zBase,
          region: regionAt(y, spec),
          voluteContrib: vContrib,
        })
      }
    }
    return samples
  })

  // ── Derived geometry summary ───────────────────────────────────────────────

  const derived = computed(() => {
    const angR   = spec.pitchAngleDeg * Math.PI / 180
    const thin   = thinPointMm(spec)
    const hsDropAt30mm = (30 * Math.tan(angR))
    const blendEntry   = surfaceZ(spec.blendCentreMm - spec.blendLengthMm / 2, spec)
    const blendExit    = surfaceZ(spec.blendCentreMm + spec.blendLengthMm / 2, spec)
    const voluteSpan   = spec.volSigmaMm * 4   // 2σ each side

    return {
      thinPointMm:      +thin.toFixed(2),
      hsDropAt30mm:     +hsDropAt30mm.toFixed(2),
      blendEntryZMm:    +blendEntry.toFixed(3),
      blendExitZMm:     +blendExit.toFixed(3),
      blendDeltaMm:     +(blendExit - blendEntry).toFixed(3),
      voluteSpanMm:     +voluteSpan.toFixed(1),
      // CNC pass count for transition zone
      passCount:        Math.ceil((spec.nutWidthMm + spec.ballNoseMm) / (spec.ballNoseMm * spec.stepoverPct / 100)) + 1,
    }
  })

  // ── Gates ──────────────────────────────────────────────────────────────────

  const gates = computed<TransitionGate[]>(() => {
    const G: TransitionGate[] = []
    const thin = derived.value.thinPointMm

    // Structural thin point
    if (spec.headstockType === 'angled') {
      if (thin < 8)
        G.push({ key:'thin', status:'fail', label:`Thin point ${thin}mm — below 8mm minimum. Grain failure risk. Reduce pitch angle or add volute.` })
      else if (thin < 12)
        G.push({ key:'thin', status:'warn', label:`Thin point ${thin}mm — volute strongly recommended for ${spec.pitchAngleDeg}° pitch.` })
      else
        G.push({ key:'thin', status:'pass', label:`Thin point ${thin}mm — adequate material at grain weak point.` })
    } else {
      G.push({ key:'thin', status:'pass', label:`Flat headstock — no grain weakness. Volute is decorative only.` })
    }

    // Volute adequacy for angled headstocks
    if (spec.headstockType === 'angled' && spec.voluteType !== 'none') {
      if (spec.voluteHeightMm < 3 && spec.pitchAngleDeg > 12)
        G.push({ key:'vol', status:'warn', label:`Volute ${spec.voluteHeightMm.toFixed(1)}mm may be marginal for ${spec.pitchAngleDeg}° — Gibson uses 4–6mm.` })
      else
        G.push({ key:'vol', status:'pass', label:`Volute adds ${spec.voluteHeightMm.toFixed(1)}mm at weak point — grain reinforcement adequate.` })
    }

    // Blend continuity — slope at entry should be smooth
    const ε = 0.5  // mm step
    const blendStart = spec.blendCentreMm - spec.blendLengthMm / 2
    const slopeNeck  = (surfaceZ(blendStart + ε, spec) - surfaceZ(blendStart - ε, spec)) / (2 * ε)
    const slopeHS    = (headstockPlaneZ(blendStart + ε, spec) - headstockPlaneZ(blendStart - ε, spec)) / (2 * ε)
    if (Math.abs(slopeNeck - slopeHS) > 1.5)
      G.push({ key:'slope', status:'warn', label:`Blend entry slope mismatch — increase blend length or adjust centre offset for smoother transition.` })
    else
      G.push({ key:'slope', status:'pass', label:`Blend entry slope continuous.` })

    // HS thickness
    if (spec.hsThicknessMm < 12)
      G.push({ key:'hst', status:'warn', label:`Headstock thickness ${spec.hsThicknessMm}mm is thin — minimum 12mm for structural tuner hole integrity.` })
    else
      G.push({ key:'hst', status:'pass', label:`Headstock thickness ${spec.hsThicknessMm}mm OK.` })

    return G
  })

  // ── G-code pass generator for transition zone ──────────────────────────────

  function transitionGCode(): string {
    const yStart = spec.blendCentreMm - spec.blendLengthMm / 2 - 5  // 5mm margin
    const yEnd   = spec.blendCentreMm + spec.blendLengthMm / 2 + 5
    const hw     = spec.nutWidthMm / 2 + 3   // 3mm overrun each side
    const bnR    = spec.ballNoseMm / 2
    const step   = spec.ballNoseMm * spec.stepoverPct / 100
    const n      = Math.ceil((hw * 2 + spec.ballNoseMm) / step) + 1
    const yStations = 16   // Y stations across transition zone

    const lines = [
      `; Headstock Transition Zone — Production Shop`,
      `; Y=${yStart.toFixed(1)}mm to ${yEnd.toFixed(1)}mm  (VINE-05: Y=0 at nut)`,
      `; Type: ${spec.headstockType}  angle: ${spec.pitchAngleDeg}°`,
      `; Volute: ${spec.voluteType}${spec.voluteType !== 'none' ? ` h=${spec.voluteHeightMm}mm @ Y=${spec.volutePositionMm}mm σ=${spec.volSigmaMm}mm` : ''}`,
      `; Ball-nose Ø${spec.ballNoseMm}mm  step ${step.toFixed(2)}mm  ${n} passes`,
      ``,
      `G21 ; mm`, `G90 ; absolute`, `G00 Z5.000`, ``,
    ]

    for (let yi = 0; yi <= yStations; yi++) {
      const y = yStart + (yEnd - yStart) * yi / yStations
      lines.push(`; Y=${y.toFixed(2)}mm  region:${regionAt(y, spec)}  base_z=${surfaceZ(y, spec).toFixed(4)}mm`)
      lines.push(`G00 Y${y.toFixed(3)}`)

      for (let i = 0; i < n; i++) {
        const x   = -(hw + bnR) + i * step
        const xn  = Math.max(-1, Math.min(1, x / (spec.nutWidthMm / 2)))
        // Back surface Z at this X/Y, tool centre sits above by ball radius
        const zSurf = surfaceZ(y, spec)
        // For the cross-section, apply profile shaping to the back depth
        const backDepth = -zSurf
        const zProfile  = backDepth * (1 - Math.pow(Math.abs(xn), 1.6))  // C-shape default
        const zTool     = -(backDepth - zProfile) - bnR

        if (i === 0) {
          lines.push(`G00 X${x.toFixed(3)} Z${(zTool + 5).toFixed(4)}`)
          lines.push(`G01 Z${zTool.toFixed(4)} F${(spec.feedMmMin * 0.4).toFixed(0)}  ; plunge`)
        } else {
          lines.push(`G01 X${x.toFixed(3)} Y${y.toFixed(3)} Z${zTool.toFixed(4)} F${spec.feedMmMin.toFixed(0)}`)
        }
      }
      lines.push(`G00 Z5.000`, ``)
    }

    lines.push(`M30  ; end transition zone`)
    return lines.join('\n')
  }

  // ── DXF export payload ─────────────────────────────────────────────────────

  const exportPayload = computed(() => ({
    headstock_type:     spec.headstockType,
    pitch_angle_deg:    spec.pitchAngleDeg,
    hs_thickness_mm:    spec.hsThicknessMm,
    neck_depth_mm:      spec.neckDepthMm,
    nut_width_mm:       spec.nutWidthMm,
    blend_length_mm:    spec.blendLengthMm,
    blend_centre_mm:    spec.blendCentreMm,
    blend_tension:      spec.blendTension,
    volute_type:        spec.voluteType,
    volute_height_mm:   spec.voluteHeightMm,
    volute_position_mm: spec.volutePositionMm,
    vol_sigma_mm:       spec.volSigmaMm,
    ball_nose_mm:       spec.ballNoseMm,
    stepover_pct:       spec.stepoverPct,
    feed_mm_min:        spec.feedMmMin,
    derived: {
      thin_point_mm:    derived.value.thinPointMm,
      hs_drop_30mm:     derived.value.hsDropAt30mm,
      blend_delta_mm:   derived.value.blendDeltaMm,
    },
  }))

  function setSpec<K extends keyof TransitionSpec>(key: K, value: TransitionSpec[K]) {
    (spec as any)[key] = value
  }

  function loadPreset(name: string) {
    const p = TRANSITION_PRESETS[name]
    if (p) Object.assign(spec, p)
  }

  return {
    spec:          readonly(spec),
    derived,
    gates,
    exportPayload,
    surfaceSamples,
    setSpec,
    loadPreset,
    transitionGCode,
    // Pure functions for external use
    surfaceZ,
    voluteZ,
    headstockPlaneZ,
    blendZ,
    regionAt,
    thinPointMm,
    PRESETS: Object.keys(TRANSITION_PRESETS),
  }
}
