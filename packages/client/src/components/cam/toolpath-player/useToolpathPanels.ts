/**
 * useToolpathPanels — Panel visibility state composable
 *
 * Extracted from ToolpathPlayer.vue to reduce component complexity.
 * Centralizes all panel toggle state and provides helpers.
 */
import { ref, computed } from 'vue';

export interface PanelState {
  // View settings
  viewMode: '2d' | '3d';
  showHeatmap: boolean;
  showMeasurementsPanel: boolean;

  // Analysis panels
  showStatsPanel: boolean;
  showFilterPanel: boolean;
  showAnnotationsPanel: boolean;
  showComparePanel: boolean;
  showCompareOverlay: boolean;
  showAudioPanel: boolean;

  // Tool panels
  showToolLegendPanel: boolean;
  showFeedAnalysisPanel: boolean;
  showStockSimulationPanel: boolean;
  showChipLoadPanel: boolean;

  // Other panels
  showGcodePanel: boolean;
  showExportPanel: boolean;
  showCollisionPanel: boolean;
  showOptPanel: boolean;
  showHelp: boolean;
}

export function useToolpathPanels(options: { default3D?: boolean } = {}) {
  // View settings
  const viewMode = ref<'2d' | '3d'>(options.default3D ? '3d' : '2d');
  const showHeatmap = ref(false);
  const showMeasurementsPanel = ref(true);

  // Analysis panels
  const showStatsPanel = ref(false);
  const showFilterPanel = ref(false);
  const showAnnotationsPanel = ref(false);
  const showComparePanel = ref(false);
  const showCompareOverlay = ref(false);
  const showAudioPanel = ref(false);

  // Tool panels
  const showToolLegendPanel = ref(false);
  const showFeedAnalysisPanel = ref(false);
  const showStockSimulationPanel = ref(false);
  const showChipLoadPanel = ref(false);

  // Other panels
  const showGcodePanel = ref(false);
  const showExportPanel = ref(false);
  const showCollisionPanel = ref(false);
  const showOptPanel = ref(false);
  const showHelp = ref(false);

  // Computed: check if any analysis panel is open
  const hasOpenAnalysisPanel = computed(() =>
    showStatsPanel.value ||
    showFilterPanel.value ||
    showAnnotationsPanel.value ||
    showComparePanel.value ||
    showAudioPanel.value
  );

  // Computed: check if any tool panel is open
  const hasOpenToolPanel = computed(() =>
    showToolLegendPanel.value ||
    showFeedAnalysisPanel.value ||
    showStockSimulationPanel.value ||
    showChipLoadPanel.value
  );

  // Close all panels
  function closeAllPanels(): void {
    showStatsPanel.value = false;
    showFilterPanel.value = false;
    showAnnotationsPanel.value = false;
    showComparePanel.value = false;
    showAudioPanel.value = false;
    showToolLegendPanel.value = false;
    showFeedAnalysisPanel.value = false;
    showStockSimulationPanel.value = false;
    showChipLoadPanel.value = false;
    showGcodePanel.value = false;
    showExportPanel.value = false;
    showCollisionPanel.value = false;
    showOptPanel.value = false;
    showHelp.value = false;
  }

  // Toggle panel (optionally closing others)
  function togglePanel(
    panelRef: ReturnType<typeof ref<boolean>>,
    closeOthers = false
  ): void {
    if (closeOthers && !panelRef.value) {
      closeAllPanels();
    }
    panelRef.value = !panelRef.value;
  }

  // Get all panel state as a flat object (for persistence)
  function getPanelState(): PanelState {
    return {
      viewMode: viewMode.value,
      showHeatmap: showHeatmap.value,
      showMeasurementsPanel: showMeasurementsPanel.value,
      showStatsPanel: showStatsPanel.value,
      showFilterPanel: showFilterPanel.value,
      showAnnotationsPanel: showAnnotationsPanel.value,
      showComparePanel: showComparePanel.value,
      showCompareOverlay: showCompareOverlay.value,
      showAudioPanel: showAudioPanel.value,
      showToolLegendPanel: showToolLegendPanel.value,
      showFeedAnalysisPanel: showFeedAnalysisPanel.value,
      showStockSimulationPanel: showStockSimulationPanel.value,
      showChipLoadPanel: showChipLoadPanel.value,
      showGcodePanel: showGcodePanel.value,
      showExportPanel: showExportPanel.value,
      showCollisionPanel: showCollisionPanel.value,
      showOptPanel: showOptPanel.value,
      showHelp: showHelp.value,
    };
  }

  // Restore panel state from a flat object
  function restorePanelState(state: Partial<PanelState>): void {
    if (state.viewMode !== undefined) viewMode.value = state.viewMode;
    if (state.showHeatmap !== undefined) showHeatmap.value = state.showHeatmap;
    if (state.showMeasurementsPanel !== undefined) showMeasurementsPanel.value = state.showMeasurementsPanel;
    if (state.showStatsPanel !== undefined) showStatsPanel.value = state.showStatsPanel;
    if (state.showFilterPanel !== undefined) showFilterPanel.value = state.showFilterPanel;
    if (state.showAnnotationsPanel !== undefined) showAnnotationsPanel.value = state.showAnnotationsPanel;
    if (state.showComparePanel !== undefined) showComparePanel.value = state.showComparePanel;
    if (state.showCompareOverlay !== undefined) showCompareOverlay.value = state.showCompareOverlay;
    if (state.showAudioPanel !== undefined) showAudioPanel.value = state.showAudioPanel;
    if (state.showToolLegendPanel !== undefined) showToolLegendPanel.value = state.showToolLegendPanel;
    if (state.showFeedAnalysisPanel !== undefined) showFeedAnalysisPanel.value = state.showFeedAnalysisPanel;
    if (state.showStockSimulationPanel !== undefined) showStockSimulationPanel.value = state.showStockSimulationPanel;
    if (state.showChipLoadPanel !== undefined) showChipLoadPanel.value = state.showChipLoadPanel;
    if (state.showGcodePanel !== undefined) showGcodePanel.value = state.showGcodePanel;
    if (state.showExportPanel !== undefined) showExportPanel.value = state.showExportPanel;
    if (state.showCollisionPanel !== undefined) showCollisionPanel.value = state.showCollisionPanel;
    if (state.showOptPanel !== undefined) showOptPanel.value = state.showOptPanel;
    if (state.showHelp !== undefined) showHelp.value = state.showHelp;
  }

  return {
    // View settings
    viewMode,
    showHeatmap,
    showMeasurementsPanel,

    // Analysis panels
    showStatsPanel,
    showFilterPanel,
    showAnnotationsPanel,
    showComparePanel,
    showCompareOverlay,
    showAudioPanel,

    // Tool panels
    showToolLegendPanel,
    showFeedAnalysisPanel,
    showStockSimulationPanel,
    showChipLoadPanel,

    // Other panels
    showGcodePanel,
    showExportPanel,
    showCollisionPanel,
    showOptPanel,
    showHelp,

    // Computed
    hasOpenAnalysisPanel,
    hasOpenToolPanel,

    // Methods
    closeAllPanels,
    togglePanel,
    getPanelState,
    restorePanelState,
  };
}
