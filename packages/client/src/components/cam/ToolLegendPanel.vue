<script setup lang="ts">
/**
 * ToolLegendPanel — P6 Multi-Tool Legend Display
 *
 * Shows color-coded legend for tools used in the toolpath:
 * - Tool number with color swatch
 * - Segment count, cut distance, cut time per tool
 * - Click to filter/highlight segments for that tool
 * - Tool change timeline markers
 */

import { computed, ref } from "vue";
import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";
import {
  analyzeToolUsage,
  buildToolChangeMarkers,
  formatToolNumber,
  formatToolTime,
  formatToolDistance,
  type ToolInfo,
  type ToolChangeMarker,
} from "@/util/toolpathTools";

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  segments: MoveSegment[];
  currentSegmentIndex?: number;
}>();

const emit = defineEmits<{
  (e: "tool-select", toolNumber: number | null): void;
  (e: "tool-change-click", marker: ToolChangeMarker): void;
  (e: "close"): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const selectedTool = ref<number | null>(null);
const showChanges = ref(true);

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const toolInfos = computed<ToolInfo[]>(() => analyzeToolUsage(props.segments));

const toolChangeMarkers = computed<ToolChangeMarker[]>(() =>
  buildToolChangeMarkers(props.segments)
);

const hasMultipleTools = computed(() => toolInfos.value.length > 1);

const totalCutTime = computed(() =>
  toolInfos.value.reduce((sum, t) => sum + t.cutTime, 0)
);

/** Current tool based on segment index */
const currentTool = computed<number | null>(() => {
  if (props.currentSegmentIndex === undefined || props.currentSegmentIndex < 0) {
    return null;
  }
  const seg = props.segments[props.currentSegmentIndex];
  return seg?.tool_number ?? 1;
});

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

function toggleTool(toolNum: number): void {
  if (selectedTool.value === toolNum) {
    selectedTool.value = null;
    emit("tool-select", null);
  } else {
    selectedTool.value = toolNum;
    emit("tool-select", toolNum);
  }
}

function handleChangeClick(marker: ToolChangeMarker): void {
  emit("tool-change-click", marker);
}

function clearSelection(): void {
  selectedTool.value = null;
  emit("tool-select", null);
}
</script>

<template>
  <div class="tool-legend-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3>Tools Used</h3>
      <div class="header-actions">
        <button
          v-if="selectedTool !== null"
          class="clear-btn"
          @click="clearSelection"
          title="Clear filter"
        >
          Clear
        </button>
        <button class="close-btn" @click="emit('close')" title="Close">
          &times;
        </button>
      </div>
    </div>

    <!-- Single tool message -->
    <div v-if="!hasMultipleTools" class="single-tool-msg">
      <p>Single-tool program ({{ formatToolNumber(toolInfos[0]?.number ?? 1) }})</p>
    </div>

    <!-- Tool List -->
    <div v-else class="tool-list">
      <div
        v-for="tool in toolInfos"
        :key="tool.number"
        class="tool-row"
        :class="{
          selected: selectedTool === tool.number,
          current: currentTool === tool.number,
        }"
        @click="toggleTool(tool.number)"
      >
        <div class="tool-swatch" :style="{ backgroundColor: tool.color }" />
        <div class="tool-info">
          <span class="tool-name">{{ formatToolNumber(tool.number) }}</span>
          <span class="tool-stats">
            {{ tool.segmentCount }} moves ·
            {{ formatToolDistance(tool.cutDistance) }} ·
            {{ formatToolTime(tool.cutTime) }}
          </span>
        </div>
        <div class="tool-pct">
          {{ Math.round((tool.cutTime / totalCutTime) * 100) }}%
        </div>
      </div>
    </div>

    <!-- Tool Changes Section -->
    <div v-if="toolChangeMarkers.length > 0" class="changes-section">
      <div class="section-header" @click="showChanges = !showChanges">
        <span>Tool Changes ({{ toolChangeMarkers.length }})</span>
        <span class="toggle-icon">{{ showChanges ? "▼" : "▶" }}</span>
      </div>

      <div v-if="showChanges" class="changes-list">
        <div
          v-for="(marker, i) in toolChangeMarkers"
          :key="i"
          class="change-row"
          @click="handleChangeClick(marker)"
        >
          <span class="change-line">L{{ marker.lineNumber }}</span>
          <span class="change-tools">
            <span
              class="mini-swatch"
              :style="{ backgroundColor: toolInfos.find((t) => t.number === marker.fromTool)?.color }"
            />
            {{ formatToolNumber(marker.fromTool) }}
            →
            <span
              class="mini-swatch"
              :style="{ backgroundColor: toolInfos.find((t) => t.number === marker.toTool)?.color }"
            />
            {{ formatToolNumber(marker.toTool) }}
          </span>
          <span class="change-time">{{ formatToolTime(marker.timeMs) }}</span>
        </div>
      </div>
    </div>

    <!-- Legend Footer -->
    <div class="legend-footer">
      <p>Click tool to filter view · Click change to jump</p>
    </div>
  </div>
</template>

<style scoped>
.tool-legend-panel {
  position: absolute;
  top: 0;
  left: 0;
  width: 280px;
  max-height: 100%;
  background: var(--bg-primary, #1e1e2e);
  border-right: 1px solid var(--border-color, #333);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #333);
  background: #1a1a2a;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #e9a840;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.clear-btn {
  background: rgba(233, 168, 64, 0.2);
  border: 1px solid #e9a840;
  color: #e9a840;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.clear-btn:hover {
  background: rgba(233, 168, 64, 0.3);
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.single-tool-msg {
  padding: 20px 16px;
  text-align: center;
}

.single-tool-msg p {
  margin: 0;
  color: #888;
  font-size: 13px;
}

.tool-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tool-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s ease;
  border-left: 3px solid transparent;
}

.tool-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tool-row.selected {
  background: rgba(233, 168, 64, 0.15);
  border-left-color: #e9a840;
}

.tool-row.current {
  background: rgba(46, 204, 113, 0.15);
}

.tool-row.current.selected {
  background: rgba(233, 168, 64, 0.2);
}

.tool-swatch {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
}

.tool-stats {
  display: block;
  font-size: 11px;
  color: #888;
  margin-top: 2px;
}

.tool-pct {
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
  font-family: "JetBrains Mono", monospace;
}

/* Changes Section */
.changes-section {
  border-top: 1px solid #333;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-header:hover {
  background: rgba(255, 255, 255, 0.03);
}

.toggle-icon {
  font-size: 10px;
}

.changes-list {
  max-height: 150px;
  overflow-y: auto;
}

.change-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 12px;
  color: #ccc;
  transition: background 0.15s ease;
}

.change-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.change-line {
  font-family: "JetBrains Mono", monospace;
  color: #888;
  font-size: 11px;
  min-width: 40px;
}

.change-tools {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
}

.mini-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}

.change-time {
  font-family: "JetBrains Mono", monospace;
  color: #666;
  font-size: 11px;
}

/* Footer */
.legend-footer {
  padding: 10px 16px;
  border-top: 1px solid #333;
}

.legend-footer p {
  margin: 0;
  font-size: 11px;
  color: #666;
  text-align: center;
}

/* Scrollbar */
.tool-list::-webkit-scrollbar,
.changes-list::-webkit-scrollbar {
  width: 6px;
}

.tool-list::-webkit-scrollbar-track,
.changes-list::-webkit-scrollbar-track {
  background: transparent;
}

.tool-list::-webkit-scrollbar-thumb,
.changes-list::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.tool-list::-webkit-scrollbar-thumb:hover,
.changes-list::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
