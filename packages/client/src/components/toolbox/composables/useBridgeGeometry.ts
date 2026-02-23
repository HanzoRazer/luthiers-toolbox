/**
 * useBridgeGeometry - Geometry calculations for Bridge Calculator
 */
import { computed, type Ref } from "vue";
import type { BridgeUIState } from "./useBridgeUnits";

export interface Point2D {
  x: number;
  y: number;
}

export function useBridgeGeometry(
  ui: BridgeUIState,
  isMM: Ref<boolean>
) {
  // Core computed values
  const scale = computed(() => ui.scale);
  const spread = computed(() => ui.spread);
  const Ct = computed(() => ui.compTreble);
  const Cb = computed(() => ui.compBass);

  // Angle calculations
  const angleRad = computed(() =>
    Math.atan((Cb.value - Ct.value) / Math.max(spread.value, 1e-6))
  );
  const angleDeg = computed(() => (angleRad.value * 180) / Math.PI);

  // Endpoints in (x,y): nut at x=0; +x towards bridge; +y towards bass side
  const treble = computed<Point2D>(() => ({
    x: scale.value + Ct.value,
    y: -spread.value / 2,
  }));
  const bass = computed<Point2D>(() => ({
    x: scale.value + Cb.value,
    y: spread.value / 2,
  }));

  // Slot polygon (rectangle around the line segment, width = slotWidth)
  const slotPoly = computed<Point2D[]>(() => {
    const x1 = treble.value.x,
      y1 = treble.value.y;
    const x2 = bass.value.x,
      y2 = bass.value.y;
    const dx = x2 - x1,
      dy = y2 - y1;
    const L = Math.hypot(dx, dy) || 1;
    const nx = -dy / L,
      ny = dx / L; // unit normal
    const half = ui.slotWidth / 2;

    // Extend visually to slotLength along the segment from midpoint
    const mx = (x1 + x2) / 2,
      my = (y1 + y2) / 2;
    const tx = dx / L,
      ty = dy / L;
    const halfLen = ui.slotLength / 2;

    const A = { x: mx - halfLen * tx + half * nx, y: my - halfLen * ty + half * ny };
    const B = { x: mx + halfLen * tx + half * nx, y: my + halfLen * ty + half * ny };
    const C = { x: mx + halfLen * tx - half * nx, y: my + halfLen * ty - half * ny };
    const D = { x: mx - halfLen * tx - half * nx, y: my - halfLen * ty - half * ny };
    return [A, B, C, D];
  });

  const slotPolygonPoints = computed(() =>
    slotPoly.value.map((p) => `${p.x},${p.y}`).join(" ")
  );

  // SVG framing (auto-fit around geometry)
  const svgPadding = 10;
  const svgW = computed(
    () =>
      Math.max(treble.value.x, bass.value.x) +
      svgPadding -
      Math.min(0, treble.value.x, bass.value.x) +
      svgPadding
  );
  const svgH = computed(() => spread.value + svgPadding * 2);
  const svgViewBox = computed(() => {
    const minX = Math.min(0, treble.value.x, bass.value.x) - svgPadding;
    const minY = -spread.value / 2 - svgPadding;
    return `${minX} ${minY} ${svgW.value} ${svgH.value}`;
  });

  // Format helper
  function fmt(n: number): string {
    return n.toFixed(2);
  }

  return {
    scale,
    spread,
    Ct,
    Cb,
    angleRad,
    angleDeg,
    treble,
    bass,
    slotPoly,
    slotPolygonPoints,
    svgW,
    svgH,
    svgViewBox,
    fmt,
  };
}
