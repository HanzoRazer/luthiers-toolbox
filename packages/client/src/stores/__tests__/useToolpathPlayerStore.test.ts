import { describe, it, expect } from "vitest";
import {
  binarySearchCumulative,
  downsampleSegments,
} from "@/stores/useToolpathPlayerStore";
import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";

function seg(partial: Partial<MoveSegment>): MoveSegment {
  return {
    type: "cut",
    from_pos: [0, 0, 0],
    to_pos: [1, 0, 0],
    feed: 600,
    duration_ms: 5,
    line_number: 1,
    line_text: "",
    ...partial,
  };
}

// F-X2: the cumulative-time search is a strict lower bound, so an exact
// boundary maps to the *start* of the next segment. Step/seek/jump rely on it.
describe("binarySearchCumulative (F-X2)", () => {
  const cum = [10, 20, 30]; // three segments, 10ms each

  it("returns the first segment near the start", () => {
    expect(binarySearchCumulative(cum, 0)).toBe(0);
    expect(binarySearchCumulative(cum, 5)).toBe(0);
  });

  it("maps an exact boundary to the next segment's start", () => {
    expect(binarySearchCumulative(cum, 10)).toBe(1);
    expect(binarySearchCumulative(cum, 20)).toBe(2);
  });

  it("returns the owning segment mid-interval", () => {
    expect(binarySearchCumulative(cum, 15)).toBe(1);
    expect(binarySearchCumulative(cum, 25)).toBe(2);
  });

  it("clamps at and beyond the end", () => {
    expect(binarySearchCumulative(cum, 30)).toBe(2);
    expect(binarySearchCumulative(cum, 999)).toBe(2);
  });

  it("returns -1 for an empty timeline", () => {
    expect(binarySearchCumulative([], 5)).toBe(-1);
  });
});

// F-X3: downsampling must conserve total cycle time (it previously dropped
// the durations of skipped segments).
describe("downsampleSegments (F-X3)", () => {
  it("conserves total duration", () => {
    const segs = Array.from({ length: 20 }, (_, i) =>
      seg({ duration_ms: 5, from_pos: [i, 0, 0], to_pos: [i + 1, 0, 0] }),
    );
    const before = segs.reduce((s, x) => s + x.duration_ms, 0);
    const out = downsampleSegments(segs, 5);
    const after = out.reduce((s, x) => s + x.duration_ms, 0);
    expect(out.length).toBeLessThan(segs.length);
    expect(after).toBeCloseTo(before, 6);
  });

  it("preserves the final endpoint", () => {
    const segs = Array.from({ length: 20 }, (_, i) =>
      seg({ from_pos: [i, 0, 0], to_pos: [i + 1, 0, 0] }),
    );
    const out = downsampleSegments(segs, 4);
    expect(out[out.length - 1].to_pos).toEqual([20, 0, 0]);
  });

  it("keeps rapids whole and still conserves time", () => {
    const segs = [
      seg({ type: "rapid", duration_ms: 3 }),
      ...Array.from({ length: 10 }, () => seg({ duration_ms: 2 })),
      seg({ type: "rapid", duration_ms: 4 }),
    ];
    const before = segs.reduce((s, x) => s + x.duration_ms, 0);
    const out = downsampleSegments(segs, 3);
    expect(out.filter((s) => s.type === "rapid").length).toBe(2);
    const after = out.reduce((s, x) => s + x.duration_ms, 0);
    expect(after).toBeCloseTo(before, 6);
  });

  it("returns the input unchanged when already under target", () => {
    const segs = [seg({}), seg({})];
    expect(downsampleSegments(segs, 100)).toBe(segs);
  });
});
