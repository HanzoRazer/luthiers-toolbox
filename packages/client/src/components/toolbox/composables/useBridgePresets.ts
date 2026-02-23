/**
 * useBridgePresets - Preset management for Bridge Calculator
 */
import { ref } from "vue";

export type FamilyPreset = {
  id: string;
  label: string;
  scale_in: number;
  spread_mm: number;
  Ct_mm: number;
  Cb_mm: number;
  slotWidth_mm: number;
  slotLen_mm: number;
};

export type SimplePreset = {
  id: string;
  label: string;
  deltaTreble_mm: number;
  deltaBass_mm: number;
};

export const FAMILY_PRESETS: FamilyPreset[] = [
  { id: "lp", label: "Les Paul (24.75\")", scale_in: 24.75, spread_mm: 52.0, Ct_mm: 1.5, Cb_mm: 3.0, slotWidth_mm: 3.0, slotLen_mm: 75 },
  { id: "strat", label: "Strat/Tele (25.5\")", scale_in: 25.5, spread_mm: 52.5, Ct_mm: 2.0, Cb_mm: 3.5, slotWidth_mm: 3.0, slotLen_mm: 75 },
  { id: "om", label: "OM Acoustic (25.4\")", scale_in: 25.4, spread_mm: 54.0, Ct_mm: 2.0, Cb_mm: 4.2, slotWidth_mm: 3.2, slotLen_mm: 80 },
  { id: "dread", label: "Dread (25.4\")", scale_in: 25.4, spread_mm: 54.0, Ct_mm: 2.0, Cb_mm: 4.5, slotWidth_mm: 3.2, slotLen_mm: 80 },
  { id: "arch", label: "Archtop (25.0\")", scale_in: 25.0, spread_mm: 52.0, Ct_mm: 1.8, Cb_mm: 3.2, slotWidth_mm: 3.0, slotLen_mm: 75 },
];

export const GAUGE_PRESETS: SimplePreset[] = [
  { id: "light", label: "Light Gauge", deltaTreble_mm: -0.3, deltaBass_mm: -0.3 },
  { id: "medium", label: "Medium Gauge", deltaTreble_mm: 0.0, deltaBass_mm: 0.0 },
  { id: "heavy", label: "Heavy Gauge", deltaTreble_mm: +0.3, deltaBass_mm: +0.4 },
];

export const ACTION_PRESETS: SimplePreset[] = [
  { id: "low", label: "Low Action", deltaTreble_mm: -0.2, deltaBass_mm: -0.2 },
  { id: "standard", label: "Standard Action", deltaTreble_mm: 0.0, deltaBass_mm: 0.0 },
  { id: "high", label: "High Action", deltaTreble_mm: +0.3, deltaBass_mm: +0.4 },
];

export function useBridgePresets() {
  const presetFamily = ref<string>("strat");
  const gaugePresetId = ref<string>("medium");
  const actionPresetId = ref<string>("standard");

  function getFamily(id: string): FamilyPreset | undefined {
    return FAMILY_PRESETS.find(p => p.id === id);
  }

  function getGauge(id: string): SimplePreset | undefined {
    return GAUGE_PRESETS.find(g => g.id === id);
  }

  function getAction(id: string): SimplePreset | undefined {
    return ACTION_PRESETS.find(a => a.id === id);
  }

  return {
    presetFamily,
    gaugePresetId,
    actionPresetId,
    familyPresets: FAMILY_PRESETS,
    gaugePresets: GAUGE_PRESETS,
    actionPresets: ACTION_PRESETS,
    getFamily,
    getGauge,
    getAction,
  };
}
