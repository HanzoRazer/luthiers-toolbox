/**
 * Toolpath Player Subcomponents
 *
 * Extracted from ToolpathPlayer.vue (3038 LOC) for maintainability.
 * Use these components to compose the player or import individually.
 */

// Phase 2 components
export { default as PlaybackControlsBar } from './PlaybackControlsBar.vue';
export { default as ToolbarButtonGroup } from './ToolbarButtonGroup.vue';
export { default as PlayerHudBar } from './PlayerHudBar.vue';
export { default as ExportAnimationPanel } from './ExportAnimationPanel.vue';

// Phase 3 components
export { default as CollisionPanel } from './CollisionPanel.vue';
export { default as OptimizationPanel } from './OptimizationPanel.vue';
export { default as GcodeSourcePanel } from './GcodeSourcePanel.vue';
export { default as KeyboardShortcutsOverlay } from './KeyboardShortcutsOverlay.vue';
export { default as MeasurementsPanel } from './MeasurementsPanel.vue';
export { default as MeasureModeIndicator } from './MeasureModeIndicator.vue';

// Phase 4 components
export { default as PanelContainer } from './PanelContainer.vue';

// Phase 5 components
export { default as LoadingOverlay } from './LoadingOverlay.vue';

// Phase 6 components
export { default as ValidationOverlay } from './ValidationOverlay.vue';
export { default as FloatingPanel } from './FloatingPanel.vue';
export { default as EmptyState } from './EmptyState.vue';

// Phase 7 components
export { default as ResolutionSlider } from './ResolutionSlider.vue';

// Phase 8 components
export { default as ControlsBarWrapper } from './ControlsBarWrapper.vue';

// Composables
export { useToolpathPanels } from './useToolpathPanels';
export type { PanelState } from './useToolpathPanels';
export { useToolpathAnalysis } from './useToolpathAnalysis';
export type { ToolpathAnalysisState, AnalysisConfig, ToolpathBounds } from './useToolpathAnalysis';
export { useToolpathExport } from './useToolpathExport';
export type { ToolpathExportState } from './useToolpathExport';
export { useToolpathAudio } from './useToolpathAudio';
export type { ToolpathAudioState, AudioSyncConfig } from './useToolpathAudio';
export { useToolpathNavigation } from './useToolpathNavigation';
export type { ToolpathNavigationState, NavigationConfig } from './useToolpathNavigation';
export { useToolpathPanelState } from './useToolpathPanelState';
export type { PanelVisibility, ToolpathPanelState } from './useToolpathPanelState';
export { useToolpathViewControls } from './useToolpathViewControls';
export type { Canvas3DRef, ViewControlsConfig, ToolpathViewControlsState } from './useToolpathViewControls';
export { useToolpathLoader } from './useToolpathLoader';
export type { LoaderConfig, ToolpathLoaderState } from './useToolpathLoader';
export { useToolpathEventHandlers } from './useToolpathEventHandlers';
export type { EventHandlersConfig, ToolpathEventHandlersState } from './useToolpathEventHandlers';
