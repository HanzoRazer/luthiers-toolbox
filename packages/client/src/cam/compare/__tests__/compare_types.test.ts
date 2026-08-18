import { describe, expect, it } from "vitest"
import {
  parseBaseline,
  parseCandidate,
  parseDiffResult,
} from "../compare_types"

describe("cam/compare compare_types (zod schemas)", () => {
  it("applies defaults for baseline name/units", () => {
    const b = parseBaseline({ id: "b1" })
    expect(b.id).toBe("b1")
    expect(b.name).toBe("Unnamed Baseline")
    expect(b.units).toBe("mm")
  })

  it("parses move union: cartesian, pt-array, and raw tuple", () => {
    const b = parseBaseline({
      id: "b2",
      name: "Named",
      units: "inch",
      moves: [
        { x: 1, y: 2, z: 3, rapid: true },
        { pt: [4, 5], kind: "cut" },
        [6, 7],
      ],
    })
    expect(b.name).toBe("Named")
    expect(b.units).toBe("inch")
    expect(b.moves).toHaveLength(3)
  })

  it("parses loops with min-3 point tuples", () => {
    const c = parseCandidate({
      id: "c1",
      loops: [{ pts: [[0, 0], [1, 0], [1, 1]] }],
    })
    expect(c.loops?.[0].pts).toHaveLength(3)
  })

  it("rejects loops with fewer than 3 points", () => {
    expect(() =>
      parseCandidate({
        id: "c2",
        loops: [{ pts: [[0, 0], [1, 0]] }],
      })
    ).toThrow()
  })

  it("applies DiffResult defaults", () => {
    const d = parseDiffResult({})
    expect(d.ok).toBe(true)
    expect(d.tolerance).toBe(0.1)
  })
})
