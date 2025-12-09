// compareViewportMath.ts
// B22.9: Viewport math utilities for autoscale + zoom-to-diff

export type BBox = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
};

export type PanZoomState = {
  scale: number;
  tx: number;
  ty: number;
};

/**
 * Compute a pan/zoom transform that fits the given bbox into
 * a pane of (paneWidth x paneHeight) with symmetric padding.
 *
 * World → screen mapping:
 *   x' = x * scale + tx
 *   y' = y * scale + ty
 */
export function computeFitTransform(
  bbox: BBox,
  paneWidth: number,
  paneHeight: number,
  paddingPx: number = 16
): PanZoomState {
  const width = bbox.maxX - bbox.minX || 1;
  const height = bbox.maxY - bbox.minY || 1;

  const innerWidth = Math.max(paneWidth - paddingPx * 2, 1);
  const innerHeight = Math.max(paneHeight - paddingPx * 2, 1);

  const scaleX = innerWidth / width;
  const scaleY = innerHeight / height;
  const scale = Math.min(scaleX, scaleY);

  const worldCenterX = (bbox.minX + bbox.maxX) / 2;
  const worldCenterY = (bbox.minY + bbox.minY) / 2;

  const screenCenterX = paneWidth / 2;
  const screenCenterY = paneHeight / 2;

  const tx = screenCenterX - worldCenterX * scale;
  const ty = screenCenterY - worldCenterY * scale;

  return { scale, tx, ty };
}

/**
 * Convenience: "zoom to diff box" is just "fit this bbox".
 * This is here mostly for clarity / future tweaks.
 */
export function computeZoomToBox(
  diffBox: BBox,
  paneWidth: number,
  paneHeight: number,
  paddingPx: number = 16
): PanZoomState {
  return computeFitTransform(diffBox, paneWidth, paneHeight, paddingPx);
}
