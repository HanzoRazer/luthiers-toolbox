<script setup lang="ts">
/**
 * ToolbarButtonGroup — Toggle buttons for ToolpathPlayer panels
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Controls visibility of various analysis and tool panels.
 */
import { computed } from 'vue';

interface Props {
  // View mode
  enable3D?: boolean;
  viewMode: '2d' | '3d';
  // Panel states
  showHeatmap: boolean;
  showExportPanel: boolean;
  measureMode: boolean;
  showHelp: boolean;
  showStatsPanel: boolean;
  showFilterPanel: boolean;
  showAnnotationsPanel: boolean;
  showComparePanel: boolean;
  showCompareOverlay: boolean;
  showAudioPanel: boolean;
  showToolLegendPanel: boolean;
  showFeedAnalysisPanel: boolean;
  showStockSimulationPanel: boolean;
  showChipLoadPanel: boolean;
  // State
  segmentCount: number;
  hasMultipleTools: boolean;
  hasBounds: boolean;
  isExporting: boolean;
  hasActiveFilter: boolean;
  // Memory info
  memoryInfo: {
    segmentCount: number;
    isWarning: boolean;
    isCritical: boolean;
  };
}

const props = withDefaults(defineProps<Props>(), {
  enable3D: true,
});

const emit = defineEmits<{
  'update:viewMode': [mode: '2d' | '3d'];
  'update:showHeatmap': [value: boolean];
  'update:showExportPanel': [value: boolean];
  'toggleMeasureMode': [];
  'update:showHelp': [value: boolean];
  'update:showStatsPanel': [value: boolean];
  'update:showFilterPanel': [value: boolean];
  'update:showAnnotationsPanel': [value: boolean];
  'update:showComparePanel': [value: boolean];
  'update:showAudioPanel': [value: boolean];
  'update:showToolLegendPanel': [value: boolean];
  'update:showFeedAnalysisPanel': [value: boolean];
  'update:showStockSimulationPanel': [value: boolean];
  'update:showChipLoadPanel': [value: boolean];
}>();

const disabled = computed(() => props.segmentCount === 0);
</script>

<template>
  <div class="toolbar-buttons">
    <!-- 2D/3D toggle -->
    <div
      v-if="enable3D"
      class="view-toggle"
    >
      <button
        class="view-btn"
        :class="{ active: viewMode === '2d' }"
        title="2D View"
        @click="emit('update:viewMode', '2d')"
      >
        2D
      </button>
      <button
        class="view-btn"
        :class="{ active: viewMode === '3d' }"
        title="3D View"
        @click="emit('update:viewMode', '3d')"
      >
        3D
      </button>
    </div>

    <!-- Heatmap toggle -->
    <button
      class="tool-btn heatmap-btn"
      :class="{ active: showHeatmap }"
      title="Toggle engagement heatmap"
      @click="emit('update:showHeatmap', !showHeatmap)"
    >
      🔥
    </button>

    <!-- Export button -->
    <button
      class="tool-btn export-btn"
      :class="{ active: showExportPanel }"
      :disabled="disabled || isExporting"
      title="Export animation"
      @click="emit('update:showExportPanel', !showExportPanel)"
    >
      📹
    </button>

    <!-- Measure button -->
    <button
      class="tool-btn measure-btn"
      :class="{ active: measureMode }"
      :disabled="disabled"
      title="Measure distance (click two points)"
      @click="emit('toggleMeasureMode')"
    >
      📏
    </button>

    <!-- Keyboard shortcuts help -->
    <button
      class="tool-btn help-btn"
      :class="{ active: showHelp }"
      title="Keyboard shortcuts (?)"
      @click="emit('update:showHelp', !showHelp)"
    >
      ⌨️
    </button>

    <!-- Statistics panel toggle -->
    <button
      class="tool-btn stats-btn"
      :class="{ active: showStatsPanel }"
      :disabled="disabled"
      title="Toolpath statistics"
      @click="emit('update:showStatsPanel', !showStatsPanel)"
    >
      📊
    </button>

    <!-- Filter panel toggle -->
    <button
      class="tool-btn filter-btn"
      :class="{ active: showFilterPanel, filtering: hasActiveFilter }"
      :disabled="disabled"
      title="Filter segments"
      @click="emit('update:showFilterPanel', !showFilterPanel)"
    >
      🔍
    </button>

    <!-- Annotations panel toggle -->
    <button
      class="tool-btn annotations-btn"
      :class="{ active: showAnnotationsPanel }"
      :disabled="disabled"
      title="Annotations & bookmarks"
      @click="emit('update:showAnnotationsPanel', !showAnnotationsPanel)"
    >
      📝
    </button>

    <!-- Compare panel toggle -->
    <button
      class="tool-btn compare-btn"
      :class="{ active: showComparePanel, comparing: showCompareOverlay }"
      :disabled="disabled"
      title="Compare toolpaths"
      @click="emit('update:showComparePanel', !showComparePanel)"
    >
      🔀
    </button>

    <!-- Audio panel toggle -->
    <button
      class="tool-btn audio-btn"
      :class="{ active: showAudioPanel }"
      :disabled="disabled"
      title="Machine sounds"
      @click="emit('update:showAudioPanel', !showAudioPanel)"
    >
      🔊
    </button>

    <!-- Tool legend panel toggle (only show if multiple tools) -->
    <button
      v-if="hasMultipleTools"
      class="tool-btn tools-btn"
      :class="{ active: showToolLegendPanel }"
      :disabled="disabled"
      title="Tool legend"
      @click="emit('update:showToolLegendPanel', !showToolLegendPanel)"
    >
      🔧
    </button>

    <!-- Feed analysis panel toggle -->
    <button
      class="tool-btn feed-btn"
      :class="{ active: showFeedAnalysisPanel }"
      :disabled="disabled"
      title="Feed rate analysis"
      @click="emit('update:showFeedAnalysisPanel', !showFeedAnalysisPanel)"
    >
      ⚡
    </button>

    <!-- Stock simulation panel toggle -->
    <button
      class="tool-btn stock-btn"
      :class="{ active: showStockSimulationPanel }"
      :disabled="disabled || !hasBounds"
      title="Stock simulation"
      @click="emit('update:showStockSimulationPanel', !showStockSimulationPanel)"
    >
      🪵
    </button>

    <!-- Chip Load Analysis -->
    <button
      class="tool-btn chipload-btn"
      :class="{ active: showChipLoadPanel }"
      :disabled="disabled"
      title="Chip load analysis"
      @click="emit('update:showChipLoadPanel', !showChipLoadPanel)"
    >
      ⚙️
    </button>

    <!-- Memory badge -->
    <div
      v-if="memoryInfo.segmentCount > 0"
      class="mem-badge"
      :class="{
        warning: memoryInfo.isWarning,
        critical: memoryInfo.isCritical,
      }"
    >
      {{ memoryInfo.segmentCount.toLocaleString() }}
    </div>
  </div>
</template>

<style scoped>
.toolbar-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* View mode toggle */
.view-toggle {
  display: flex;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 4px;
}

.view-btn {
  background: #252538;
  border: none;
  color: #888;
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.view-btn:first-child {
  border-right: 1px solid #3a3a5c;
}

.view-btn:hover {
  background: #33334a;
  color: #ccc;
}

.view-btn.active {
  background: #1a3a6b;
  color: #4a90d9;
}

/* Tool buttons base */
.tool-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.tool-btn:hover:not(:disabled) {
  background: #33334a;
  color: #ccc;
}

.tool-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Button-specific active states */
.heatmap-btn:hover:not(:disabled) { color: #e67e22; }
.heatmap-btn.active {
  background: linear-gradient(135deg, #5c2a1a 0%, #5c4a1a 50%, #1a4a3a 100%);
  border-color: #e67e22;
  color: #fff;
}

.export-btn:hover:not(:disabled) { color: #e74c3c; }
.export-btn.active {
  background: #3a1a1a;
  border-color: #e74c3c;
  color: #e74c3c;
}

.measure-btn.active,
.help-btn.active,
.stats-btn.active,
.annotations-btn.active,
.audio-btn.active,
.tools-btn.active,
.feed-btn.active,
.stock-btn.active,
.chipload-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

.filter-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

.filter-btn.filtering {
  background: #1a4a3a;
  border-color: #2ecc71;
  color: #2ecc71;
}

.compare-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

.compare-btn.comparing {
  background: #4a1a6b;
  border-color: #9b59b6;
  color: #9b59b6;
}

/* Memory badge */
.mem-badge {
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 10px;
  background: #1a3a6b;
  color: #4A90D9;
  margin-left: 4px;
}

.mem-badge.warning {
  background: #5c4a1a;
  color: #f39c12;
}

.mem-badge.critical {
  background: #5c1a1a;
  color: #e74c3c;
}
</style>
