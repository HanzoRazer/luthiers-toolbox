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

// Default export for CommonJS compatibility
export default {
  domeCalc,
  sweepRadii,
  compareBackSpans,
  formatResultLine,
  buildBackRadiusSummary
};
