/**
 * useFretboard
 *
 * Reactive composable for fretboard geometry:
 *   - Single and compound (conical) radius
 *   - Fret position table (equal temperament)
 *   - Crown height at every fret station via sagitta formula
 *   - Board width taper (nut → last fret)
 *   - Nut slot depth per string (crown + action height)
 *   - CNC ball-nose toolpath parameters
 *   - G-code pass generator per fret station
 *
 * Pure TypeScript — no Vue/Konva imports.
 * Wires into WorkspaceView via FretboardPanel.vue.
 */

import { reactive, computed, readonly } from 'vue'

const INCH_TO_MM = 25.4

// ─── Types ────────────────────────────────────────────────────────────────────

export type RadiusType = 'single' | 'compound'

export interface FretboardSpec {
  radiusType:   RadiusType
  r1Inch:       number   // nut-end radius (inches)
  r2Inch:       number   // body-end radius (inches, compound only)
  scaleLengthMm:number   // vibrating string length
  fretCount:    number   // 19-24
  nutWidthMm:   number   // board width at nut
  width12Mm:    number   // board width at 12th fret
  thicknessMm:  number   // fretboard blank thickness

  // CNC
  ballNoseMm:   number   // bit diameter
  stepoverPct:  number   // 0-40%
  feedMmMin:    number
  depthOfCutMm: number

  // Nut slot action heights
  nutActionE1:  number   // high E (mm above fret 1 crown)
  nutActionE6:  number   // low  E (mm above fret 1 crown)
}

export interface FretStation {
  fret:        number
  positionMm:  number   // distance from nut
  radiusInch:  number
  widthMm:     number
  crownMm:     number   // sagitta height
}

export interface NutSlot {
  string:      number
  depthMm:     number   // slot depth = crown at nut + action
  widthMm:     number   // slot width ≈ string gauge
}

export interface ToolpassLine {
  passNum:   number
  x:         number    // mm from board centreline
  zEntry:    number    // Z at board edge (air)
  zApex:     number    // Z at board centre (deepest)
  gcode:     string
}

export interface FretboardGate {
  key:    string
  status: 'pass' | 'warn' | 'fail'
  label:  string
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_SPEC: FretboardSpec = {
  radiusType:    'single',
  r1Inch:        12,
  r2Inch:        16,
  scaleLengthMm: 628,
  fretCount:     22,
  nutWidthMm:    43,
  width12Mm:     56,
  thicknessMm:   6,
  ballNoseMm:    6,
  stepoverPct:   15,
  feedMmMin:     1200,
  depthOfCutMm:  0.3,
  nutActionE1:   0.5,
  nutActionE6:   0.7,
}

// ─── Pure geometry functions ───────────────────────────────────────────────────

/** Equal temperament fret position from nut (mm) */
export function fretPosition(fret: number, scaleLength: number): number {
  return scaleLength - scaleLength / Math.pow(2, fret / 12)
}

/** Board width at fret n via linear taper (nut→last fret extrapolated from 12th) */
export function boardWidthAtFret(
  fret: number,
  fretCount: number,
  nutWidth: number,
  width12: number,
): number {
  const t = fret / fretCount
  return nutWidth + (width12 - nutWidth) * t * 2
}

/** Radius at fret n — linear interpolation for compound, constant for single */
export function radiusAtFret(
  fret: number,
  fretCount: number,
  r1: number,
  r2: number,
  type: RadiusType,
): number {
  if (type === 'single') return r1
  const t = fret / fretCount
  return r1 + (r2 - r1) * t
}

/**
 * Sagitta (crown height) of a circular arc.
 * r = radius in mm, w = chord width in mm.
 * h = r - sqrt(r² - (w/2)²)
 */
export function sagittaHeight(radiusInch: number, widthMm: number): number {
  const r = radiusInch * INCH_TO_MM
  const half = widthMm / 2
  if (r < half) return 0
  return r - Math.sqrt(r * r - half * half)
}

/** Ball-nose step-over in mm */
export function stepoverMm(ballNoseMm: number, stepoverPct: number): number {
  return ballNoseMm * (stepoverPct / 100)
}

/** Number of passes across full board width */
export function passCount(widthMm: number, ballNoseMm: number, stepoverPct: number): number {
  const step = stepoverMm(ballNoseMm, stepoverPct)
  return Math.ceil((widthMm + ballNoseMm) / step) + 1
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useFretboard() {
  const spec = reactive<FretboardSpec>({ ...DEFAULT_SPEC })

  // ── Fret station table ─────────────────────────────────────────────────────

  const fretStations = computed<FretStation[]>(() => {
    const stations: FretStation[] = []
    for (let i = 0; i <= spec.fretCount; i++) {
      const pos   = i === 0 ? 0 : fretPosition(i, spec.scaleLengthMm)
      const r     = radiusAtFret(i, spec.fretCount, spec.r1Inch, spec.r2Inch, spec.radiusType)
      const w     = boardWidthAtFret(i, spec.fretCount, spec.nutWidthMm, spec.width12Mm)
      const crown = sagittaHeight(r, w)
      stations.push({ fret: i, positionMm: pos, radiusInch: r, widthMm: w, crownMm: crown })
    }
    return stations
  })

  // ── Nut slots ──────────────────────────────────────────────────────────────

  const nutSlots = computed<NutSlot[]>(() => {
    const crown0 = fretStations.value[0]?.crownMm ?? 0
    return [
      { string: 1, depthMm: crown0 + spec.nutActionE1, widthMm: 0.43 },  // high E
      { string: 2, depthMm: crown0 + spec.nutActionE1 + 0.05, widthMm: 0.56 },
      { string: 3, depthMm: crown0 + spec.nutActionE1 + 0.08, widthMm: 0.71 },
      { string: 4, depthMm: crown0 + spec.nutActionE6 - 0.08, widthMm: 0.86 },
      { string: 5, depthMm: crown0 + spec.nutActionE6 - 0.04, widthMm: 1.09 },
      { string: 6, depthMm: crown0 + spec.nutActionE6, widthMm: 1.32 },  // low E
    ]
  })

  // ── Toolpath passes (for a given fret station index) ──────────────────────

  function generatePasses(fretIndex: number): ToolpassLine[] {
    const station = fretStations.value[fretIndex]
    if (!station) return []

    const r     = station.radiusInch * INCH_TO_MM
    const w     = station.widthMm
    const bnR   = spec.ballNoseMm / 2
    const step  = stepoverMm(spec.ballNoseMm, spec.stepoverPct)
    const n     = passCount(w, spec.ballNoseMm, spec.stepoverPct)
    const lines: ToolpassLine[] = []

    for (let i = 0; i < n; i++) {
      const x = -(w / 2 + bnR) + i * step
      // Z of tool centre following the arc (ball-nose contact point)
      const dx = x   // relative to board centre
      const zArc = Math.abs(dx) <= r
        ? -(r - Math.sqrt(r * r - dx * dx))   // negative = cutting depth
        : 0
      const zTool = zArc + bnR                 // tool centre above material

      const gcode = `G01 X${x.toFixed(3)} Z${zTool.toFixed(4)} F${spec.feedMmMin}`

      lines.push({
        passNum: i + 1,
        x,
        zEntry: bnR,
        zApex: zTool,
        gcode,
      })
    }
    return lines
  }

  // ── Full G-code program for one fret station ───────────────────────────────

  function fretStationGCode(fretIndex: number): string {
    const station = fretStations.value[fretIndex]
    if (!station) return ''
    const passes  = generatePasses(fretIndex)
    const w       = station.widthMm
    const bnR     = spec.ballNoseMm / 2
    const yPos    = station.positionMm.toFixed(3)

    const lines = [
      `; === Fret ${station.fret === 0 ? 'NUT' : station.fret} station  Y=${yPos}mm ===`,
      `; Radius: ${station.radiusInch.toFixed(2)}"  Width: ${w.toFixed(2)}mm  Crown: ${station.crownMm.toFixed(4)}mm`,
      `; Ball-nose Ø${spec.ballNoseMm}mm  Step ${stepoverMm(spec.ballNoseMm, spec.stepoverPct).toFixed(2)}mm  ${passes.length} passes`,
      `G00 Z5.000`,
      `G00 X${(-(w / 2 + bnR)).toFixed(3)} Y${yPos}`,
      `G01 Z${bnR.toFixed(4)} F${(spec.feedMmMin * 0.4).toFixed(0)}  ; plunge`,
      ...passes.map(p => p.gcode),
      `G00 Z5.000`,
    ]
    return lines.join('\n')
  }

  // ── Derived summary ────────────────────────────────────────────────────────

  const derived = computed(() => {
    const nut  = fretStations.value[0]
    const f12  = fretStations.value.find(s => s.fret === 12) ?? nut
    const last = fretStations.value[fretStations.value.length - 1]
    const wMax = last?.widthMm ?? spec.width12Mm
    const passes = passCount(wMax, spec.ballNoseMm, spec.stepoverPct)

    return {
      crownNut:     nut?.crownMm.toFixed(4) ?? '—',
      crown12:      f12?.crownMm.toFixed(4) ?? '—',
      crownLast:    last?.crownMm.toFixed(4) ?? '—',
      totalPasses:  passes,
      stepoverMm:   stepoverMm(spec.ballNoseMm, spec.stepoverPct).toFixed(2),
      maxWidthMm:   wMax.toFixed(1),
      nutSlotDepthE1: nutSlots.value[0]?.depthMm.toFixed(3) ?? '—',
      nutSlotDepthE6: nutSlots.value[5]?.depthMm.toFixed(3) ?? '—',
    }
  })

  // ── Gates ──────────────────────────────────────────────────────────────────

  const gates = computed<FretboardGate[]>(() => {
    const G: FretboardGate[] = []

    if (spec.radiusType === 'compound' && spec.r2Inch <= spec.r1Inch)
      G.push({ key:'compound', status:'fail', label:`Body radius ${spec.r2Inch}" must be greater than nut radius ${spec.r1Inch}"` })
    else if (spec.radiusType === 'compound')
      G.push({ key:'compound', status:'pass', label:`Compound ${spec.r1Inch}"→${spec.r2Inch}" — valid conical geometry` })

    if (spec.ballNoseMm > spec.nutWidthMm / 2)
      G.push({ key:'ball', status:'warn', label:`Ball-nose Ø${spec.ballNoseMm}mm is large relative to nut width ${spec.nutWidthMm}mm` })
    else
      G.push({ key:'ball', status:'pass', label:`Ball-nose Ø${spec.ballNoseMm}mm fits nut width` })

    if (spec.depthOfCutMm > spec.ballNoseMm / 4)
      G.push({ key:'doc', status:'warn', label:`DOC ${spec.depthOfCutMm}mm exceeds Ø/4 — risk of chatter on finish pass` })
    else
      G.push({ key:'doc', status:'pass', label:`DOC ${spec.depthOfCutMm}mm within safe range for Ø${spec.ballNoseMm}mm` })

    const crown0 = parseFloat(derived.value.crownNut)
    if (crown0 > spec.thicknessMm * 0.4)
      G.push({ key:'crown', status:'warn', label:`Crown ${derived.value.crownNut}mm = ${(crown0/spec.thicknessMm*100).toFixed(0)}% of board thickness — check blank` })
    else
      G.push({ key:'crown', status:'pass', label:`Crown ${derived.value.crownNut}mm within board thickness ${spec.thicknessMm}mm` })

    return G
  })

  // ── DXF export payload ─────────────────────────────────────────────────────

  const exportPayload = computed(() => ({
    radius_type:      spec.radiusType,
    r1_inch:          spec.r1Inch,
    r2_inch:          spec.r2Inch,
    scale_length_mm:  spec.scaleLengthMm,
    fret_count:       spec.fretCount,
    nut_width_mm:     spec.nutWidthMm,
    width_12th_mm:    spec.width12Mm,
    thickness_mm:     spec.thicknessMm,
    ball_nose_mm:     spec.ballNoseMm,
    stepover_pct:     spec.stepoverPct,
    feed_mm_min:      spec.feedMmMin,
    depth_of_cut_mm:  spec.depthOfCutMm,
    fret_stations:    fretStations.value.map(s => ({
      fret:         s.fret,
      position_mm:  +s.positionMm.toFixed(3),
      radius_inch:  +s.radiusInch.toFixed(3),
      width_mm:     +s.widthMm.toFixed(3),
      crown_mm:     +s.crownMm.toFixed(4),
    })),
    nut_slots: nutSlots.value,
  }))

  // ── Actions ────────────────────────────────────────────────────────────────

  function setSpec<K extends keyof FretboardSpec>(key: K, value: FretboardSpec[K]) {
    (spec as any)[key] = value
  }

  function resetToDefaults() { Object.assign(spec, DEFAULT_SPEC) }

  return {
    spec:           readonly(spec),
    fretStations,
    nutSlots,
    derived,
    gates,
    exportPayload,
    setSpec,
    resetToDefaults,
    generatePasses,
    fretStationGCode,
    // expose pure functions for direct use in canvas drawing
    fretPosition,
    boardWidthAtFret,
    radiusAtFret,
    sagittaHeight,
    passCount,
    stepoverMm,
  }
}
