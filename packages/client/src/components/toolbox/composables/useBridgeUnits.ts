/**
 * useBridgeUnits - Unit conversion and reactive UI state for Bridge Calculator
 */
import { computed, reactive, ref, watch } from "vue";
import type { FamilyPreset, SimplePreset } from "./useBridgePresets";
import { FAMILY_PRESETS, GAUGE_PRESETS, ACTION_PRESETS } from "./useBridgePresets";

export interface BridgeUIState {
  scale: number;
  spread: number;
  compTreble: number;
  compBass: number;
  slotWidth: number;
  slotLength: number;
}

export function useBridgeUnits() {
  const isMM = ref(true);
  const unitLabel = computed(() => (isMM.value ? "mm" : "in"));

  // Conversion helpers
  const in2mm = (x: number) => x * 25.4;
  const mm2in = (x: number) => x / 25.4;

  // Reactive UI state (in current units)
  const ui = reactive<BridgeUIState>({
    scale: in2mm(25.5), // default Strat
    spread: 52.5,
    compTreble: 2.0,
    compBass: 3.5,
    slotWidth: 3.0,
    slotLength: 75.0,
  });

  /**
   * Load a family preset and convert to current units
   */
  function applyFamilyPreset(id: string) {
    const f = FAMILY_PRESETS.find((p) => p.id === id);
    if (!f) return;

    if (isMM.value) {
      ui.scale = in2mm(f.scale_in);
      ui.spread = f.spread_mm;
      ui.compTreble = f.Ct_mm;
      ui.compBass = f.Cb_mm;
      ui.slotWidth = f.slotWidth_mm;
      ui.slotLength = f.slotLen_mm;
    } else {
      ui.scale = f.scale_in;
      ui.spread = mm2in(f.spread_mm);
      ui.compTreble = mm2in(f.Ct_mm);
      ui.compBass = mm2in(f.Cb_mm);
      ui.slotWidth = mm2in(f.slotWidth_mm);
      ui.slotLength = mm2in(f.slotLen_mm);
    }
  }

  /**
   * Apply gauge/action nudges on top of the family preset
   */
  function applyPresets(
    familyId: string,
    gaugeId: string,
    actionId: string
  ) {
    applyFamilyPreset(familyId);
    const g = GAUGE_PRESETS.find((x) => x.id === gaugeId);
    const a = ACTION_PRESETS.find((x) => x.id === actionId);
    if (!g || !a) return;

    const dT = g.deltaTreble_mm + a.deltaTreble_mm;
    const dB = g.deltaBass_mm + a.deltaBass_mm;

    if (isMM.value) {
      ui.compTreble += dT;
      ui.compBass += dB;
    } else {
      ui.compTreble += mm2in(dT);
      ui.compBass += mm2in(dB);
    }
  }

  /**
   * Watch for unit toggle and convert all fields
   */
  function setupUnitWatch() {
    watch(isMM, (newVal, oldVal) => {
      if (newVal === oldVal) return;
      if (newVal) {
        // switched to mm
        ui.scale = in2mm(ui.scale);
        ui.spread = in2mm(ui.spread);
        ui.compTreble = in2mm(ui.compTreble);
        ui.compBass = in2mm(ui.compBass);
        ui.slotWidth = in2mm(ui.slotWidth);
        ui.slotLength = in2mm(ui.slotLength);
      } else {
        // switched to inches
        ui.scale = mm2in(ui.scale);
        ui.spread = mm2in(ui.spread);
        ui.compTreble = mm2in(ui.compTreble);
        ui.compBass = mm2in(ui.compBass);
        ui.slotWidth = mm2in(ui.slotWidth);
        ui.slotLength = mm2in(ui.slotLength);
      }
    });
  }

  return {
    isMM,
    unitLabel,
    ui,
    in2mm,
    mm2in,
    applyFamilyPreset,
    applyPresets,
    setupUnitWatch,
  };
}
