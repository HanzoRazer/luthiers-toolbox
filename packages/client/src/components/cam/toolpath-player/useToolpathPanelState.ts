/**
 * useToolpathPanelState — Consolidated panel visibility state for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Manages all panel toggle states in a single composable.
 */

import { ref, type Ref } from 'vue';

export interface PanelVisibility {
  // P5 panels
  gcode: Ref<boolean>;
  heatmap: Ref<boolean>;
  measurements: Ref<boolean>;
  stats: Ref<boolean>;
  filter: Ref<boolean>;
  annotations: Ref<boolean>;
  compare: Ref<boolean>;
  audio: Ref<boolean>;
  // P6 panels
  toolLegend: Ref<boolean>;
  feedAnalysis: Ref<boolean>;
  stockSimulation: Ref<boolean>;
  chipLoad: Ref<boolean>;
}

export interface ToolpathPanelState {
  panels: PanelVisibility;
  // Convenience toggles
  togglePanel: (panel: keyof PanelVisibility) => void;
  closeAllPanels: () => void;
  // Compare overlay (separate from panel visibility)
  showCompareOverlay: Ref<boolean>;
}

export function useToolpathPanelState(): ToolpathPanelState {
  // P5 panels
  const gcode = ref(false);
  const heatmap = ref(false);
  const measurements = ref(true); // Default open when measurements exist
  const stats = ref(false);
  const filter = ref(false);
  const annotations = ref(false);
  const compare = ref(false);
  const audio = ref(false);

  // P6 panels
  const toolLegend = ref(false);
  const feedAnalysis = ref(false);
  const stockSimulation = ref(false);
  const chipLoad = ref(false);

  // Compare overlay state
  const showCompareOverlay = ref(false);

  const panels: PanelVisibility = {
    gcode,
    heatmap,
    measurements,
    stats,
    filter,
    annotations,
    compare,
    audio,
    toolLegend,
    feedAnalysis,
    stockSimulation,
    chipLoad,
  };

  function togglePanel(panel: keyof PanelVisibility): void {
    panels[panel].value = !panels[panel].value;
  }

  function closeAllPanels(): void {
    Object.values(panels).forEach((p) => {
      p.value = false;
    });
    showCompareOverlay.value = false;
  }

  return {
    panels,
    togglePanel,
    closeAllPanels,
    showCompareOverlay,
  };
}
