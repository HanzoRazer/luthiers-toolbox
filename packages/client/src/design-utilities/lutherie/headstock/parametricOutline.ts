/**
 * Parametric headstock outline in recovered model space.
 *
 * Provenance: port of `buildHeadstockPath` from the PR #443 recovery of
 * `ps-vue-src/composables/useHeadstockPath.ts`. Defaults and ranges are the
 * BODY and SHOULDER groups of `ps-vue-src/components/headstock/constants.ts`.
 * Tip styles follow `TipStyle` 0–3 in `ps-vue-src/types/headstock.ts`
 * (Rounded, Squared, Pointed, Scroll). The archive directory is recorded in
 * `docs/investigations/headstock-integration-feasibility-002_2026-10-19/NEXT_ORDER.md`.
 * This module does not import it.
 *
 * Coordinates are the suite's 200×320 drawing space (nut datum y=298, center x=100).
 * They are outline units, not millimeters. The archived `MM = 0.215` factor is not applied.
 */

export type HeadstockTipStyle = "rounded" | "squared" | "pointed" | "scroll"

export interface HeadstockOutlineParams {
  nutWidth: number
  length: number
  tipWidth: number
  asymmetry: number
  taper: number
  waistDepth: number
  waistPos: number
  bassShoulder: number
  trebleShoulder: number
  tipRounding: number
}

export interface HeadstockParameterDefinition {
  id: keyof HeadstockOutlineParams
  label: string
  group: "BODY" | "SHOULDER"
  min: number
  max: number
  step: number
}

export interface HeadstockOutlineValidation {
  valid: boolean
  errors: string[]
}

export class HeadstockOutlineError extends Error {
  readonly errors: string[]

  constructor(errors: string[]) {
    super(errors.join("; "))
    this.name = "HeadstockOutlineError"
    this.errors = errors
  }
}

export const HEADSTOCK_OUTLINE_PARAMETER_DEFS: readonly HeadstockParameterDefinition[] = [
  { id: "nutWidth", label: "Nut width", group: "BODY", min: 54, max: 80, step: 0.5 },
  { id: "length", label: "Length", group: "BODY", min: 200, max: 310, step: 1 },
  { id: "tipWidth", label: "Tip width", group: "BODY", min: 16, max: 90, step: 0.5 },
  { id: "asymmetry", label: "Asymmetry", group: "BODY", min: -20, max: 20, step: 0.5 },
  { id: "taper", label: "Taper", group: "BODY", min: -20, max: 30, step: 0.5 },
  { id: "waistDepth", label: "Waist depth", group: "SHOULDER", min: 0, max: 25, step: 0.5 },
  { id: "waistPos", label: "Waist pos", group: "SHOULDER", min: 0.2, max: 0.65, step: 0.01 },
  { id: "bassShoulder", label: "Bass R", group: "SHOULDER", min: 8, max: 60, step: 0.5 },
  { id: "trebleShoulder", label: "Treble R", group: "SHOULDER", min: 8, max: 60, step: 0.5 },
  { id: "tipRounding", label: "Tip round", group: "SHOULDER", min: 0, max: 50, step: 1 },
]

export const HEADSTOCK_OUTLINE_DEFAULTS: Readonly<HeadstockOutlineParams> = {
  nutWidth: 70,
  length: 276,
  tipWidth: 58,
  asymmetry: 0,
  taper: 0,
  waistDepth: 2,
  waistPos: 0.38,
  bassShoulder: 28,
  trebleShoulder: 28,
  tipRounding: 18,
}

const TIP_STYLES: readonly HeadstockTipStyle[] = ["rounded", "squared", "pointed", "scroll"]

function isTipStyle(style: string): style is HeadstockTipStyle {
  return (TIP_STYLES as readonly string[]).includes(style)
}

export function validateHeadstockOutlineParams(
  params: HeadstockOutlineParams,
): HeadstockOutlineValidation {
  const errors: string[] = []
  if (params === null || typeof params !== "object") {
    return { valid: false, errors: ["Outline parameters are missing."] }
  }
  for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
    const value = params[def.id]
    if (typeof value !== "number") {
      errors.push(`${def.label} is missing.`)
      continue
    }
    if (!Number.isFinite(value)) {
      errors.push(`${def.label} must be a finite outline-unit number.`)
      continue
    }
    if (value < def.min) {
      errors.push(`${def.label} is below ${def.min}.`)
    } else if (value > def.max) {
      errors.push(`${def.label} is above ${def.max}.`)
    }
  }
  return { valid: errors.length === 0, errors }
}

/**
 * Closed SVG path. Throws when the parameters or tip style are outside the recovered contract.
 * The curve construction is the archived function, including `(taper || 0)` after validation
 * has already rejected non-finite taper.
 */
export function buildHeadstockOutlinePath(
  params: HeadstockOutlineParams,
  style: HeadstockTipStyle,
): string {
  const validation = validateHeadstockOutlineParams(params)
  if (!validation.valid) {
    throw new HeadstockOutlineError(validation.errors)
  }
  if (!isTipStyle(style)) {
    throw new HeadstockOutlineError([`Unsupported tip style: ${String(style)}.`])
  }

  const P = params
  const cx = 100
  const ny = 298
  const nw2 = P.nutWidth / 2
  const tw2 = P.tipWidth / 2
  const asym = P.asymmetry
  const wd = P.waistDepth
  const wp = P.waistPos
  const bsr = P.bassShoulder
  const tsr = P.trebleShoulder
  const tr = P.tipRounding
  const tap = (P.taper || 0) / 2

  const waistY = ny - P.length * wp
  const shoulderY = ny - P.length * 0.76
  const tipY = ny - P.length

  const nutL = cx - nw2
  const nutR = cx + nw2
  const waistL = cx - nw2 + wd
  const waistR = cx + nw2 - wd
  const shouldL = cx - tw2 + asym / 2 - 5 - tap
  const shouldR = cx + tw2 + asym / 2 + 5 + tap
  const tipL = cx - tw2 + asym / 2
  const tipR = cx + tw2 + asym / 2

  const h = (y1: number, y2: number, f = 0.44) => Math.abs(y2 - y1) * f
  const fmt = (v: number) => v.toFixed(2)

  const leftSide = [
    `C ${fmt(nutL)},${fmt(ny - h(ny, waistY))} ${fmt(waistL)},${fmt(waistY + h(waistY, ny, 0.38))} ${fmt(waistL)},${fmt(waistY)}`,
    `C ${fmt(waistL)},${fmt(waistY - h(waistY, shoulderY, 0.42))} ${fmt(shouldL)},${fmt(shoulderY + bsr * 0.85)} ${fmt(shouldL)},${fmt(shoulderY)}`,
    `C ${fmt(shouldL)},${fmt(shoulderY - bsr * 0.6)} ${fmt(tipL)},${fmt(tipY + h(tipY, shoulderY, 0.32))} ${fmt(tipL)},${fmt(tipY)}`,
  ].join(" ")

  let tip: string
  switch (style) {
    case "rounded":
      tip = `C ${fmt(tipL)},${fmt(tipY - tr)} ${fmt(tipR)},${fmt(tipY - tr)} ${fmt(tipR)},${fmt(tipY)}`
      break
    case "squared":
      tip = `L ${fmt(tipL)},${fmt(tipY - 2)} L ${fmt(cx)},${fmt(tipY - tr * 0.3)} L ${fmt(tipR)},${fmt(tipY - 2)} L ${fmt(tipR)},${fmt(tipY)}`
      break
    case "pointed":
      tip = `L ${fmt(cx + asym * 0.4)},${fmt(tipY - tr * 1.5)} L ${fmt(tipR)},${fmt(tipY)}`
      break
    case "scroll":
      tip = `C ${fmt(tipL - tr * 0.6)},${fmt(tipY - tr * 0.3)} ${fmt(tipL - tr * 0.6)},${fmt(tipY - tr * 1.1)} ${fmt(cx + asym * 0.3)},${fmt(tipY - tr * 1.1)} `
        + `C ${fmt(tipR + tr * 0.3)},${fmt(tipY - tr * 1.1)} ${fmt(tipR + tr * 0.2)},${fmt(tipY - tr * 0.2)} ${fmt(tipR)},${fmt(tipY)}`
      break
  }

  const rightSide = [
    `C ${fmt(tipR)},${fmt(tipY + h(tipY, shoulderY, 0.32))} ${fmt(shouldR)},${fmt(shoulderY - tsr * 0.6)} ${fmt(shouldR)},${fmt(shoulderY)}`,
    `C ${fmt(shouldR)},${fmt(shoulderY + tsr * 0.85)} ${fmt(waistR)},${fmt(waistY - h(waistY, shoulderY, 0.42))} ${fmt(waistR)},${fmt(waistY)}`,
    `C ${fmt(waistR)},${fmt(waistY + h(waistY, ny, 0.38))} ${fmt(nutR)},${fmt(ny - h(ny, waistY))} ${fmt(nutR)},${fmt(ny)}`,
  ].join(" ")

  return `M ${fmt(nutL)},${fmt(ny)} ${leftSide} ${tip} ${rightSide} Z`
}

/**
 * Display window for the recovered model space.
 *
 * The path is still built in the suite's 200×320 drawing space. Valid corners of
 * the declared ranges place control points outside that frame; the default pointed
 * tip includes Y = -5.00. A viewBox of "0 0 200 320" clips those points.
 *
 * Cubic segments stay inside the convex hull of their control points, and each
 * control-point coordinate is linear in the parameters, so the extremes sit on
 * range corners. This viewport is those corner bounds plus
 * {@link HEADSTOCK_OUTLINE_VIEWPORT_PAD} outline units, which covers the 1-unit
 * stroke. It does not change `buildHeadstockOutlinePath`.
 */
export const HEADSTOCK_OUTLINE_VIEWPORT_PAD = 2

export interface HeadstockOutlineViewport {
  minX: number
  minY: number
  width: number
  height: number
  viewBox: string
}

function rangeCorners(): HeadstockOutlineParams[] {
  const count = 1 << HEADSTOCK_OUTLINE_PARAMETER_DEFS.length
  const corners: HeadstockOutlineParams[] = []
  for (let mask = 0; mask < count; mask += 1) {
    const params = {} as HeadstockOutlineParams
    HEADSTOCK_OUTLINE_PARAMETER_DEFS.forEach((def, index) => {
      params[def.id] = (mask & (1 << index)) === 0 ? def.min : def.max
    })
    corners.push(params)
  }
  return corners
}

function controlPointBounds(): { minX: number; minY: number; maxX: number; maxY: number } {
  let minX = Number.POSITIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY
  for (const params of rangeCorners()) {
    for (const style of TIP_STYLES) {
      const numbers = buildHeadstockOutlinePath(params, style).match(/-?\d+\.\d+/g) ?? []
      for (let index = 0; index < numbers.length; index += 2) {
        const x = Number(numbers[index])
        const y = Number(numbers[index + 1])
        minX = Math.min(minX, x)
        minY = Math.min(minY, y)
        maxX = Math.max(maxX, x)
        maxY = Math.max(maxY, y)
      }
    }
  }
  return { minX, minY, maxX, maxY }
}

export function headstockOutlineDisplayViewport(): HeadstockOutlineViewport {
  const bounds = controlPointBounds()
  const pad = HEADSTOCK_OUTLINE_VIEWPORT_PAD
  const minX = bounds.minX - pad
  const minY = bounds.minY - pad
  const width = bounds.maxX - bounds.minX + pad * 2
  const height = bounds.maxY - bounds.minY + pad * 2
  const fmt = (value: number) => value.toFixed(2)
  return {
    minX,
    minY,
    width,
    height,
    viewBox: `${fmt(minX)} ${fmt(minY)} ${fmt(width)} ${fmt(height)}`,
  }
}

export const HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX = headstockOutlineDisplayViewport().viewBox
