import { computed } from 'vue'
import type { HeadstockParams, TipStyle, TunerPattern } from '@/types/headstock'

/** Canvas units → mm conversion factor */
export const MM = 0.215

/**
 * Build a closed SVG path string from HeadstockParams.
 * All coordinates live in the 200 × 320 path space (nut datum at y=298, cx=100).
 */
export function buildHeadstockPath(P: HeadstockParams, style: TipStyle): string {
  const cx = 100, ny = 298
  const nw2  = P.nutWidth   / 2
  const tw2  = P.tipWidth   / 2
  const asym = P.asymmetry
  const wd   = P.waistDepth
  const wp   = P.waistPos
  const bsr  = P.bassShoulder
  const tsr  = P.trebleShoulder
  const tr   = P.tipRounding
  const tap  = (P.taper || 0) / 2

  const waistY    = ny - P.length * wp
  const shoulderY = ny - P.length * 0.76
  const tipY      = ny - P.length

  const nutL    = cx - nw2
  const nutR    = cx + nw2
  const waistL  = cx - nw2 + wd
  const waistR  = cx + nw2 - wd
  const shouldL = cx - tw2 + asym / 2 - 5 - tap
  const shouldR = cx + tw2 + asym / 2 + 5 + tap
  const tipL    = cx - tw2 + asym / 2
  const tipR    = cx + tw2 + asym / 2

  const h = (y1: number, y2: number, f = 0.44) => Math.abs(y2 - y1) * f
  const f = (v: number) => v.toFixed(2)

  const leftSide = [
    `C ${f(nutL)},${f(ny - h(ny, waistY))} ${f(waistL)},${f(waistY + h(waistY, ny, 0.38))} ${f(waistL)},${f(waistY)}`,
    `C ${f(waistL)},${f(waistY - h(waistY, shoulderY, 0.42))} ${f(shouldL)},${f(shoulderY + bsr * 0.85)} ${f(shouldL)},${f(shoulderY)}`,
    `C ${f(shouldL)},${f(shoulderY - bsr * 0.6)} ${f(tipL)},${f(tipY + h(tipY, shoulderY, 0.32))} ${f(tipL)},${f(tipY)}`,
  ].join(' ')

  let tip: string
  switch (style) {
    case 0: tip = `C ${f(tipL)},${f(tipY - tr)} ${f(tipR)},${f(tipY - tr)} ${f(tipR)},${f(tipY)}`; break
    case 1: tip = `L ${f(tipL)},${f(tipY - 2)} L ${f(cx)},${f(tipY - tr * 0.3)} L ${f(tipR)},${f(tipY - 2)} L ${f(tipR)},${f(tipY)}`; break
    case 2: tip = `L ${f(cx + asym * 0.4)},${f(tipY - tr * 1.5)} L ${f(tipR)},${f(tipY)}`; break
    default: {
      tip = `C ${f(tipL - tr * 0.6)},${f(tipY - tr * 0.3)} ${f(tipL - tr * 0.6)},${f(tipY - tr * 1.1)} ${f(cx + asym * 0.3)},${f(tipY - tr * 1.1)} `
          + `C ${f(tipR + tr * 0.3)},${f(tipY - tr * 1.1)} ${f(tipR + tr * 0.2)},${f(tipY - tr * 0.2)} ${f(tipR)},${f(tipY)}`
    }
  }

  const rightSide = [
    `C ${f(tipR)},${f(tipY + h(tipY, shoulderY, 0.32))} ${f(shouldR)},${f(shoulderY - tsr * 0.6)} ${f(shouldR)},${f(shoulderY)}`,
    `C ${f(shouldR)},${f(shoulderY + tsr * 0.85)} ${f(waistR)},${f(waistY - h(waistY, shoulderY, 0.42))} ${f(waistR)},${f(waistY)}`,
    `C ${f(waistR)},${f(waistY + h(waistY, ny, 0.38))} ${f(nutR)},${f(ny - h(ny, waistY))} ${f(nutR)},${f(ny)}`,
  ].join(' ')

  return `M ${f(nutL)},${f(ny)} ${leftSide} ${tip} ${rightSide} Z`
}

/** Tuner position layout in path space */
export interface TunerPos { x: number; y: number; side: 'bass' | 'treble' }

export function buildTunerPositions(P: HeadstockParams, pat: TunerPattern): TunerPos[] {
  const cx = 100, ny = 298
  const tipY = ny - P.length
  const span = ny - tipY
  const bassX   = cx - P.nutWidth / 2 + P.pegInset
  const trebleX = cx + P.nutWidth / 2 - P.pegInset

  const spread = (n: number, i: number) => tipY + span * (i + 0.5) / n

  switch (pat) {
    case '6L': return Array.from({ length: 6 }, (_, i) => ({ x: bassX,   y: spread(6, i), side: 'bass'   as const }))
    case '6R': return Array.from({ length: 6 }, (_, i) => ({ x: trebleX, y: spread(6, i), side: 'treble' as const }))
    case '3+3': return [
      ...Array.from({ length: 3 }, (_, i) => ({ x: bassX,   y: spread(3, i), side: 'bass'   as const })),
      ...Array.from({ length: 3 }, (_, i) => ({ x: trebleX, y: spread(3, i), side: 'treble' as const })),
    ]
    case '4+2': return [
      ...Array.from({ length: 4 }, (_, i) => ({ x: bassX,   y: spread(4, i), side: 'bass'   as const })),
      ...Array.from({ length: 2 }, (_, i) => ({ x: trebleX, y: spread(2, i), side: 'treble' as const })),
    ]
    case '3+2+1': return [
      ...Array.from({ length: 3 }, (_, i) => ({ x: bassX,   y: spread(3, i), side: 'bass'   as const })),
      ...Array.from({ length: 2 }, (_, i) => ({ x: trebleX, y: spread(2, i), side: 'treble' as const })),
      { x: cx, y: tipY + span * 0.5, side: 'bass' as const },
    ]
  }
}

/**
 * Composable: reactive path string that updates whenever params or style change.
 */
export function useHeadstockPath(
  getParams: () => HeadstockParams,
  getStyle:  () => TipStyle,
) {
  return computed(() => buildHeadstockPath(getParams(), getStyle()))
}
