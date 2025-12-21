/**
 * Preview Types - Bundle 31.0.5
 */

import type { RosetteParamSpec } from "./rosette";

export type RosettePreviewSvgRequest = {
  spec: RosetteParamSpec;
  size_px?: number;
  padding_px?: number;
};

export type RosettePreviewSvgResponse = {
  svg: string;
  size_px: number;
  view_box: string;
  warnings: string[];
  debug?: Record<string, any> | null;
};
