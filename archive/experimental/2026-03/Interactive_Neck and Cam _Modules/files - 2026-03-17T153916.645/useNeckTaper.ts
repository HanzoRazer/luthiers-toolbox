/**
 * useNeckTaper
 *
 * Neck width taper and string spacing geometry.
 * Feeds into useNeckProfile (shoulder width per station)
 * and useCamSpec (tuner post column alignment verification).
 *
 * Taper types:
 *   linear   — constant rate nut→body (most common)
 *   convex   — slightly wider in mid-neck, pinches at ends
 *   concave  — slow taper then faster past 12th (smoothstep)
 *   stepped  — two-rate: slow nut→12th, faster 12th→body
 *
 * String spacing methods:
 *   equal-edge   — equal string-to-edge distance (standard)
 *   equal-centre — equal centre-to-centre (classical)
 *   fan          — proportional to bridge spacing
 *   compound     — TOM-style, tighter centre strings
 *
 * All outputs in mm. Zero = neck centreline.
 */

import { reactive, computed, readonly } from 'vue'
import { fretPosition } from './useFretboard'

// ─── Types ────────────────────────────────────────────────────────────────────

export type TaperType   = 'linear' | 'convex' | 'concave' | 'stepped'
export type SpacingType = 'equal-edge' | 'equal-centre' | 'fan' | 'compound'

export interface NeckTaperSpec {
  scaleLengthMm:   number   // used in distance-based taper formula (repo taper_math.py)
  fretCount:       number
  nutWidthMm:      number
  width12Mm:       number
  lastFretWidthMm: number
  taperType:       TaperType

  // String spacing
  spacingType:     SpacingType
  stringCount:     number
  edgeMarginNutMm: number   // string-to-edge at nut
  edgeMargin12Mm:  number   // string-to-edge at 12th
  bridgeSpacingMm: number   // total string span at bridge

  // Fretboard bevel
  bevelAngleDeg:   number   // edge bevel for BCAM chamfer pass
}

export interface StringStation {
  fret:         number
  positionMm:   number     // distance from nut
  neckWidthMm:  number
  edgeMarginMm: number     // interpolated
  stringPositions: number[] // mm from centreline, neg=bass
  ccSpacingMm:  number     // centre-to-centre at this station (uniform only)
}

export interface TaperGate {
  key:    string
  status: 'pass' | 'warn' | 'fail'
  label:  string
}

// ─── Standard string gauges (light .009 set) ─────────────────────────────────

export const STRING_GAUGES_LIGHT  = [0.43, 0.56, 0.71, 0.86, 1.09, 1.32]
export const STRING_GAUGES_MEDIUM = [0.46, 0.61, 0.79, 1.02, 1.32, 1.63]
export const STRING_GAUGES_7STR   = [0.43, 0.56, 0.71, 0.86, 1.09, 1.32, 1.63]
export const STRING_GAUGES_8STR   = [0.43, 0.56, 0.71, 0.86, 1.09, 1.32, 1.63, 2.03]

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_SPEC: NeckTaperSpec = {
  scaleLengthMm:   628,
  fretCount:       22,
  nutWidthMm:      43,
  width12Mm:       54,
  lastFretWidthMm: 64,
  taperType:       'linear',
  spacingType:     'equal-edge',
  stringCount:     6,
  edgeMarginNutMm: 3.0,
  edgeMargin12Mm:  4.0,
  bridgeSpacingMm: 52.0,
  bevelAngleDeg:   15,
}

// ─── Geometry ─────────────────────────────────────────────────────────────────

/**
 * Distance-based neck width at fret n.
 *
 * Formula from repo taper_math.py (Wave 17):
 *   W_f = W_nut + (x_f / L_N) × (W_end - W_nut)
 *
 * Uses actual physical distance from nut to fret (ET formula),
 * not fret index. More geometrically accurate for CNC layout
 * because fret spacing is logarithmic, not linear.
 *
 * x_f = scale - scale / 2^(f/12)   (distance from nut to fret f)
 * L_N = distance from nut to the reference end fret
 */
export function neckWidthAtFret(
  fret: number,
  fretCount: number,
  nutW: number,
  w12: number,
  wLast: number,
  type: TaperType,
  scaleLengthMm = 628,
): number {
  // Physical distances (mm) — this is what the repo uses
  const x_f = fret === 0 ? 0 : scaleLengthMm - scaleLengthMm / Math.pow(2, fret / 12)
  const L_N = scaleLengthMm - scaleLengthMm / Math.pow(2, fretCount / 12)  // distance to last fret
  const L_12 = scaleLengthMm - scaleLengthMm / Math.pow(2, 12 / 12)        // distance to 12th fret
  const t = L_N > 0 ? x_f / L_N : 0

  switch (type) {
    case 'linear':
      // W_f = W_nut + (x_f / L_N) × (W_end - W_nut) — direct from repo
      return nutW + t * (wLast - nutW)

    case 'convex': {
      // Bell curve — wider than linear in mid-neck, uses actual distances
      const t12 = L_12 / L_N   // fraction of total length at 12th fret
      const tc = 4 * (t / t12) * (1 - t / t12)
      const midBulge = (w12 - (nutW + (wLast - nutW) * t12)) * tc * 0.4
      return nutW + t * (wLast - nutW) + midBulge
    }

    case 'concave': {
      // Smoothstep on distance — slow start, faster past 12th
      const ts = t * t * (3 - 2 * t)
      return nutW + ts * (wLast - nutW)
    }

    case 'stepped': {
      // Two distinct rates split at 12th fret distance
      const t12 = L_N > 0 ? L_12 / L_N : 0.5
      if (t <= t12) return nutW + (w12 - nutW) * (t / t12)
      return w12 + (wLast - w12) * ((t - t12) / (1 - t12))
    }
  }
}

export function edgeMarginAtFret(
  fret: number,
  fretCount: number,
  marginNut: number,
  margin12: number,
): number {
  const t = Math.min(1, fret / fretCount)
  return marginNut + (margin12 - marginNut) * t
}

export function stringPositionsAtFret(
  neckW: number,
  edgeMargin: number,
  stringCount: number,
  spacingType: SpacingType,
  bridgeSpacing: number,
  fretFraction = 0,   // 0=nut, 1=last fret (for fan calculation)
): number[] {
  const usable = neckW - edgeMargin * 2
  const n = stringCount

  switch (spacingType) {
    case 'equal-edge': {
      return Array.from({ length: n }, (_, i) =>
        -usable / 2 + (usable / (n - 1)) * i
      )
    }

    case 'equal-centre': {
      const cc = usable / (n - 1)
      return Array.from({ length: n }, (_, i) =>
        -usable / 2 + cc * i
      )
    }

    case 'fan': {
      // Fan: C-C spreads proportionally from nut C-C toward bridge C-C
      const nutCC = usable / (n - 1)
      const bridgeCC = bridgeSpacing / (n - 1)
      const cc = nutCC + (bridgeCC - nutCC) * fretFraction
      return Array.from({ length: n }, (_, i) =>
        -(cc * (n - 1)) / 2 + cc * i
      )
    }

    case 'compound': {
      // TOM-style: equal CC but outer strings pushed slightly wider
      const cc = usable / (n - 1)
      return Array.from({ length: n }, (_, i) => {
        const t = i / (n - 1)   // 0=bass, 1=treble
        const spread = Math.abs(t - 0.5) * 0.12   // outer strings 6% wider
        return (-usable / 2 + cc * i) * (1 + spread)
      })
    }
  }
}

export function bevelOffsetMm(neckHalfWidthMm: number, angleDeg: number): number {
  return neckHalfWidthMm * Math.tan(angleDeg * Math.PI / 180)
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useNeckTaper() {
  const spec = reactive<NeckTaperSpec>({ ...DEFAULT_SPEC })

  // ── All fret stations ─────────────────────────────────────────────────────

  const stations = computed<StringStation[]>(() => {
    const keyFrets = [0, 1, 2, 3, 5, 7, 9, 12, 15, 17, 19, spec.fretCount]
      .filter(n => n <= spec.fretCount)

    return keyFrets.map(n => {
      const pos      = n === 0 ? 0 : fretPosition(n, spec.scaleLengthMm)
      const w        = neckWidthAtFret(n, spec.fretCount, spec.nutWidthMm, spec.width12Mm, spec.lastFretWidthMm, spec.taperType)
      const margin   = edgeMarginAtFret(n, spec.fretCount, spec.edgeMarginNutMm, spec.edgeMargin12Mm)
      const fraction = n / spec.fretCount
      const strPos   = stringPositionsAtFret(w, margin, spec.stringCount, spec.spacingType, spec.bridgeSpacingMm, fraction)
      const cc       = strPos.length > 1 ? strPos[1] - strPos[0] : 0

      return {
        fret:             n,
        positionMm:       pos,
        neckWidthMm:      w,
        edgeMarginMm:     margin,
        stringPositions:  strPos,
        ccSpacingMm:      cc,
      }
    })
  })

  // ── Derived summary ────────────────────────────────────────────────────────

  const derived = computed(() => {
    const nutStation  = stations.value[0]
    const f12Station  = stations.value.find(s => s.fret === 12) ?? stations.value[0]
    const lastStation = stations.value[stations.value.length - 1]
    const totalLen    = fretPosition(spec.fretCount, spec.scaleLengthMm)

    return {
      taperRateMmPerM:  ((spec.lastFretWidthMm - spec.nutWidthMm) / totalLen * 1000).toFixed(2),
      ccAtNut:          nutStation.ccSpacingMm.toFixed(2),
      ccAt12:           f12Station.ccSpacingMm.toFixed(2),
      nutEdgeLeft:      (nutStation.stringPositions[0] + spec.nutWidthMm / 2).toFixed(2),
      nutEdgeRight:     (spec.nutWidthMm / 2 - nutStation.stringPositions[nutStation.stringPositions.length - 1]).toFixed(2),
      bevelOffsetNut:   bevelOffsetMm(spec.nutWidthMm / 2, spec.bevelAngleDeg).toFixed(2),
      bevelOffsetLast:  bevelOffsetMm(spec.lastFretWidthMm / 2, spec.bevelAngleDeg).toFixed(2),
      totalStringSpread: (
        (lastStation.stringPositions[lastStation.stringPositions.length - 1] -
         lastStation.stringPositions[0]) -
        (nutStation.stringPositions[nutStation.stringPositions.length - 1] -
         nutStation.stringPositions[0])
      ).toFixed(2),
    }
  })

  // ── Gates ──────────────────────────────────────────────────────────────────

  const gates = computed<TaperGate[]>(() => {
    const G: TaperGate[] = []
    const d = derived.value
    const nutStation = stations.value[0]

    // Edge margins
    const leftMargin  = parseFloat(d.nutEdgeLeft)
    const rightMargin = parseFloat(d.nutEdgeRight)
    if (leftMargin < 2.5 || rightMargin < 2.5)
      G.push({ key:'edge', status:'warn', label:`Edge margin ${leftMargin.toFixed(2)}mm / ${rightMargin.toFixed(2)}mm — min 2.5mm recommended` })
    else
      G.push({ key:'edge', status:'pass', label:`Edge margins ${leftMargin.toFixed(2)}mm / ${rightMargin.toFixed(2)}mm OK` })

    // Width progression
    if (spec.width12Mm <= spec.nutWidthMm)
      G.push({ key:'w12', status:'fail', label:`12th width must be greater than nut width` })
    else
      G.push({ key:'w12', status:'pass', label:`Width taper ${spec.nutWidthMm}→${spec.width12Mm}→${spec.lastFretWidthMm}mm valid` })

    // Nut width range
    if (spec.nutWidthMm < 38 || spec.nutWidthMm > 48)
      G.push({ key:'nut', status:'warn', label:`Nut width ${spec.nutWidthMm}mm outside standard 38–48mm range` })
    else
      G.push({ key:'nut', status:'pass', label:`Nut width ${spec.nutWidthMm}mm within standard range` })

    // Fan spacing vs bridge
    if (spec.spacingType === 'fan') {
      const nutSpan = nutStation.stringPositions[nutStation.stringPositions.length - 1] -
                      nutStation.stringPositions[0]
      if (nutSpan > spec.bridgeSpacingMm)
        G.push({ key:'fan', status:'warn', label:`Nut string span ${nutSpan.toFixed(1)}mm exceeds bridge spacing ${spec.bridgeSpacingMm}mm` })
      else
        G.push({ key:'fan', status:'pass', label:`Fan spacing nut→bridge consistent` })
    }

    return G
  })

  // ── Nut slot specs (for CNC nut slot routing) ─────────────────────────────

  const nutSlotSpec = computed(() => {
    const nutStation = stations.value[0]
    const gauges = spec.stringCount === 6 ? STRING_GAUGES_LIGHT :
                   spec.stringCount === 7 ? STRING_GAUGES_7STR :
                   spec.stringCount === 8 ? STRING_GAUGES_8STR : STRING_GAUGES_LIGHT

    return nutStation.stringPositions.map((x, i) => ({
      string:       i + 1,
      positionMm:   +(x + spec.nutWidthMm / 2).toFixed(3),
      centrelineMm: +x.toFixed(3),
      gaugeInch:    gauges[i] ?? 1.0,
      slotWidthMm:  +((gauges[i] ?? 1.0) * 1.1).toFixed(3),   // 10% clearance
    }))
  })

  // ── DXF export payload ─────────────────────────────────────────────────────

  const exportPayload = computed(() => ({
    taper_type:          spec.taperType,
    spacing_type:        spec.spacingType,
    nut_width_mm:        spec.nutWidthMm,
    width_12th_mm:       spec.width12Mm,
    last_fret_width_mm:  spec.lastFretWidthMm,
    string_count:        spec.stringCount,
    edge_margin_nut_mm:  spec.edgeMarginNutMm,
    edge_margin_12_mm:   spec.edgeMargin12Mm,
    bridge_spacing_mm:   spec.bridgeSpacingMm,
    bevel_angle_deg:     spec.bevelAngleDeg,
    stations: stations.value.map(st => ({
      fret:              st.fret,
      position_mm:       +st.positionMm.toFixed(3),
      neck_width_mm:     +st.neckWidthMm.toFixed(3),
      edge_margin_mm:    +st.edgeMarginMm.toFixed(3),
      string_positions:  st.stringPositions.map(x => +x.toFixed(3)),
      cc_spacing_mm:     +st.ccSpacingMm.toFixed(3),
    })),
    nut_slots: nutSlotSpec.value,
  }))

  // ── Actions ────────────────────────────────────────────────────────────────

  function setSpec<K extends keyof NeckTaperSpec>(key: K, value: NeckTaperSpec[K]) {
    (spec as any)[key] = value
  }

  function widthAtFret(n: number): number {
    return neckWidthAtFret(n, spec.fretCount, spec.nutWidthMm, spec.width12Mm, spec.lastFretWidthMm, spec.taperType, spec.scaleLengthMm)
  }

  function stringPosAtFret(n: number): number[] {
    const w      = widthAtFret(n)
    const margin = edgeMarginAtFret(n, spec.fretCount, spec.edgeMarginNutMm, spec.edgeMargin12Mm)
    return stringPositionsAtFret(w, margin, spec.stringCount, spec.spacingType, spec.bridgeSpacingMm, n / spec.fretCount)
  }

  return {
    spec:          readonly(spec),
    stations,
    derived,
    gates,
    nutSlotSpec,
    exportPayload,
    setSpec,
    widthAtFret,
    stringPosAtFret,
    // expose pure functions
    neckWidthAtFret,
    edgeMarginAtFret,
    stringPositionsAtFret,
    bevelOffsetMm,
  }
}
