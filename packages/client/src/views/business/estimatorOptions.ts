/**
 * Dropdown options for Engineering Estimator
 * Extracted from EngineeringEstimatorView.vue for maintainability
 */
import type {
  InstrumentType,
  BuilderExperience,
  BodyComplexity,
  BindingComplexity,
  NeckComplexity,
  FretboardInlay,
  FinishType,
  RosetteComplexity,
} from "@/types/businessEstimator";

export const instrumentTypes: { value: InstrumentType; label: string }[] = [
  { value: "acoustic_dreadnought", label: "Acoustic Dreadnought" },
  { value: "acoustic_om", label: "Acoustic OM" },
  { value: "acoustic_parlor", label: "Acoustic Parlor" },
  { value: "classical", label: "Classical" },
  { value: "electric_solid", label: "Electric Solid Body" },
  { value: "electric_hollow", label: "Electric Hollow Body" },
  { value: "electric_semi_hollow", label: "Electric Semi-Hollow" },
];

export const experienceLevels: { value: BuilderExperience; label: string }[] = [
  { value: "beginner", label: "Beginner (1.5x)" },
  { value: "intermediate", label: "Intermediate (1.2x)" },
  { value: "experienced", label: "Experienced (1.0x)" },
  { value: "master", label: "Master (0.85x)" },
];

export const bodyOptions: { value: BodyComplexity; label: string }[] = [
  { value: "standard", label: "Standard" },
  { value: "cutaway_soft", label: "Soft Cutaway" },
  { value: "cutaway_florentine", label: "Florentine Cutaway" },
  { value: "cutaway_venetian", label: "Venetian Cutaway" },
  { value: "arm_bevel", label: "Arm Bevel" },
  { value: "tummy_cut", label: "Tummy Cut" },
  { value: "carved_top", label: "Carved Top" },
];

export const bindingOptions: { value: BindingComplexity; label: string }[] = [
  { value: "none", label: "None" },
  { value: "single", label: "Single" },
  { value: "multiple", label: "Multi-ply" },
  { value: "herringbone", label: "Herringbone" },
];

export const neckOptions: { value: NeckComplexity; label: string }[] = [
  { value: "standard", label: "Standard" },
  { value: "volute", label: "Volute" },
  { value: "scarf_joint", label: "Scarf Joint" },
  { value: "multi_scale", label: "Multi-Scale" },
];

export const inlayOptions: { value: FretboardInlay; label: string }[] = [
  { value: "none", label: "None" },
  { value: "dots", label: "Dots" },
  { value: "blocks", label: "Blocks" },
  { value: "trapezoids", label: "Trapezoids" },
  { value: "custom", label: "Custom" },
];

export const finishOptions: { value: FinishType; label: string }[] = [
  { value: "oil", label: "Oil (0.5x)" },
  { value: "wax", label: "Wax (0.45x)" },
  { value: "shellac_wipe", label: "Shellac Wipe" },
  { value: "shellac_french_polish", label: "French Polish (2.2x)" },
  { value: "nitro_solid", label: "Nitro Solid (1.0x)" },
  { value: "nitro_burst", label: "Nitro Burst (1.45x)" },
  { value: "poly_solid", label: "Poly Solid (0.75x)" },
];

export const rosetteOptions: { value: RosetteComplexity; label: string }[] = [
  { value: "none", label: "None" },
  { value: "simple_rings", label: "Simple Rings" },
  { value: "mosaic", label: "Mosaic" },
  { value: "custom_art", label: "Custom Art" },
];
