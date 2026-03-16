<script setup lang="ts">
/**
 * PanelsLayer — Consolidated floating panels for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Contains all floating analysis panels (Annotations, Compare, Audio, Tool Legend, etc.)
 */

import { ref } from 'vue';
import { FloatingPanel, PanelContainer } from './index';
import ToolpathStats from '../ToolpathStats.vue';
import ToolpathFilter from '../ToolpathFilter.vue';
import ToolpathAnnotations from '../ToolpathAnnotations.vue';
import ToolpathComparePanel from '../ToolpathComparePanel.vue';
import ToolpathAudioPanel from '../ToolpathAudioPanel.vue';
import ToolLegendPanel from '../ToolLegendPanel.vue';
import FeedAnalysisPanel from '../FeedAnalysisPanel.vue';
import StockSimulationPanel from '../StockSimulationPanel.vue';
import ChipLoadPanel from '../ChipLoadPanel.vue';
import type { PanelVisibility } from './useToolpathPanelState';
import type { ToolpathEventHandlersState } from './useToolpathEventHandlers';

// Use generic segment type to avoid import conflicts
type Segment = {
  type: string;
  from_pos: [number, number, number];
  to_pos: [number, number, number];
  feed: number;
  duration_ms: number;
  line_number: number;
  line_text: string;
  tool_number?: number;
  spindle_rpm?: number;
  spindle_on?: boolean;
};

type Bounds = {
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
  z_min: number;
  z_max: number;
};

interface Props {
  panels: PanelVisibility;
  segments: Segment[];
  segmentCount: number;
  sourceGcode: string | null;
  currentSegmentIndex: number;
  toolPosition: [number, number, number];
  currentLineNumber: number | null;
  toolDiameter: number;
  bounds: Bounds | null;
  eventHandlers: ToolpathEventHandlersState;
}

const props = defineProps<Props>();

// Local ref for filter panel
const filterPanelRef = ref<InstanceType<typeof ToolpathFilter> | null>(null);

defineExpose({ filterPanelRef });
</script>

<template>
  <!-- Statistics Panel -->
  <PanelContainer
    v-if="props.panels.stats.value && props.segmentCount > 0"
    title="📊 Toolpath Statistics"
    accent="blue"
    position="top-left"
    @close="props.panels.stats.value = false"
  >
    <ToolpathStats :segments="(props.segments as any)" />
  </PanelContainer>

  <!-- Filter Panel -->
  <PanelContainer
    v-if="props.panels.filter.value && props.segmentCount > 0"
    title="🔍 Segment Filter"
    accent="orange"
    position="top-right"
    width="340px"
    :z-index="13"
    @close="props.panels.filter.value = false"
  >
    <template #actions>
      <button
        v-if="filterPanelRef?.hasActiveFilter"
        class="action-btn"
        @click="filterPanelRef?.resetFilter()"
      >
        Reset
      </button>
    </template>
    <ToolpathFilter
      ref="filterPanelRef"
      :segments="(props.segments as any)"
    />
  </PanelContainer>

  <!-- Annotations Panel -->
  <FloatingPanel
    v-if="props.panels.annotations.value && props.segmentCount > 0"
    position="top-right"
    :z-index="14"
    accent="#4a90d9"
  >
    <ToolpathAnnotations
      :current-segment="props.currentSegmentIndex"
      :current-position="props.toolPosition"
      :current-line-number="props.currentLineNumber"
      @close="props.panels.annotations.value = false"
      @goto="props.eventHandlers.handleAnnotationGoto"
    />
  </FloatingPanel>

  <!-- Compare Panel -->
  <FloatingPanel
    v-if="props.panels.compare.value && props.segmentCount > 0"
    position="top-left"
    width="360px"
    :z-index="15"
    accent="#9b59b6"
  >
    <ToolpathComparePanel
      :base-segments="(props.segments as any)"
      :base-gcode="props.sourceGcode ?? undefined"
      @close="props.panels.compare.value = false"
      @compare-segments="props.eventHandlers.handleCompareSegments"
      @overlay-toggle="props.eventHandlers.handleCompareOverlayToggle"
    />
  </FloatingPanel>

  <!-- Audio Panel -->
  <FloatingPanel
    v-if="props.panels.audio.value && props.segmentCount > 0"
    position="top-right"
    :z-index="15"
    accent="#e9a840"
  >
    <ToolpathAudioPanel
      @close="props.panels.audio.value = false"
    />
  </FloatingPanel>

  <!-- Tool Legend Panel -->
  <FloatingPanel
    v-if="props.panels.toolLegend.value && props.segmentCount > 0"
    position="top-left"
    width="280px"
    :z-index="15"
    accent="#4a90d9"
  >
    <ToolLegendPanel
      :segments="(props.segments as any)"
      :current-segment-index="props.currentSegmentIndex"
      @tool-select="props.eventHandlers.handleToolSelect"
      @tool-change-click="props.eventHandlers.handleToolChangeClick"
      @close="props.panels.toolLegend.value = false"
    />
  </FloatingPanel>

  <!-- Feed Analysis Panel -->
  <FloatingPanel
    v-if="props.panels.feedAnalysis.value && props.segmentCount > 0"
    position="top-right"
    width="360px"
    :z-index="16"
    accent="#f39c12"
  >
    <FeedAnalysisPanel
      :segments="(props.segments as any)"
      :tool-diameter="props.toolDiameter"
      @hint-click="props.eventHandlers.handleFeedHintClick"
      @close="props.panels.feedAnalysis.value = false"
    />
  </FloatingPanel>

  <!-- Stock Simulation Panel -->
  <FloatingPanel
    v-if="props.panels.stockSimulation.value && props.segmentCount > 0 && props.bounds"
    position="top-left"
    :z-index="17"
    accent="#8B4513"
  >
    <StockSimulationPanel
      :segments="(props.segments as any)"
      :current-segment-index="props.currentSegmentIndex"
      :bounds="(props.bounds as any)"
      :tool-diameter="props.toolDiameter"
      @close="props.panels.stockSimulation.value = false"
    />
  </FloatingPanel>

  <!-- Chip Load Panel -->
  <FloatingPanel
    v-if="props.panels.chipLoad.value && props.segmentCount > 0"
    position="top-right"
    width="340px"
    :z-index="18"
    accent="#f39c12"
  >
    <ChipLoadPanel
      :segments="(props.segments as any)"
      :tool-diameter="props.toolDiameter"
      :flute-count="2"
      :default-rpm="18000"
      @issue-click="props.eventHandlers.handleChipLoadIssueClick"
      @close="props.panels.chipLoad.value = false"
    />
  </FloatingPanel>
</template>

<style scoped>
.action-btn {
  padding: 2px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.action-btn:hover {
  background: #33334a;
  color: #fff;
}
</style>
