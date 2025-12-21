/**
 * Generator Types - Bundle 31.0.5
 */

import type { RosetteParamSpec } from "./rosette";

export type GeneratorDescriptor = {
  generator_key: string;
  name: string;
  description: string;
  param_hints: Record<string, any>;
};

export type GeneratorListResponse = {
  generators: GeneratorDescriptor[];
};

export type GeneratorGenerateRequest = {
  outer_diameter_mm: number;
  inner_diameter_mm: number;
  params: Record<string, any>;
};

export type GeneratorGenerateResponse = {
  spec: RosetteParamSpec;
  generator_key: string;
  warnings: string[];
};
