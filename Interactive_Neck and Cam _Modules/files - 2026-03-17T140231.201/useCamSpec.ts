/**
 * useCamSpec
 *
 * Reactive composable for the three critical CAM parameters that must
 * be resolved before a headstock DXF goes to the BCAM 2030A:
 *
 *   1. Headstock pitch angle (and fixture requirements)
 *   2. Truss rod channel geometry
 *   3. Tuner mechanical layout (post holes + mounting screws)
 *
 * Produces:
 *   - derived dimensions (break angle, wall thickness, column height…)
 *   - CAM gate results (Carruth floor, rod fits nut, end mill ≤ rod width…)
 *   - DXF layer payload ready to merge into ExportRequest (dxf_export.py)
 *   - Konva drawing instructions for overlay on WorkspaceView canvas
 *
 * Zero UI dependencies — consumed by CamSpecPanel.vue and WorkspaceView.vue.
 */

import { reactive, computed, readonly } from 'vue'
import type { ParametricParams } from '@/types/headstock'

const MM = 0.215   // canvas units → mm

// ─── Types ────────────────────────────────────────────────────────────────────

export type PitchStyle  = 'angled' | 'flat'
export type RodAccess   = 'heel'   | 'head'
export type RodType     = 'single' | 'double'
export type TunerPattern = '3+3' | '6L' | '6R' | '4+2'

export interface CamSpec {
  // Pitch
  pitchStyle: PitchStyle
  angle:      number       // degrees, 0-17

  // Nut
  nutHeightMm: number      // nut height above headstock face mm

  // Truss rod
  rodAccess:   RodAccess
  rodType:     RodType
  rodWidthMm:  number
  rodDepthMm:  number
  rodLengthMm: number
  endMillMm:   number      // router bit diameter for channel

  // Tuners
  tunerPattern:    TunerPattern
  postDiamMm:      number  // peg hole bore diameter
  postCCmm:        number  // post centre-to-centre
  screwDiamMm:     number  // mounting screw pilot diameter
  edgeClearMm:     number  // min clearance from post centre to headstock edge
}

export interface TunerHoleSpec {
  x:        number   // canvas units (matches headstock 0-200 space)
  y:        number
  postR:    number   // canvas units
  screwR:   number
  side:     'bass' | 'treble'
  index:    number
}

export interface RodChannelSpec {
  cx:        number  // centre X canvas units
  startY:    number  // Y canvas units (nut end)
  endY:      number  // Y canvas units (other end)
  widthU:    number  // width in canvas units
  depthU:    number  // depth in canvas units
  emRadiusU: number  // end-mill radius canvas units
}

export interface GateResult {
  key:    string
  status: 'pass' | 'warn' | 'fail'
  label:  string
}

export interface DerivedDimensions {
  breakAngleDeg:    number
  wallThicknessMm:  number   // material each side of rod channel
  postHeightMm:     number   // tuner post height needed given pitch
  columnHeightMm:   number   // total post column height on inline patterns
  rodClearanceMm:   number   // minimum neck thickness at channel
  fixtureNote:      string
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_SPEC: CamSpec = {
  pitchStyle:   'angled',
  angle:        13,
  nutHeightMm:  6,
  rodAccess:    'heel',
  rodType:      'single',
  rodWidthMm:   6,
  rodDepthMm:   11,
  rodLengthMm:  445,
  endMillMm:    6,
  tunerPattern: '3+3',
  postDiamMm:   10,
  postCCmm:     35,
  screwDiamMm:  3,
  edgeClearMm:  5,
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useCamSpec(nutWidthMm = 43, headstockLengthMm = 175) {

  const spec = reactive<CamSpec>({ ...DEFAULT_SPEC })

  // ── Derived dimensions ─────────────────────────────────────────────────────

  const derived = computed<DerivedDimensions>(() => {
    const angR = spec.angle * Math.PI / 180

    // String break angle over nut is roughly pitch angle minus 2° lost to nut height
    const breakAngleDeg = spec.pitchStyle === 'flat'
      ? 0
      : Math.max(0, spec.angle - 2)

    // Wall thickness each side of rod channel
    const wallThicknessMm = (nutWidthMm - spec.rodWidthMm) / 2

    // Post height needed: on angled headstocks the treble side rises
    // more than the bass side — use worst-case (half nut width × tan angle)
    const postHeightMm = spec.pitchStyle === 'angled'
      ? +(Math.tan(angR) * (nutWidthMm / 2) + spec.nutHeightMm).toFixed(1)
      : +spec.nutHeightMm.toFixed(1)

    // Total column height for inline patterns
    const postsInColumn = spec.tunerPattern === '6L' || spec.tunerPattern === '6R'
      ? 6
      : spec.tunerPattern === '4+2'
      ? 4   // longer column
      : 3
    const columnHeightMm = (postsInColumn - 1) * spec.postCCmm

    // Minimum neck thickness at rod channel
    const rodClearanceMm = spec.rodDepthMm + 2   // 2mm below channel

    // Fixture note for BCAM operator
    const fixtureNote = spec.pitchStyle === 'angled'
      ? `${spec.angle}° wedge spoilboard required — blank must seat flush`
      : 'Flat fixture — no angled spoilboard needed'

    return {
      breakAngleDeg,
      wallThicknessMm,
      postHeightMm,
      columnHeightMm,
      rodClearanceMm,
      fixtureNote,
    }
  })

  // ── Gate checks ────────────────────────────────────────────────────────────

  const gates = computed<GateResult[]>(() => {
    const G: GateResult[] = []

    // Carruth 6° minimum string break angle
    if (spec.pitchStyle === 'angled') {
      if (spec.angle < 6)
        G.push({ key:'carruth', status:'fail', label:`${spec.angle}° pitch is below Carruth's 6° minimum break angle` })
      else
        G.push({ key:'carruth', status:'pass', label:`${spec.angle}° ≥ Carruth 6° floor` })
    }

    // Rod width fits inside nut
    const minWall = 2.5   // mm each side, min structural wall
    if (spec.rodWidthMm + minWall * 2 > nutWidthMm)
      G.push({ key:'rod-nut', status:'fail', label:`Rod ${spec.rodWidthMm}mm + ${minWall*2}mm walls exceeds nut ${nutWidthMm.toFixed(0)}mm` })
    else
      G.push({ key:'rod-nut', status:'pass', label:`Rod ${spec.rodWidthMm}mm fits nut width (${derived.value.wallThicknessMm.toFixed(1)}mm walls)` })

    // End mill ≤ rod width
    if (spec.endMillMm > spec.rodWidthMm)
      G.push({ key:'endmill', status:'fail', label:`End mill Ø${spec.endMillMm}mm > rod width ${spec.rodWidthMm}mm — channel too narrow` })
    else
      G.push({ key:'endmill', status:'pass', label:`End mill Ø${spec.endMillMm}mm ≤ rod ${spec.rodWidthMm}mm` })

    // Edge clearance
    if (spec.edgeClearMm < 4)
      G.push({ key:'edge', status:'warn', label:`Edge clearance ${spec.edgeClearMm}mm — minimum 4mm recommended` })
    else
      G.push({ key:'edge', status:'pass', label:`Edge clearance ${spec.edgeClearMm}mm OK` })

    // Inline column fits headstock length
    if (spec.tunerPattern === '6L' || spec.tunerPattern === '6R') {
      const colH = derived.value.columnHeightMm
      if (colH > headstockLengthMm * 0.85)
        G.push({ key:'column', status:'warn', label:`6-inline column ${colH.toFixed(0)}mm — check headstock length (${headstockLengthMm.toFixed(0)}mm)` })
      else
        G.push({ key:'column', status:'pass', label:`6-inline column ${colH.toFixed(0)}mm fits headstock` })
    }

    // Head-access slot on flat headstock (unusual — flag for confirmation)
    if (spec.rodAccess === 'head' && spec.pitchStyle === 'flat')
      G.push({ key:'head-flat', status:'warn', label:'Head-access slot on flat headstock — confirm nut shelf depth' })

    return G
  })

  // ── Tuner hole positions (canvas units 0-200 × 0-320) ──────────────────────

  const tunerHoles = computed<TunerHoleSpec[]>(() => {
    const nutWidthU   = nutWidthMm   / MM
    const headLenU    = headstockLengthMm / MM
    const insetU      = spec.edgeClearMm / MM
    const postCCu     = spec.postCCmm    / MM
    const postRu      = (spec.postDiamMm / 2) / MM
    const screwRu     = (spec.screwDiamMm / 2) / MM

    const cx    = 100                        // headstock centreline
    const nutY  = 298                        // nut Y in canvas units
    const tipY  = nutY - headLenU
    const bassX = cx - nutWidthU / 2 + insetU
    const trebX = cx + nutWidthU / 2 - insetU

    const column = (x: number, count: number, side: 'bass' | 'treble'): TunerHoleSpec[] =>
      Array.from({ length: count }, (_, i) => ({
        x,
        y: tipY + (nutY - tipY) * ((i + 0.5) / count),
        postR:  postRu,
        screwR: screwRu,
        side,
        index: i,
      }))

    switch (spec.tunerPattern) {
      case '3+3': return [...column(bassX, 3, 'bass'), ...column(trebX, 3, 'treble')]
      case '6L':  return column(bassX, 6, 'bass')
      case '6R':  return column(trebX, 6, 'treble')
      case '4+2': return [...column(bassX, 4, 'bass'), ...column(trebX, 2, 'treble')]
    }
  })

  // ── Rod channel spec (canvas units) ────────────────────────────────────────

  const rodChannel = computed<RodChannelSpec>(() => {
    const cx       = 100
    const nutY     = 298
    const widthU   = spec.rodWidthMm / MM
    const depthU   = spec.rodDepthMm / MM
    const emRU     = (spec.endMillMm / 2) / MM
    const lenU     = spec.rodLengthMm / MM

    if (spec.rodAccess === 'head') {
      // Channel runs from nut toward headstock tip
      return {
        cx,
        startY: nutY,
        endY:   nutY - lenU * 0.38,   // headstock portion of channel
        widthU, depthU, emRadiusU: emRU,
      }
    } else {
      // Heel access — channel starts just past nut into neck
      return {
        cx,
        startY: nutY,
        endY:   nutY - lenU,          // full length into neck
        widthU, depthU, emRadiusU: emRU,
      }
    }
  })

  // ── DXF export payload (merges into ExportRequest) ─────────────────────────

  const exportPayload = computed(() => ({
    tuner_holes: tunerHoles.value.map(t => ({
      x:      t.x,
      y:      t.y,
      radius: t.postR,
    })),
    truss_rod: {
      access:       spec.rodAccess,
      type:         spec.rodType,
      width_mm:     spec.rodWidthMm,
      depth_mm:     spec.rodDepthMm,
      length_mm:    spec.rodLengthMm,
      end_mill_mm:  spec.endMillMm,
      cx_u:         rodChannel.value.cx,
      start_y_u:    rodChannel.value.startY,
      end_y_u:      rodChannel.value.endY,
    },
    pitch: {
      style:        spec.pitchStyle,
      angle_deg:    spec.pitchStyle === 'flat' ? 0 : spec.angle,
      fixture_note: derived.value.fixtureNote,
    },
    screw_holes: tunerHoles.value.flatMap(t => {
      // Two mounting screws per tuner, offset perpendicular to column axis
      const offU = t.postR * 2.2
      return [
        { x: t.x - offU, y: t.y, radius: t.screwR },
        { x: t.x + offU, y: t.y, radius: t.screwR },
      ]
    }),
  }))

  // ── Helpers ────────────────────────────────────────────────────────────────

  function setSpec<K extends keyof CamSpec>(key: K, value: CamSpec[K]) {
    (spec as any)[key] = value
  }

  function loadFromParams(p: ParametricParams) {
    // Sync nut width and headstock length from parametric params if available
    // (caller passes updated nutWidthMm and headstockLengthMm externally)
  }

  function resetToDefaults() {
    Object.assign(spec, DEFAULT_SPEC)
  }

  return {
    spec:          readonly(spec),
    derived,
    gates,
    tunerHoles,
    rodChannel,
    exportPayload,
    setSpec,
    loadFromParams,
    resetToDefaults,
  }
}
