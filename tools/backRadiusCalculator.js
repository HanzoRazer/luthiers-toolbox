/**
 * Back Radius Calculator — Shell Stiffness from Dome Radius
 *
 * Theory (LUTHERIE_MATH.md §43):
 *   f_domed = f_flat × sqrt(1 + C × (L/R)²)
 *   s = L² / (8R)
 *
 * Variables:
 *   R = dome radius (m)
 *   L = effective span (m)
 *   s = sagitta (dome height)
 *   C = calibration constant (default: 10)
 *
 * Physical meaning:
 *   Tighter dome → higher membrane stiffness N
 *   Higher N → higher modal frequencies
 *   15ft back radius adds ~7% frequency increase over 559mm span (C=10)
 */

/**
 * Calculate dome properties and frequency increase factor
 * @param {number} radiusFt - Dome radius in feet
 * @param {number} spanMm - Effective span in mm
 * @param {number} C - Calibration constant (default: 10)
 * @returns {Object} - { radiusM, spanM, sagitta_mm, frequencyFactor, percentIncrease }
 */
export function domeCalc(radiusFt, spanMm, C = 10) {
  const radiusM = radiusFt * 0.3048;  // ft to m
  const spanM = spanMm / 1000;         // mm to m

  // Sagitta: s = L² / (8R)
  const sagittaM = (spanM * spanM) / (8 * radiusM);
  const sagitta_mm = sagittaM * 1000;

  // Frequency factor: sqrt(1 + C × (L/R)²)
  const LoverR = spanM / radiusM;
  const frequencyFactor = Math.sqrt(1 + C * LoverR * LoverR);
  const percentIncrease = (frequencyFactor - 1) * 100;

  return {
    radiusFt,
    radiusM,
    spanMm,
    spanM,
    sagitta_mm,
    frequencyFactor,
    percentIncrease
  };
}

/**
 * Sweep through a range of radii for a fixed span
 * @param {number} spanMm - Effective span in mm
 * @param {number[]} radiiFt - Array of radii to evaluate (feet)
 * @param {number} C - Calibration constant (default: 10)
 * @returns {Object[]} - Array of domeCalc results
 */
export function sweepRadii(spanMm, radiiFt = [10, 12, 15, 20, 25, 28, 30, 35, 40], C = 10) {
  return radiiFt.map(r => domeCalc(r, spanMm, C));
}

/**
 * Compare dome effect across different back spans (lower bout widths)
 * @param {number} radiusFt - Dome radius in feet
 * @param {Object} spans - Named spans { name: spanMm }
 * @param {number} C - Calibration constant (default: 10)
 * @returns {Object[]} - Array of results with span names
 */
export function compareBackSpans(radiusFt, spans = {
  'Classical (370mm)': 370,
  'OM/000 (400mm)': 400,
  'Dreadnought (410mm)': 410,
  'Jumbo (430mm)': 430,
  'J-200 (445mm)': 445
}, C = 10) {
  return Object.entries(spans).map(([name, spanMm]) => ({
    name,
    ...domeCalc(radiusFt, spanMm, C)
  }));
}

/**
 * Format a single result line for display
 * @param {Object} result - Result from domeCalc
 * @returns {string} - Formatted string
 */
export function formatResultLine(result) {
  const r = result.radiusFt ? `R=${result.radiusFt}ft` : '';
  const span = result.spanMm ? `L=${result.spanMm}mm` : '';
  const sag = `sag=${result.sagitta_mm.toFixed(2)}mm`;
  const freq = `+${result.percentIncrease.toFixed(1)}%`;
  const name = result.name ? `${result.name}: ` : '';
  return `${name}${r} ${span} → ${sag}, ${freq}`;
}

/**
 * Build a complete summary table for back radius design
 * @param {number} spanMm - Effective span in mm
 * @param {number[]} radiiFt - Array of radii to evaluate
 * @param {number} C - Calibration constant
 * @returns {Object} - { header, rows, recommendation }
 */
export function buildBackRadiusSummary(spanMm, radiiFt = [10, 12, 15, 20, 25, 28, 30, 35, 40], C = 10) {
  const results = sweepRadii(spanMm, radiiFt, C);

  const header = `Back Radius Analysis — Span: ${spanMm}mm, C=${C}`;

  const rows = results.map(r => ({
    radiusFt: r.radiusFt,
    sagitta_mm: r.sagitta_mm.toFixed(2),
    percentIncrease: r.percentIncrease.toFixed(1),
    formatted: formatResultLine(r)
  }));

  // Find the "sweet spot" — typically 15-20ft for guitars
  const sweetSpot = results.find(r => r.radiusFt >= 15 && r.radiusFt <= 20);
  const recommendation = sweetSpot
    ? `Typical guitar back: ${sweetSpot.radiusFt}ft radius → ${sweetSpot.sagitta_mm.toFixed(1)}mm dome, +${sweetSpot.percentIncrease.toFixed(1)}% stiffness`
    : 'No typical radius in range';

  return { header, rows, recommendation, raw: results };
}

// =============================================================================
// §44 — Longitudinal Body Radius Pairs and Wood Quality Mapping
// =============================================================================
//
// Theory (LUTHERIE_MATH.md §44):
//   Top and back are radiused independently to (R_top, R_back).
//   The §43 shell-stiffness correction applies to each plate separately.
//   The pair maps to wood quality and body size.
//
//   Design hypothesis (Ross Echols, PE #78195):
//     32ft is the hydraulic balance point from irrigation system design
//     (Hazen-Williams flow optimization). Applied to acoustic plate energy
//     distribution as an UNTESTED cross-domain hypothesis. Validation
//     requires physical measurement.
//
//   One global C is shared between top and back. C_top and C_back may
//   differ due to material and grain orientation — split deferred pending
//   physical calibration data.
// =============================================================================

/**
 * Industry and experimental radius pair reference points.
 * Values in feet. Each entry includes the wood-tier hypothesis from §44.
 */
export const INDUSTRY_RADIUS_PAIRS = [
  {
    builder: 'Martin standard',
    R_top_ft: 35,
    R_back_ft: 15,
    ratio: 35 / 15,
    woodTier: 'premium_solid',
    backBehavior: 'moderately_active',
    notes: 'Historical default — premium wood era'
  },
  {
    builder: 'Martin alternate',
    R_top_ft: 30,
    R_back_ft: 10,
    ratio: 30 / 10,
    woodTier: 'premium_solid',
    backBehavior: 'rigid_reflector',
    notes: 'Tighter top, stiffer back'
  },
  {
    builder: 'Taylor (some models)',
    R_top_ft: 40,
    R_back_ft: 10,
    ratio: 40 / 10,
    woodTier: 'premium_solid',
    backBehavior: 'rigid_reflector',
    notes: 'Flat top + stiff back, premium Sitka'
  },
  {
    builder: 'Gibson J-45',
    R_top_ft: 35,
    R_back_ft: 15,
    ratio: 35 / 15,
    woodTier: 'premium_solid',
    backBehavior: 'moderately_active',
    notes: 'Same as Martin standard'
  },
  {
    builder: 'Ross experiment A',
    R_top_ft: 32,
    R_back_ft: 8,
    ratio: 32 / 8,
    woodTier: 'laminate_or_cheap_solid',
    backBehavior: 'rigid_reflector',
    notes: 'Laminate / cheap wood target — 32ft hydraulic balance hypothesis'
  },
  {
    builder: 'Ross experiment B',
    R_top_ft: 32,
    R_back_ft: 12,
    ratio: 32 / 12,
    woodTier: 'mid_grade_solid',
    backBehavior: 'transition_zone',
    notes: 'Mid-grade solid target — back partially active'
  },
  {
    builder: 'Ross experiment C',
    R_top_ft: 32,
    R_back_ft: 16,
    ratio: 32 / 16,
    woodTier: 'premium_solid',
    backBehavior: 'passive_radiator',
    notes: 'Premium solid target — back as full passive radiator'
  }
];

/**
 * Suggest a wood-tier classification from a (R_top, R_back) pair.
 * Returns one of: 'laminate_or_cheap_solid', 'mid_grade_solid', 'premium_solid'.
 *
 * Classification is based on the back radius (which controls back behavior)
 * and the top radius (which signals construction philosophy).
 *
 * @param {number} R_top_ft  - Top plate radius in feet
 * @param {number} R_back_ft - Back plate radius in feet
 * @returns {string}         - Wood tier label
 */
export function suggestWoodTier(R_top_ft, R_back_ft) {
  // Tight back (≤10ft) → rigid reflector → laminate/cheap (unless premium top stiffness)
  if (R_back_ft <= 10) {
    if (R_top_ft >= 38) return 'premium_solid';     // Taylor 40/10 case
    return 'laminate_or_cheap_solid';
  }
  // Mid back (10-14ft) → transition zone → mid-grade solid
  if (R_back_ft <= 14) return 'mid_grade_solid';
  // Loose back (≥15ft) → passive radiator → premium solid
  return 'premium_solid';
}

/**
 * Classify back behavior from back radius alone.
 * @param {number} R_back_ft
 * @returns {string} - 'rigid_reflector' | 'transition_zone' | 'passive_radiator'
 */
export function classifyBackBehavior(R_back_ft) {
  if (R_back_ft <= 10) return 'rigid_reflector';
  if (R_back_ft <= 14) return 'transition_zone';
  return 'passive_radiator';
}

/**
 * Per-plate shell stiffness correction for a (R_top, R_back) radius pair.
 *
 * Applies §43 dome-radius correction independently to top and back.
 * One global C is used for both plates (see §44 calibration note).
 *
 * @param {number} R_top_ft  - Top plate radius in feet
 * @param {number} R_back_ft - Back plate radius in feet
 * @param {number} spanMm    - Effective span in mm (lower bout width)
 * @param {number} C         - Calibration constant (default: 10)
 * @param {Object} [opts]    - Optional { L_top_mm, L_back_mm } to override per-plate spans
 * @returns {Object} - Full pair analysis
 */
export function radiusPairCalc(R_top_ft, R_back_ft, spanMm, C = 10, opts = {}) {
  const L_top_mm = opts.L_top_mm ?? spanMm;
  const L_back_mm = opts.L_back_mm ?? spanMm;

  const top = domeCalc(R_top_ft, L_top_mm, C);
  const back = domeCalc(R_back_ft, L_back_mm, C);

  const ratio = R_top_ft / R_back_ft;
  const woodTier = suggestWoodTier(R_top_ft, R_back_ft);
  const backBehavior = classifyBackBehavior(R_back_ft);

  // Locate matching industry reference if any
  const reference = INDUSTRY_RADIUS_PAIRS.find(
    p => p.R_top_ft === R_top_ft && p.R_back_ft === R_back_ft
  ) || null;

  return {
    R_top_ft,
    R_back_ft,
    spanMm,
    C,
    ratio,
    woodTier,
    backBehavior,
    reference,
    top,
    back,
    // Convenience: relative shell-stiffening difference between plates
    topVsBackPercent: (top.percentIncrease - back.percentIncrease).toFixed(2)
  };
}

/**
 * Sweep all industry reference points for a given span.
 * Returns radiusPairCalc results for each entry in INDUSTRY_RADIUS_PAIRS.
 *
 * @param {number} spanMm - Effective span in mm
 * @param {number} C      - Calibration constant (default: 10)
 * @returns {Object[]}    - Array of pair analyses
 */
export function sweepIndustryPairs(spanMm, C = 10) {
  return INDUSTRY_RADIUS_PAIRS.map(p =>
    radiusPairCalc(p.R_top_ft, p.R_back_ft, spanMm, C)
  );
}

/**
 * Format a single pair result line for display.
 * @param {Object} pair - Result from radiusPairCalc
 * @returns {string}
 */
export function formatPairLine(pair) {
  const builder = pair.reference ? `${pair.reference.builder}: ` : '';
  const r = `R_top=${pair.R_top_ft}ft / R_back=${pair.R_back_ft}ft`;
  const ratio = `ratio=${pair.ratio.toFixed(2)}`;
  const tShift = `top +${pair.top.percentIncrease.toFixed(1)}%`;
  const bShift = `back +${pair.back.percentIncrease.toFixed(1)}%`;
  const tier = `[${pair.woodTier}]`;
  return `${builder}${r} (${ratio}) → ${tShift}, ${bShift} ${tier}`;
}

// Default export for CommonJS compatibility
export default {
  // §43
  domeCalc,
  sweepRadii,
  compareBackSpans,
  formatResultLine,
  buildBackRadiusSummary,
  // §44
  INDUSTRY_RADIUS_PAIRS,
  suggestWoodTier,
  classifyBackBehavior,
  radiusPairCalc,
  sweepIndustryPairs,
  formatPairLine
};
