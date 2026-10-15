import { computed } from 'vue'
import type { HeadstockParams, Gate, NoveltyResult, ScoreResult, GateStatus } from '@/types/headstock'
import { CORPUS } from '@/stores/headstock'
import { MM } from './useHeadstockPath'

// ─── Parameter ranges for normalisation ──────────────────────────────────────
const RANGES: Record<keyof HeadstockParams, [number, number]> = {
  nutWidth:        [54, 80],
  length:          [200, 310],
  tipWidth:        [16, 90],
  asymmetry:       [-20, 20],
  taper:           [-20, 30],
  waistDepth:      [0, 25],
  waistPos:        [0.2, 0.65],
  bassShoulder:    [8, 60],
  trebleShoulder:  [8, 60],
  tipRounding:     [0, 50],
  pegSpacing:      [30, 55],
  pegInset:        [8, 20],
}

type NormVec = Record<keyof HeadstockParams, number>

function normalise(p: HeadstockParams): NormVec {
  return Object.fromEntries(
    Object.entries(RANGES).map(([k, [lo, hi]]) => [k, (p[k as keyof HeadstockParams] - lo) / (hi - lo)])
  ) as NormVec
}

function euclidDist(a: NormVec, b: NormVec): number {
  const keys = Object.keys(RANGES) as (keyof HeadstockParams)[]
  const sum  = keys.reduce((acc, k) => acc + (a[k] - b[k]) ** 2, 0)
  return Math.sqrt(sum / keys.length)
}

// ─── Novelty computation ──────────────────────────────────────────────────────

export function computeNovelty(params: HeadstockParams): NoveltyResult {
  const pn = normalise(params)
  const dists = Object.fromEntries(
    Object.entries(CORPUS).map(([name, cp]) => [name, euclidDist(pn, normalise(cp))])
  )
  const minDist   = Math.min(...Object.values(dists))
  const closestTo = Object.entries(dists).sort((a, b) => a[1] - b[1])[0][0]
  const score     = Math.min(Math.round(minDist * 340), 100)
  return { score, minDist, closestTo, corpusDists: dists }
}

// ─── Manufacture gates ────────────────────────────────────────────────────────

export function computeGates(params: HeadstockParams, toolDiaMm: number): Gate[] {
  const P = params
  const toolR = toolDiaMm / 2

  const g = (name: string, detail: string, pass: GateStatus): Gate => ({ name, detail, pass })
  const mmStr = (v: number) => `${v.toFixed(1)} mm`

  const waistWidthMm  = (P.nutWidth - P.waistDepth * 2) * MM
  const tipWidthMm    = P.tipWidth * MM
  const pegClearMm    = (P.pegSpacing - 13) * MM
  const minCurveMm    = Math.min(P.bassShoulder, P.trebleShoulder, P.tipRounding) * MM

  return [
    g(
      'Min material at waist',
      `${mmStr(waistWidthMm)} (≥ 12 mm required)`,
      waistWidthMm >= 12 ? 'pass' : waistWidthMm >= 8 ? 'warn' : 'fail',
    ),
    g(
      'Tip width',
      `${mmStr(tipWidthMm)} (≥ 8 mm required)`,
      tipWidthMm >= 8 ? 'pass' : 'fail',
    ),
    g(
      'Peg clearance',
      `${mmStr(pegClearMm)} between peg centres (≥ 8 mm)`,
      pegClearMm >= 8 ? 'pass' : pegClearMm >= 5 ? 'warn' : 'fail',
    ),
    g(
      `Min curve radius ≥ tool radius (${mmStr(toolR)})`,
      `smallest curve = ${mmStr(minCurveMm)}`,
      minCurveMm >= toolR * 1.1 ? 'pass' : 'warn',
    ),
    g(
      'Waist position',
      `${(P.waistPos * 100).toFixed(0)}% from nut (valid 20–65%)`,
      P.waistPos >= 0.2 && P.waistPos <= 0.65 ? 'pass' : 'fail',
    ),
  ]
}

// ─── Composable ───────────────────────────────────────────────────────────────

export function useScoring(
  getParams:  () => HeadstockParams,
  getToolDia: () => number,
) {
  const result = computed<ScoreResult>(() => ({
    novelty: computeNovelty(getParams()),
    gates:   computeGates(getParams(), getToolDia()),
  }))

  const noveltyColor = computed(() => {
    const s = result.value.novelty.score
    return s < 30 ? '#c85040' : s < 55 ? '#b87020' : '#5ab86a'
  })

  const gatesSummary = computed(() => {
    const gates = result.value.gates
    const pass = gates.filter(g => g.pass === 'pass').length
    const fail = gates.filter(g => g.pass === 'fail').length
    return { pass, fail, warn: gates.length - pass - fail, total: gates.length }
  })

  return { result, noveltyColor, gatesSummary }
}
