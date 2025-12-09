// compareViewportMath.spec.ts
// B22.9: Unit tests for viewport math utilities

import { describe, it, expect } from "vitest";
import {
  computeFitTransform,
  computeZoomToBox,
  type BBox,
} from "./compareViewportMath";

describe("compareViewportMath", () => {
  const squareBox: BBox = { minX: 0, minY: 0, maxX: 100, maxY: 100 };
  const wideBox: BBox = { minX: 0, minY: 0, maxX: 200, maxY: 100 };

  it("fits a square bbox into a square pane with padding", () => {
    const paneWidth = 400;
    const paneHeight = 400;
    const padding = 20;

    const t = computeFitTransform(squareBox, paneWidth, paneHeight, padding);

    // inner size = 360x360, box size = 100x100, scale = 3.6
    expect(t.scale).toBeCloseTo(3.6, 5);

    // center should be roughly pane center
    const cx = (squareBox.minX + squareBox.maxX) / 2;
    const cy = (squareBox.minY + squareBox.maxY) / 2;
    const screenX = cx * t.scale + t.tx;
    const screenY = cy * t.scale + t.ty;

    expect(screenX).toBeCloseTo(paneWidth / 2, 5);
    expect(screenY).toBeCloseTo(paneHeight / 2, 5);
  });

  it("uses the smaller scale to preserve aspect ratio", () => {
    const paneWidth = 400;
    const paneHeight = 200;
    const padding = 0;

    const t = computeFitTransform(wideBox, paneWidth, paneHeight, padding);

    // box width=200, height=100; pane 400x200 -> scaleX=2, scaleY=2
    expect(t.scale).toBeCloseTo(2, 5);
  });

  it("computeZoomToBox behaves like computeFitTransform", () => {
    const paneWidth = 500;
    const paneHeight = 300;
    const padding = 10;

    const t1 = computeFitTransform(squareBox, paneWidth, paneHeight, padding);
    const t2 = computeZoomToBox(squareBox, paneWidth, paneHeight, padding);

    expect(t2.scale).toBeCloseTo(t1.scale, 6);
    expect(t2.tx).toBeCloseTo(t1.tx, 6);
    expect(t2.ty).toBeCloseTo(t1.ty, 6);
  });

  it("handles degenerate bbox gracefully", () => {
    const pointBox: BBox = { minX: 10, minY: 20, maxX: 10, maxY: 20 };
    const t = computeFitTransform(pointBox, 400, 300, 0);

    expect(Number.isFinite(t.scale)).toBe(true);
    expect(Number.isFinite(t.tx)).toBe(true);
    expect(Number.isFinite(t.ty)).toBe(true);
  });

  it("handles zero-size pane gracefully", () => {
    const t = computeFitTransform(squareBox, 0, 0, 0);

    expect(Number.isFinite(t.scale)).toBe(true);
    expect(Number.isFinite(t.tx)).toBe(true);
    expect(Number.isFinite(t.ty)).toBe(true);
  });

  it("respects padding in small panes", () => {
    const paneWidth = 100;
    const paneHeight = 100;
    const padding = 40; // large padding relative to pane

    const t = computeFitTransform(squareBox, paneWidth, paneHeight, padding);

    // inner size = 20x20 (100 - 2*40), box size = 100x100, scale = 0.2
    expect(t.scale).toBeCloseTo(0.2, 5);
  });

  it("centers bbox in asymmetric pane", () => {
    const paneWidth = 600;
    const paneHeight = 200;
    const padding = 0;

    const t = computeFitTransform(squareBox, paneWidth, paneHeight, padding);

    // Should be limited by height: scale = 2.0
    expect(t.scale).toBeCloseTo(2.0, 5);

    // Verify centering
    const cx = (squareBox.minX + squareBox.maxX) / 2;
    const cy = (squareBox.minY + squareBox.maxY) / 2;
    const screenX = cx * t.scale + t.tx;
    const screenY = cy * t.scale + t.ty;

    expect(screenX).toBeCloseTo(paneWidth / 2, 5);
    expect(screenY).toBeCloseTo(paneHeight / 2, 5);
  });

  it("handles negative coordinate bbox", () => {
    const negBox: BBox = { minX: -50, minY: -50, maxX: 50, maxY: 50 };
    const paneWidth = 400;
    const paneHeight = 400;
    const padding = 0;

    const t = computeFitTransform(negBox, paneWidth, paneHeight, padding);

    // Box size = 100x100, pane = 400x400, scale = 4.0
    expect(t.scale).toBeCloseTo(4.0, 5);

    // Center at (0,0) should map to screen center
    const screenX = 0 * t.scale + t.tx;
    const screenY = 0 * t.scale + t.ty;

    expect(screenX).toBeCloseTo(paneWidth / 2, 5);
    expect(screenY).toBeCloseTo(paneHeight / 2, 5);
  });
});
