<script setup lang="ts">
/**
 * ControlsBarWrapper — Unified controls bar for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Composes ToolbarButtonGroup and PlaybackControlsBar with all event bindings.
 */

import ToolbarButtonGroup from './ToolbarButtonGroup.vue';
import PlaybackControlsBar from './PlaybackControlsBar.vue';
import type { MemoryInfo } from '@/stores/useToolpathPlayerStore';
import type { PanelVisibility } from './useToolpathPanelState';

type PlayState = 'idle' | 'playing' | 'paused';

interface Props {
  // View state
  enable3D: boolean;
  viewMode: '2d' | '3d';
  // Panel visibility
  panels: PanelVisibility;
  showExportPanel: boolean;
  showCompareOverlay: boolean;
  // Feature state
  isExporting: boolean;
  measureMode: boolean;
  showHelp: boolean;
  hasActiveFilter: boolean;
  hasMultipleTools: boolean;
  hasBounds: boolean;
  // Data
  segmentCount: number;
  memoryInfo: MemoryInfo;
  // Playback
  playState: PlayState;
  progress: number;
  speed: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:viewMode': [value: '2d' | '3d'];
  'update:showExportPanel': [value: boolean];
  'update:showHelp': [value: boolean];
  toggleMeasureMode: [];
  // Playback controls
  play: [];
  pause: [];
  stop: [];
  stepForward: [];
  stepBackward: [];
  seek: [progress: number];
  setSpeed: [speed: number];
}>();
</script>

<template>
  <div class="controls-bar">
    <ToolbarButtonGroup
      :enable3-d="props.enable3D"
      :view-mode="props.viewMode"
      :show-heatmap="props.panels.heatmap.value"
      :show-export-panel="props.showExportPanel"
      :is-exporting="props.isExporting"
      :measure-mode="props.measureMode"
      :show-help="props.showHelp"
      :show-stats-panel="props.panels.stats.value"
      :show-filter-panel="props.panels.filter.value"
      :has-active-filter="props.hasActiveFilter"
      :show-annotations-panel="props.panels.annotations.value"
      :show-compare-panel="props.panels.compare.value"
      :show-compare-overlay="props.showCompareOverlay"
      :show-audio-panel="props.panels.audio.value"
      :has-multiple-tools="props.hasMultipleTools"
      :show-tool-legend-panel="props.panels.toolLegend.value"
      :show-feed-analysis-panel="props.panels.feedAnalysis.value"
      :show-stock-simulation-panel="props.panels.stockSimulation.value"
      :has-bounds="props.hasBounds"
      :show-chip-load-panel="props.panels.chipLoad.value"
      :segment-count="props.segmentCount"
      :memory-info="props.memoryInfo"
      @update:view-mode="emit('update:viewMode', $event)"
      @update:show-heatmap="props.panels.heatmap.value = $event"
      @update:show-export-panel="emit('update:showExportPanel', $event)"
      @toggle-measure-mode="emit('toggleMeasureMode')"
      @update:show-help="emit('update:showHelp', $event)"
      @update:show-stats-panel="props.panels.stats.value = $event"
      @update:show-filter-panel="props.panels.filter.value = $event"
      @update:show-annotations-panel="props.panels.annotations.value = $event"
      @update:show-compare-panel="props.panels.compare.value = $event"
      @update:show-audio-panel="props.panels.audio.value = $event"
      @update:show-tool-legend-panel="props.panels.toolLegend.value = $event"
      @update:show-feed-analysis-panel="props.panels.feedAnalysis.value = $event"
      @update:show-stock-simulation-panel="props.panels.stockSimulation.value = $event"
      @update:show-chip-load-panel="props.panels.chipLoad.value = $event"
    />
    <PlaybackControlsBar
      :play-state="props.playState"
      :progress="props.progress"
      :speed="props.speed"
      :segment-count="props.segmentCount"
      @play="emit('play')"
      @pause="emit('pause')"
      @stop="emit('stop')"
      @step-forward="emit('stepForward')"
      @step-backward="emit('stepBackward')"
      @seek="emit('seek', $event)"
      @set-speed="emit('setSpeed', $event)"
    />
  </div>
</template>

<style scoped>
.controls-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  background: #13131f;
  border-top: 1px solid #2a2a4a;
  flex-shrink: 0;
}
</style>
