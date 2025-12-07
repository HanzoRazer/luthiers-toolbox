/**
 * Treble Bleed Calculator
 * Recommends capacitor and resistor values for treble bleed circuits
 */

export interface TrebleBleedResult {
  style: string;
  cap_pf: number;
  resistor_k: number | null;
  series: boolean;
  approx_fc_hz: number | null;
  note: string;
}

/**
 * Recommend treble bleed values based on pot resistance and cable capacitance
 * @param pot_ohm - Potentiometer resistance in ohms (e.g., 500000 for 500k)
 * @param cable_pf - Cable capacitance in picofarads (typically 300-700pF)
 * @param style - Circuit style: 'cap-only', 'parallel', or 'series'
 */
export function recommendTrebleBleed(
  pot_ohm: number = 500000,
  cable_pf: number = 500,
  style: 'cap-only' | 'parallel' | 'series' = 'parallel'
): TrebleBleedResult {
  const presets: Record<string, { cap_pf: number; res_k: number | null; series: boolean; note: string }> = {
    'cap-only': {
      cap_pf: 820,
      res_k: null,
      series: false,
      note: 'Bright; may sound glassy'
    },
    'parallel': {
      cap_pf: 820,
      res_k: 150,
      series: false,
      note: 'Balanced; common'
    },
    'series': {
      cap_pf: 1000,
      res_k: 150,
      series: true,
      note: 'Natural taper on many HBs'
    }
  };

  const preset = presets[style] || presets['cap-only'];
  const cap_f = (preset.cap_pf || 0) * 1e-12;
  const effR = preset.series ? pot_ohm : pot_ohm / 3;
  const f_c = cap_f ? 1 / (2 * Math.PI * effR * cap_f) : null;

  return {
    style,
    cap_pf: preset.cap_pf,
    resistor_k: preset.res_k,
    series: preset.series,
    approx_fc_hz: f_c,
    note: preset.note
  };
}
