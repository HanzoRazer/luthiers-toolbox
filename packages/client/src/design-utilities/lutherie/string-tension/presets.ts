/**
 * String Set Presets
 *
 * The Production Shop — String Tension Calculator
 *
 * Validated presets use uwOverride values sourced from physical measurement.
 * See validationSource for citation.
 *
 * Achilles 2000 note: D'Addario EXL120 A-string factory-labeled .032"
 * but measured linear density confirmed actual gauge ~.036".
 * The corrected gauge is reflected in the EXL120 preset below.
 *
 * Conversion: µ (kg/m) → UW (lbs/in) = µ × 0.055997
 */

import type { StringSetPreset } from './types'

const KGM_TO_LBIN = 0.055997

export const PRESETS: StringSetPreset[] = [

  // ============================================================================
  // GUITAR / BASS
  // ============================================================================

  {
    id: 'g9',
    category: 'guitar',
    label: 'Guitar 9–42',
    scaleLength: 25.5,
    strings: [
      { note: 'E', octave: 4, gauge: 9,  material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'B', octave: 3, gauge: 11, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'G', octave: 3, gauge: 16, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'D', octave: 3, gauge: 24, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'A', octave: 2, gauge: 32, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'E', octave: 2, gauge: 42, material: 'nickel_wound', scaleLength: 25.5 },
    ],
  },

  {
    id: 'g10',
    category: 'guitar',
    label: 'Guitar 10–46',
    scaleLength: 25.5,
    strings: [
      { note: 'E', octave: 4, gauge: 10, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'B', octave: 3, gauge: 13, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'G', octave: 3, gauge: 17, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'D', octave: 3, gauge: 26, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'A', octave: 2, gauge: 36, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'E', octave: 2, gauge: 46, material: 'nickel_wound', scaleLength: 25.5 },
    ],
  },

  {
    id: 'ac12',
    category: 'guitar',
    label: 'Acoustic 12–54',
    scaleLength: 25.5,
    strings: [
      { note: 'E', octave: 4, gauge: 12, material: 'plain_steel',      scaleLength: 25.5 },
      { note: 'B', octave: 3, gauge: 16, material: 'plain_steel',      scaleLength: 25.5 },
      { note: 'G', octave: 3, gauge: 24, material: 'phosphor_bronze',  scaleLength: 25.5 },
      { note: 'D', octave: 3, gauge: 32, material: 'phosphor_bronze',  scaleLength: 25.5 },
      { note: 'A', octave: 2, gauge: 42, material: 'phosphor_bronze',  scaleLength: 25.5 },
      { note: 'E', octave: 2, gauge: 54, material: 'phosphor_bronze',  scaleLength: 25.5 },
    ],
  },

  {
    id: 'g7',
    category: 'guitar',
    label: '7-string 9–52',
    scaleLength: 25.5,
    strings: [
      { note: 'E', octave: 4, gauge: 9,  material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'B', octave: 3, gauge: 11, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'G', octave: 3, gauge: 16, material: 'plain_steel',  scaleLength: 25.5 },
      { note: 'D', octave: 3, gauge: 24, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'A', octave: 2, gauge: 32, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'E', octave: 2, gauge: 42, material: 'nickel_wound', scaleLength: 25.5 },
      { note: 'B', octave: 1, gauge: 52, material: 'nickel_wound', scaleLength: 25.5 },
    ],
  },

  {
    id: 'classical',
    category: 'guitar',
    label: 'Classical',
    scaleLength: 25.6,
    strings: [
      { note: 'E', octave: 4, gauge: 29, material: 'nylon_treble', scaleLength: 25.6 },
      { note: 'B', octave: 3, gauge: 33, material: 'nylon_treble', scaleLength: 25.6 },
      { note: 'G', octave: 3, gauge: 40, material: 'nylon_treble', scaleLength: 25.6 },
      { note: 'D', octave: 3, gauge: 30, material: 'nylon_wound',  scaleLength: 25.6 },
      { note: 'A', octave: 2, gauge: 34, material: 'nylon_wound',  scaleLength: 25.6 },
      { note: 'E', octave: 2, gauge: 42, material: 'nylon_wound',  scaleLength: 25.6 },
    ],
  },

  {
    id: 'b4',
    category: 'guitar',
    label: 'Bass 4 45–100',
    scaleLength: 34,
    strings: [
      { note: 'G', octave: 2, gauge: 45,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'D', octave: 2, gauge: 65,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'A', octave: 1, gauge: 80,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'E', octave: 1, gauge: 100, material: 'nickel_wound', scaleLength: 34 },
    ],
  },

  {
    id: 'b5',
    category: 'guitar',
    label: 'Bass 5 45–130',
    scaleLength: 34,
    strings: [
      { note: 'G', octave: 2, gauge: 45,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'D', octave: 2, gauge: 65,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'A', octave: 1, gauge: 80,  material: 'nickel_wound', scaleLength: 34 },
      { note: 'E', octave: 1, gauge: 100, material: 'nickel_wound', scaleLength: 34 },
      { note: 'B', octave: 0, gauge: 130, material: 'nickel_wound', scaleLength: 34 },
    ],
  },

  // ============================================================================
  // MANDOLIN / LUTE
  // ============================================================================

  {
    id: 'mandolin',
    category: 'mando',
    label: 'Mandolin',
    scaleLength: 13.875,
    note: '8 strings — 4 doubled courses',
    strings: [
      { note: 'E', octave: 5, gauge: 11, material: 'plain_steel',  scaleLength: 13.875 },
      { note: 'E', octave: 5, gauge: 11, material: 'plain_steel',  scaleLength: 13.875 },
      { note: 'A', octave: 4, gauge: 15, material: 'plain_steel',  scaleLength: 13.875 },
      { note: 'A', octave: 4, gauge: 15, material: 'plain_steel',  scaleLength: 13.875 },
      { note: 'D', octave: 4, gauge: 24, material: 'nickel_wound', scaleLength: 13.875 },
      { note: 'D', octave: 4, gauge: 24, material: 'nickel_wound', scaleLength: 13.875 },
      { note: 'G', octave: 3, gauge: 36, material: 'nickel_wound', scaleLength: 13.875 },
      { note: 'G', octave: 3, gauge: 36, material: 'nickel_wound', scaleLength: 13.875 },
    ],
  },

  {
    id: 'lute6',
    category: 'mando',
    label: 'Lute 6-course',
    scaleLength: 24.0,
    note: 'Empirical UW for gut/synthetic — a=440. For a=415 lower all notes by one semitone.',
    strings: [
      { note: 'G', octave: 4, gauge: 15, material: 'nylon_treble', scaleLength: 24.0, uwOverride: 6.55e-6, uwSource: 'Gut/synthetic empirical' },
      { note: 'D', octave: 4, gauge: 22, material: 'nylon_treble', scaleLength: 24.0, uwOverride: 1.36e-5, uwSource: 'Gut/synthetic empirical' },
      { note: 'A', octave: 3, gauge: 26, material: 'nylon_treble', scaleLength: 24.0, uwOverride: 2.43e-5, uwSource: 'Gut/synthetic empirical' },
      { note: 'F', octave: 3, gauge: 28, material: 'nylon_treble', scaleLength: 24.0, uwOverride: 3.30e-5, uwSource: 'Gut/synthetic empirical' },
      { note: 'C', octave: 3, gauge: 35, material: 'nylon_wound',  scaleLength: 24.0, uwOverride: 5.89e-5, uwSource: 'Gut/synthetic empirical' },
      { note: 'G', octave: 2, gauge: 42, material: 'nylon_wound',  scaleLength: 24.0, uwOverride: 1.22e-4, uwSource: 'Gut/synthetic empirical' },
    ],
  },

  // ============================================================================
  // UKE / BANJO
  // ============================================================================

  {
    id: 'uke_concert',
    category: 'uke',
    label: 'Uke concert',
    scaleLength: 15.0,
    strings: [
      { note: 'G', octave: 4, gauge: 28, material: 'nylon_treble', scaleLength: 15.0 },
      { note: 'C', octave: 4, gauge: 34, material: 'nylon_treble', scaleLength: 15.0 },
      { note: 'E', octave: 4, gauge: 26, material: 'nylon_treble', scaleLength: 15.0 },
      { note: 'A', octave: 4, gauge: 22, material: 'nylon_treble', scaleLength: 15.0 },
    ],
  },

  {
    id: 'uke_tenor',
    category: 'uke',
    label: 'Uke tenor',
    scaleLength: 17.0,
    strings: [
      { note: 'G', octave: 3, gauge: 28, material: 'nylon_treble', scaleLength: 17.0 },
      { note: 'C', octave: 4, gauge: 34, material: 'nylon_treble', scaleLength: 17.0 },
      { note: 'E', octave: 4, gauge: 26, material: 'nylon_treble', scaleLength: 17.0 },
      { note: 'A', octave: 4, gauge: 22, material: 'nylon_treble', scaleLength: 17.0 },
    ],
  },

  {
    id: 'banjo5',
    category: 'uke',
    label: 'Banjo 5-string',
    scaleLength: 26.25,
    multiScale: true,
    note: 'S1 (drone) uses 22" scale — starts at 5th fret peg',
    strings: [
      { note: 'G', octave: 4, gauge: 9,  material: 'plain_steel',  scaleLength: 22.0 },
      { note: 'D', octave: 4, gauge: 10, material: 'plain_steel',  scaleLength: 26.25 },
      { note: 'G', octave: 3, gauge: 13, material: 'plain_steel',  scaleLength: 26.25 },
      { note: 'B', octave: 3, gauge: 17, material: 'plain_steel',  scaleLength: 26.25 },
      { note: 'D', octave: 3, gauge: 22, material: 'nickel_wound', scaleLength: 26.25 },
    ],
  },

  // ============================================================================
  // FOLK
  // ============================================================================

  {
    id: 'dulcimer_dad',
    category: 'folk',
    label: 'Dulcimer DAD',
    scaleLength: 27.0,
    note: 'Appalachian dulcimer, DAD tuning. Empirical UW — long scale at low tension.',
    strings: [
      { note: 'D', octave: 4, gauge: 12, material: 'plain_steel',  scaleLength: 27.0, uwOverride: 3.66e-5, uwSource: 'Dulcimer empirical' },
      { note: 'D', octave: 4, gauge: 12, material: 'plain_steel',  scaleLength: 27.0, uwOverride: 3.66e-5, uwSource: 'Dulcimer empirical' },
      { note: 'A', octave: 3, gauge: 13, material: 'plain_steel',  scaleLength: 27.0, uwOverride: 4.30e-5, uwSource: 'Dulcimer empirical' },
      { note: 'D', octave: 3, gauge: 22, material: 'nickel_wound', scaleLength: 27.0, uwOverride: 1.60e-4, uwSource: 'Dulcimer empirical' },
    ],
  },

  // ============================================================================
  // ORCHESTRAL
  // ============================================================================

  {
    id: 'violin',
    category: 'orch',
    label: 'Violin',
    scaleLength: 13.0,
    note: 'UW calibrated to Thomastik-Infeld Dominant medium tension',
    strings: [
      { note: 'G', octave: 3, gauge: 32, material: 'nickel_wound', scaleLength: 13.0, uwOverride: 1.34e-4, uwSource: 'T-I Dominant medium' },
      { note: 'D', octave: 4, gauge: 28, material: 'nickel_wound', scaleLength: 13.0, uwOverride: 5.63e-5, uwSource: 'T-I Dominant medium' },
      { note: 'A', octave: 4, gauge: 22, material: 'nickel_wound', scaleLength: 13.0, uwOverride: 3.10e-5, uwSource: 'T-I Dominant medium' },
      { note: 'E', octave: 5, gauge: 10, material: 'plain_steel',  scaleLength: 13.0, uwOverride: 1.84e-5, uwSource: 'T-I Dominant medium' },
    ],
  },

  {
    id: 'viola',
    category: 'orch',
    label: 'Viola',
    scaleLength: 14.5,
    note: 'UW calibrated to Thomastik-Infeld Dominant medium tension',
    strings: [
      { note: 'C', octave: 3, gauge: 44, material: 'nickel_wound', scaleLength: 14.5, uwOverride: 3.49e-4, uwSource: 'T-I Dominant medium' },
      { note: 'G', octave: 3, gauge: 34, material: 'nickel_wound', scaleLength: 14.5, uwOverride: 1.55e-4, uwSource: 'T-I Dominant medium' },
      { note: 'D', octave: 4, gauge: 28, material: 'nickel_wound', scaleLength: 14.5, uwOverride: 6.39e-5, uwSource: 'T-I Dominant medium' },
      { note: 'A', octave: 4, gauge: 22, material: 'nickel_wound', scaleLength: 14.5, uwOverride: 3.09e-5, uwSource: 'T-I Dominant medium' },
    ],
  },

  {
    id: 'cello',
    category: 'orch',
    label: 'Cello',
    scaleLength: 27.5,
    note: 'UW calibrated to Thomastik-Infeld Dominant medium tension',
    strings: [
      { note: 'C', octave: 2, gauge: 80, material: 'nickel_wound', scaleLength: 27.5, uwOverride: 6.57e-4, uwSource: 'T-I Dominant medium' },
      { note: 'G', octave: 2, gauge: 64, material: 'nickel_wound', scaleLength: 27.5, uwOverride: 2.79e-4, uwSource: 'T-I Dominant medium' },
      { note: 'D', octave: 3, gauge: 48, material: 'nickel_wound', scaleLength: 27.5, uwOverride: 1.18e-4, uwSource: 'T-I Dominant medium' },
      { note: 'A', octave: 3, gauge: 36, material: 'nickel_wound', scaleLength: 27.5, uwOverride: 5.80e-5, uwSource: 'T-I Dominant medium' },
    ],
  },

  // ============================================================================
  // VALIDATED — Achilles 2000 measured µ values
  // ============================================================================

  {
    id: 'val_f250l',
    category: 'validated',
    label: 'Fender 250L (9–42)',
    scaleLength: 25.5,
    validated: true,
    validationSource: 'Achilles 2000 — Physics 398 EMI, UIUC',
    refTensionsN: [56.40, 48.86, 66.61, 58.55, 71.11, 65.90],
    strings: [
      { note: 'E', octave: 4, gauge: 9,  material: 'plain_steel',  scaleLength: 25.5, uwOverride: 3.09e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'B', octave: 3, gauge: 11, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 4.77e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'G', octave: 3, gauge: 16, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 1.03e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'D', octave: 3, gauge: 24, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 1.62e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'A', octave: 2, gauge: 32, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 3.50e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'E', octave: 2, gauge: 42, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 5.78e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
    ],
  },

  {
    id: 'val_exl120',
    category: 'validated',
    label: "D'Addario EXL120 (9–42*)",
    scaleLength: 25.5,
    validated: true,
    validationSource: 'Achilles 2000 — Physics 398 EMI, UIUC',
    note: "A-string factory-labeled .032\" — measured density confirmed actual gauge ~.036\"",
    refTensionsN: [59.93, 48.87, 67.35, 69.06, 86.61, 67.29],
    strings: [
      { note: 'E', octave: 4, gauge: 9,  material: 'plain_steel',  scaleLength: 25.5, uwOverride: 3.29e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'B', octave: 3, gauge: 11, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 4.78e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'G', octave: 3, gauge: 16, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 1.04e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'D', octave: 3, gauge: 24, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 1.91e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'A', octave: 2, gauge: 36, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 4.27e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ (actual .036")' },
      { note: 'E', octave: 2, gauge: 42, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 5.90e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
    ],
  },

  {
    id: 'val_exl110',
    category: 'validated',
    label: "D'Addario EXL110 (10–46)",
    scaleLength: 25.5,
    validated: true,
    validationSource: 'Achilles 2000 — Physics 398 EMI, UIUC',
    refTensionsN: [70.87, 68.15, 73.62, 80.77, 85.57, 77.41],
    strings: [
      { note: 'E', octave: 4, gauge: 10, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 3.89e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'B', octave: 3, gauge: 13, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 6.66e-4 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'G', octave: 3, gauge: 17, material: 'plain_steel',  scaleLength: 25.5, uwOverride: 1.14e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'D', octave: 3, gauge: 26, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 2.23e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'A', octave: 2, gauge: 36, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 4.21e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
      { note: 'E', octave: 2, gauge: 46, material: 'nickel_wound', scaleLength: 25.5, uwOverride: 6.79e-3 * KGM_TO_LBIN, uwSource: 'Achilles 2000 measured µ' },
    ],
  },
]
