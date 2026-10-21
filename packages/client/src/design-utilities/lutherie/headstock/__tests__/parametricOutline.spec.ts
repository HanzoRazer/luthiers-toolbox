import { createHash } from "node:crypto"
import { describe, expect, it } from "vitest"
import {
  HEADSTOCK_OUTLINE_DEFAULTS,
  HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX,
  HEADSTOCK_OUTLINE_PARAMETER_DEFS,
  HEADSTOCK_OUTLINE_VIEWPORT_PAD,
  HeadstockOutlineError,
  buildHeadstockOutlinePath,
  validateHeadstockOutlineParams,
  type HeadstockOutlineParams,
  type HeadstockTipStyle,
} from "../parametricOutline"

const DEFAULTS: HeadstockOutlineParams = { ...HEADSTOCK_OUTLINE_DEFAULTS }

const ARCHIVED_DEFAULTS: Record<HeadstockTipStyle, string> = {
  rounded: "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 66.00,112.04 66.00,88.24 C 66.00,71.44 71.00,43.20 71.00,22.00 C 71.00,4.00 129.00,4.00 129.00,22.00 C 129.00,43.20 134.00,71.44 134.00,88.24 C 134.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
  squared: "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 66.00,112.04 66.00,88.24 C 66.00,71.44 71.00,43.20 71.00,22.00 L 71.00,20.00 L 100.00,16.60 L 129.00,20.00 L 129.00,22.00 C 129.00,43.20 134.00,71.44 134.00,88.24 C 134.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
  pointed: "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 66.00,112.04 66.00,88.24 C 66.00,71.44 71.00,43.20 71.00,22.00 L 100.00,-5.00 L 129.00,22.00 C 129.00,43.20 134.00,71.44 134.00,88.24 C 134.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
  scroll: "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 66.00,112.04 66.00,88.24 C 66.00,71.44 71.00,43.20 71.00,22.00 C 60.20,16.60 60.20,2.20 100.00,2.20 C 134.40,2.20 132.60,18.40 129.00,22.00 C 129.00,43.20 134.00,71.44 134.00,88.24 C 134.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
}

const ARCHIVED_SHA256: Record<HeadstockTipStyle, string> = {
  rounded: "0a9260463c7a4620eadeabed4642ee6a190085771043fe90ad2a67d5cd2fa939",
  squared: "2c474db034c7c671ae6ff0ce85f7f8aac080b1b176b8961eda81916ee364dfd6",
  pointed: "c189b2bf9c1eccb020e2ff59251ce98c3035c1015016e248d60116a1b20c704f",
  scroll: "596a28bae496f55bd9c7620d4ec35c61fc374f80a490f7a1932489d2d7f5eed7",
}

function sha256(value: string): string {
  return createHash("sha256").update(value).digest("hex")
}

function assertClosedFinite(path: string) {
  expect(path.startsWith("M ")).toBe(true)
  expect(path.endsWith(" Z")).toBe(true)
  expect(path).not.toMatch(/NaN|Infinity|undefined|null/)
}

describe("archived outline equivalence", () => {
  it("matches the archived default path for every tip style", () => {
    for (const style of Object.keys(ARCHIVED_DEFAULTS) as HeadstockTipStyle[]) {
      const path = buildHeadstockOutlinePath(DEFAULTS, style)
      expect(path).toBe(ARCHIVED_DEFAULTS[style])
      expect(sha256(path)).toBe(ARCHIVED_SHA256[style])
    }
  })

  it("matches one non-default archived fixture per tip style", () => {
    expect(buildHeadstockOutlinePath({ ...DEFAULTS, nutWidth: 80 }, "rounded")).toBe(
      "M 60.00,298.00 C 60.00,251.85 62.00,232.97 62.00,193.12 C 62.00,149.07 66.00,112.04 66.00,88.24 C 66.00,71.44 71.00,43.20 71.00,22.00 C 71.00,4.00 129.00,4.00 129.00,22.00 C 129.00,43.20 134.00,71.44 134.00,88.24 C 134.00,112.04 138.00,149.07 138.00,193.12 C 138.00,232.97 140.00,251.85 140.00,298.00 Z",
    )
    expect(buildHeadstockOutlinePath({ ...DEFAULTS, length: 200 }, "squared")).toBe(
      "M 65.00,298.00 C 65.00,264.56 67.00,250.88 67.00,222.00 C 67.00,190.08 66.00,169.80 66.00,146.00 C 66.00,129.20 71.00,113.36 71.00,98.00 L 71.00,96.00 L 100.00,92.60 L 129.00,96.00 L 129.00,98.00 C 129.00,113.36 134.00,129.20 134.00,146.00 C 134.00,169.80 133.00,190.08 133.00,222.00 C 133.00,250.88 135.00,264.56 135.00,298.00 Z",
    )
    expect(buildHeadstockOutlinePath({ ...DEFAULTS, tipWidth: 16 }, "pointed")).toBe(
      "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 87.00,112.04 87.00,88.24 C 87.00,71.44 92.00,43.20 92.00,22.00 L 100.00,-5.00 L 108.00,22.00 C 108.00,43.20 113.00,71.44 113.00,88.24 C 113.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
    )
    expect(buildHeadstockOutlinePath({ ...DEFAULTS, asymmetry: -20 }, "scroll")).toBe(
      "M 65.00,298.00 C 65.00,251.85 67.00,232.97 67.00,193.12 C 67.00,149.07 56.00,112.04 56.00,88.24 C 56.00,71.44 61.00,43.20 61.00,22.00 C 50.20,16.60 50.20,2.20 94.00,2.20 C 124.40,2.20 122.60,18.40 119.00,22.00 C 119.00,43.20 124.00,71.44 124.00,88.24 C 124.00,112.04 133.00,149.07 133.00,193.12 C 133.00,232.97 135.00,251.85 135.00,298.00 Z",
    )
  })
})

describe("outline kernel", () => {
  it("repeats the same string for the same input", () => {
    const first = buildHeadstockOutlinePath(DEFAULTS, "rounded")
    const second = buildHeadstockOutlinePath({ ...DEFAULTS }, "rounded")
    expect(first).toBe(second)
  })

  it("gives each tip style a distinct closed path", () => {
    const paths = (Object.keys(ARCHIVED_DEFAULTS) as HeadstockTipStyle[]).map((style) =>
      buildHeadstockOutlinePath(DEFAULTS, style),
    )
    for (const path of paths) assertClosedFinite(path)
    expect(new Set(paths).size).toBe(4)
  })

  it("changes the path when any body or shoulder parameter changes", () => {
    const base = buildHeadstockOutlinePath(DEFAULTS, "rounded")
    for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
      const alternate = DEFAULTS[def.id] === def.max ? def.min : def.max
      const params = { ...DEFAULTS, [def.id]: alternate }
      expect(buildHeadstockOutlinePath(params, "rounded")).not.toBe(base)
    }
  })

  it("accepts every documented minimum and maximum", () => {
    const min = {} as HeadstockOutlineParams
    const max = {} as HeadstockOutlineParams
    for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
      min[def.id] = def.min
      max[def.id] = def.max
    }
    expect(validateHeadstockOutlineParams(min).valid).toBe(true)
    expect(validateHeadstockOutlineParams(max).valid).toBe(true)
    assertClosedFinite(buildHeadstockOutlinePath(min, "scroll"))
    assertClosedFinite(buildHeadstockOutlinePath(max, "pointed"))
  })

  it("rejects values outside the documented range", () => {
    expect(validateHeadstockOutlineParams({ ...DEFAULTS, nutWidth: 53.9 }).valid).toBe(false)
    expect(validateHeadstockOutlineParams({ ...DEFAULTS, length: 310.1 }).valid).toBe(false)
    expect(() => buildHeadstockOutlinePath({ ...DEFAULTS, taper: -20.1 }, "rounded")).toThrow(HeadstockOutlineError)
    expect(() => buildHeadstockOutlinePath({ ...DEFAULTS, tipRounding: 51 }, "rounded")).toThrow(HeadstockOutlineError)
  })

  it("rejects missing, non-finite, and unknown tip styles", () => {
    const missing = { ...DEFAULTS } as Partial<HeadstockOutlineParams>
    delete missing.waistPos
    const missingResult = validateHeadstockOutlineParams(missing as HeadstockOutlineParams)
    expect(missingResult.valid).toBe(false)
    expect(missingResult.errors.join(" ")).toMatch(/Waist pos/)

    for (const bad of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
      expect(validateHeadstockOutlineParams({ ...DEFAULTS, bassShoulder: bad }).valid).toBe(false)
    }
    expect(() => buildHeadstockOutlinePath(DEFAULTS, "volute" as HeadstockTipStyle)).toThrow(HeadstockOutlineError)
  })

  it("does not expose tuner placement", async () => {
    const kernel = await import("../parametricOutline")
    expect(kernel).not.toHaveProperty("buildTunerPositions")
    expect(kernel).not.toHaveProperty("MM")
    expect(Object.keys(HEADSTOCK_OUTLINE_DEFAULTS)).not.toContain("pegInset")
    expect(HEADSTOCK_OUTLINE_PARAMETER_DEFS.map((def) => def.id)).not.toContain("pegSpacing")
  })
})

const STYLES = Object.keys(ARCHIVED_DEFAULTS) as HeadstockTipStyle[]

function viewBoxRect(viewBox: string) {
  const [minX, minY, width, height] = viewBox.split(" ").map(Number)
  return { minX, minY, maxX: minX + width, maxY: minY + height }
}

function coordinates(path: string): Array<[number, number]> {
  const numbers = path.match(/-?\d+\.\d+/g)?.map(Number) ?? []
  const pairs: Array<[number, number]> = []
  for (let index = 0; index < numbers.length; index += 2) {
    pairs.push([numbers[index], numbers[index + 1]])
  }
  return pairs
}

function expectInside(path: string) {
  const box = viewBoxRect(HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX)
  for (const [x, y] of coordinates(path)) {
    expect(x).toBeGreaterThanOrEqual(box.minX)
    expect(x).toBeLessThanOrEqual(box.maxX)
    expect(y).toBeGreaterThanOrEqual(box.minY)
    expect(y).toBeLessThanOrEqual(box.maxY)
  }
}

function atLimits(bound: "min" | "max"): HeadstockOutlineParams {
  const params = {} as HeadstockOutlineParams
  for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
    params[def.id] = def[bound]
  }
  return params
}

describe("display viewport", () => {
  it("fits every default style, including the pointed tip below Y = 0", () => {
    expect(HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX.startsWith("0 0 200 320")).toBe(false)
    for (const style of STYLES) {
      const path = buildHeadstockOutlinePath(DEFAULTS, style)
      expect(sha256(path)).toBe(ARCHIVED_SHA256[style])
      expectInside(path)
    }
    const pointed = coordinates(ARCHIVED_DEFAULTS.pointed)
    expect(pointed.some(([, y]) => y === -5)).toBe(true)
    expectInside(ARCHIVED_DEFAULTS.pointed)
  })

  it("keeps minimum and maximum parameter vectors inside the viewport", () => {
    for (const params of [atLimits("min"), atLimits("max")]) {
      for (const style of STYLES) {
        expectInside(buildHeadstockOutlinePath(params, style))
      }
    }
  })

  it("pads past every range-corner control point without changing path hashes", () => {
    let minX = Number.POSITIVE_INFINITY
    let minY = Number.POSITIVE_INFINITY
    let maxX = Number.NEGATIVE_INFINITY
    let maxY = Number.NEGATIVE_INFINITY
    const count = 1 << HEADSTOCK_OUTLINE_PARAMETER_DEFS.length
    for (let mask = 0; mask < count; mask += 1) {
      const params = {} as HeadstockOutlineParams
      HEADSTOCK_OUTLINE_PARAMETER_DEFS.forEach((def, index) => {
        params[def.id] = (mask & (1 << index)) === 0 ? def.min : def.max
      })
      for (const style of STYLES) {
        const path = buildHeadstockOutlinePath(params, style)
        for (const [x, y] of coordinates(path)) {
          minX = Math.min(minX, x)
          minY = Math.min(minY, y)
          maxX = Math.max(maxX, x)
          maxY = Math.max(maxY, y)
        }
      }
    }
    const box = viewBoxRect(HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX)
    expect(box.minX).toBeLessThanOrEqual(minX - HEADSTOCK_OUTLINE_VIEWPORT_PAD)
    expect(box.minY).toBeLessThanOrEqual(minY - HEADSTOCK_OUTLINE_VIEWPORT_PAD)
    expect(box.maxX).toBeGreaterThanOrEqual(maxX + HEADSTOCK_OUTLINE_VIEWPORT_PAD)
    expect(box.maxY).toBeGreaterThanOrEqual(maxY + HEADSTOCK_OUTLINE_VIEWPORT_PAD)
    for (const style of STYLES) {
      expect(sha256(buildHeadstockOutlinePath(DEFAULTS, style))).toBe(ARCHIVED_SHA256[style])
    }
  })
})
