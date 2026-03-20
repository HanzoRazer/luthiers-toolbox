<script setup lang="ts">
/**
 * ToolpathStats — P5 Statistics & Analytics Panel (thin presenter).
 * Stats computation, formatters, and chart helpers: @/composables/useToolpathStats
 */

import { ref, toRef } from "vue";
import type { MoveSegment } from "@/util/toolpathAnalytics";
import {
  useToolpathStats,
  TOOLPATH_STATS_TAB_IDS,
  toolpathStatsTabLabel,
  type ToolpathStatsTabId,
} from "@/composables/useToolpathStats";

interface Props {
  segments: MoveSegment[];
}

const props = defineProps<Props>();

const activeTab = ref<ToolpathStatsTabId>("overview");

const {
  stats,
  moveTypeChartData,
  efficiencyScore,
  efficiencyGrade,
  formatDistance,
  formatFeed,
  formatPercent,
  axisBarWidthStyle,
  rapidTimePercent,
  histogramBarHeightPercent,
  layerBarInlineStyle,
} = useToolpathStats(toRef(props, "segments"));
</script>

<template>
  <div class="toolpath-stats">
    <!-- Tab Navigation -->
    <div class="stats-tabs">
      <button
        v-for="tab in TOOLPATH_STATS_TAB_IDS"
        :key="tab"
        class="stats-tab"
        :class="{ active: activeTab === tab }"
        @click="activeTab = tab"
      >
        {{ toolpathStatsTabLabel(tab) }}
      </button>
    </div>

    <!-- No Data State -->
    <div v-if="!stats" class="stats-empty">
      <span>No toolpath loaded</span>
    </div>

    <!-- Overview Tab -->
    <div v-else-if="activeTab === 'overview'" class="stats-content">
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">Segments</span>
          <span class="stat-value">{{ stats.segmentCount.toLocaleString() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">G-code Lines</span>
          <span class="stat-value">{{ stats.lineCount.toLocaleString() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Total Time</span>
          <span class="stat-value time">{{ stats.time.formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Total Distance</span>
          <span class="stat-value">{{ formatDistance(stats.distance.total) }}</span>
        </div>
      </div>

      <!-- Move Type Distribution -->
      <div class="stats-section">
        <h4 class="section-title">Move Types</h4>
        <div class="move-type-chart">
          <div
            v-for="item in moveTypeChartData"
            :key="item.label"
            class="move-type-bar"
            :style="{ width: item.percent + '%', background: item.color }"
            :title="`${item.label}: ${item.value} (${item.percent.toFixed(1)}%)`"
          />
        </div>
        <div class="move-type-legend">
          <div
            v-for="item in moveTypeChartData"
            :key="item.label"
            class="legend-item"
          >
            <span class="legend-dot" :style="{ background: item.color }" />
            <span class="legend-label">{{ item.label }}</span>
            <span class="legend-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <!-- Quick Efficiency -->
      <div class="stats-section efficiency-quick">
        <div class="efficiency-score" :style="{ borderColor: efficiencyGrade.color }">
          <span class="efficiency-grade" :style="{ color: efficiencyGrade.color }">
            {{ efficiencyGrade.grade }}
          </span>
          <span class="efficiency-label">{{ efficiencyGrade.label }}</span>
        </div>
        <div class="efficiency-bar-container">
          <div
            class="efficiency-bar"
            :style="{ width: efficiencyScore + '%', background: efficiencyGrade.color }"
          />
        </div>
        <span class="efficiency-pct">{{ efficiencyScore.toFixed(0) }}%</span>
      </div>
    </div>

    <!-- Distance Tab -->
    <div v-else-if="activeTab === 'distance'" class="stats-content">
      <div class="stats-grid cols-2">
        <div class="stat-card large">
          <span class="stat-label">Total Distance</span>
          <span class="stat-value">{{ formatDistance(stats.distance.total) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Cutting</span>
          <span class="stat-value cut">{{ formatDistance(stats.distance.cut) }}</span>
          <span class="stat-sub">{{ formatPercent(stats.distance.cut / stats.distance.total) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Rapid</span>
          <span class="stat-value rapid">{{ formatDistance(stats.distance.rapid) }}</span>
          <span class="stat-sub">{{ formatPercent(stats.distance.rapid / stats.distance.total) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Arc</span>
          <span class="stat-value arc">{{ formatDistance(stats.distance.arc) }}</span>
          <span class="stat-sub">{{ formatPercent(stats.distance.arc / stats.distance.total) }}</span>
        </div>
      </div>

      <div class="stats-section">
        <h4 class="section-title">Axis Travel</h4>
        <div class="axis-bars">
          <div class="axis-row">
            <span class="axis-label">X</span>
            <div class="axis-bar-track">
              <div
                class="axis-bar x"
                :style="axisBarWidthStyle(stats.distance.xTravel)"
              />
            </div>
            <span class="axis-value">{{ formatDistance(stats.distance.xTravel) }}</span>
          </div>
          <div class="axis-row">
            <span class="axis-label">Y</span>
            <div class="axis-bar-track">
              <div
                class="axis-bar y"
                :style="axisBarWidthStyle(stats.distance.yTravel)"
              />
            </div>
            <span class="axis-value">{{ formatDistance(stats.distance.yTravel) }}</span>
          </div>
          <div class="axis-row">
            <span class="axis-label">Z</span>
            <div class="axis-bar-track">
              <div
                class="axis-bar z"
                :style="axisBarWidthStyle(stats.distance.zTravel)"
              />
            </div>
            <span class="axis-value">{{ formatDistance(stats.distance.zTravel) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Time Tab -->
    <div v-else-if="activeTab === 'time'" class="stats-content">
      <div class="stats-grid cols-3">
        <div class="stat-card large">
          <span class="stat-label">Total Time</span>
          <span class="stat-value time">{{ stats.time.formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Cutting</span>
          <span class="stat-value cut">{{ stats.time.cutFormatted }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Rapid</span>
          <span class="stat-value rapid">{{ stats.time.rapidFormatted }}</span>
        </div>
      </div>

      <div class="stats-section">
        <h4 class="section-title">Time Distribution</h4>
        <div class="time-bar-container">
          <div class="time-bar-track">
            <div
              class="time-bar cut"
              :style="{ width: stats.time.cutPercent + '%' }"
              title="Cutting time"
            />
            <div
              class="time-bar rapid"
              :style="{ width: rapidTimePercent + '%' }"
              title="Rapid time"
            />
          </div>
          <div class="time-bar-labels">
            <span class="cut-label">Cutting {{ stats.time.cutPercent.toFixed(1) }}%</span>
            <span class="rapid-label">Rapid {{ rapidTimePercent.toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Feed Tab -->
    <div v-else-if="activeTab === 'feed'" class="stats-content">
      <div class="stats-grid cols-2">
        <div class="stat-card">
          <span class="stat-label">Min Feed</span>
          <span class="stat-value">{{ formatFeed(stats.feed.min) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Max Feed</span>
          <span class="stat-value">{{ formatFeed(stats.feed.max) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Avg Feed</span>
          <span class="stat-value">{{ formatFeed(stats.feed.avg) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Weighted Avg</span>
          <span class="stat-value">{{ formatFeed(stats.feed.weightedAvg) }}</span>
        </div>
      </div>

      <div v-if="stats.feed.histogram.length > 0" class="stats-section">
        <h4 class="section-title">Feed Rate Distribution</h4>
        <div class="feed-histogram">
          <div
            v-for="(bucket, i) in stats.feed.histogram"
            :key="i"
            class="histogram-bar-container"
          >
            <div
              class="histogram-bar"
              :style="{ height: histogramBarHeightPercent(bucket.percent) + '%' }"
              :title="`${Math.round(bucket.min)}-${Math.round(bucket.max)} mm/min: ${bucket.count} moves`"
            />
            <span class="histogram-label">{{ Math.round(bucket.min) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Z Depth Tab -->
    <div v-else-if="activeTab === 'depth'" class="stats-content">
      <div class="stats-grid cols-3">
        <div class="stat-card">
          <span class="stat-label">Z Min (Deepest)</span>
          <span class="stat-value depth">{{ stats.zDepth.min.toFixed(2) }} mm</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Z Max</span>
          <span class="stat-value">{{ stats.zDepth.max.toFixed(2) }} mm</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Z Range</span>
          <span class="stat-value">{{ stats.zDepth.range.toFixed(2) }} mm</span>
        </div>
      </div>

      <div class="stats-section">
        <h4 class="section-title">Detected Layers ({{ stats.zDepth.layerCount }})</h4>
        <div class="layers-list">
          <div
            v-for="(z, i) in stats.zDepth.layers.slice(0, 10)"
            :key="i"
            class="layer-item"
          >
            <span class="layer-num">L{{ i + 1 }}</span>
            <div class="layer-bar-track">
              <div
                class="layer-bar"
                :style="layerBarInlineStyle(z)"
              />
            </div>
            <span class="layer-value">{{ z.toFixed(2) }} mm</span>
          </div>
          <div v-if="stats.zDepth.layers.length > 10" class="layers-more">
            +{{ stats.zDepth.layers.length - 10 }} more layers...
          </div>
        </div>
      </div>
    </div>

    <!-- Efficiency Tab -->
    <div v-else-if="activeTab === 'efficiency'" class="stats-content">
      <div class="efficiency-main">
        <div class="efficiency-circle" :style="{ borderColor: efficiencyGrade.color }">
          <span class="efficiency-big-grade" :style="{ color: efficiencyGrade.color }">
            {{ efficiencyGrade.grade }}
          </span>
          <span class="efficiency-big-score">{{ efficiencyScore.toFixed(0) }}%</span>
          <span class="efficiency-big-label">{{ efficiencyGrade.label }}</span>
        </div>
      </div>

      <div class="efficiency-breakdown">
        <div class="efficiency-row">
          <span class="eff-label">Cutting Efficiency</span>
          <div class="eff-bar-track">
            <div
              class="eff-bar"
              :style="{ width: (stats.efficiency.cuttingEfficiency * 100) + '%' }"
            />
          </div>
          <span class="eff-value">{{ formatPercent(stats.efficiency.cuttingEfficiency) }}</span>
        </div>
        <div class="efficiency-row">
          <span class="eff-label">Distance Efficiency</span>
          <div class="eff-bar-track">
            <div
              class="eff-bar"
              :style="{ width: (stats.efficiency.distanceEfficiency * 100) + '%' }"
            />
          </div>
          <span class="eff-value">{{ formatPercent(stats.efficiency.distanceEfficiency) }}</span>
        </div>
        <div class="efficiency-row">
          <span class="eff-label">Feed Utilization</span>
          <div class="eff-bar-track">
            <div
              class="eff-bar"
              :style="{ width: (stats.efficiency.feedUtilization * 100) + '%' }"
            />
          </div>
          <span class="eff-value">{{ formatPercent(stats.efficiency.feedUtilization) }}</span>
        </div>
        <div class="efficiency-row">
          <span class="eff-label">Rapid Optimization</span>
          <div class="eff-bar-track">
            <div
              class="eff-bar"
              :style="{ width: (stats.efficiency.rapidScore * 100) + '%' }"
            />
          </div>
          <span class="eff-value">{{ formatPercent(stats.efficiency.rapidScore) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolpath-stats {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-size: 11px;
  color: #ccc;
}

/* ── Tabs ──────────────────────────────────────────────────────────── */
.stats-tabs {
  display: flex;
  gap: 2px;
  padding: 8px 8px 0;
  background: #13131f;
  border-bottom: 1px solid #2a2a4a;
  flex-wrap: wrap;
}

.stats-tab {
  padding: 6px 10px;
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  color: #666;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.stats-tab:hover {
  background: #252538;
  color: #aaa;
}

.stats-tab.active {
  background: #1a1a2e;
  border-color: #4a90d9;
  border-bottom-color: #1a1a2e;
  color: #4a90d9;
  margin-bottom: -1px;
}

/* ── Content ───────────────────────────────────────────────────────── */
.stats-content {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

.stats-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

/* ── Grid ──────────────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.stats-grid.cols-2 {
  grid-template-columns: repeat(2, 1fr);
}

.stats-grid.cols-3 {
  grid-template-columns: repeat(3, 1fr);
}

.stat-card {
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-card.large {
  grid-column: span 2;
}

.stat-label {
  color: #666;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.stat-value.time { color: #4a90d9; }
.stat-value.cut { color: #2ecc71; }
.stat-value.rapid { color: #e74c3c; }
.stat-value.arc { color: #9b59b6; }
.stat-value.depth { color: #e67e22; }

.stat-sub {
  font-size: 10px;
  color: #666;
}

/* ── Sections ──────────────────────────────────────────────────────── */
.stats-section {
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #888;
}

/* ── Move Type Chart ───────────────────────────────────────────────── */
.move-type-chart {
  display: flex;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 10px;
}

.move-type-bar {
  min-width: 2px;
  transition: width 0.3s ease;
}

.move-type-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-label {
  color: #888;
}

.legend-value {
  color: #fff;
  font-weight: 600;
}

/* ── Efficiency Quick ──────────────────────────────────────────────── */
.efficiency-quick {
  display: flex;
  align-items: center;
  gap: 12px;
}

.efficiency-score {
  width: 50px;
  height: 50px;
  border: 3px solid;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.efficiency-grade {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}

.efficiency-label {
  font-size: 8px;
  color: #888;
}

.efficiency-bar-container {
  flex: 1;
  height: 8px;
  background: #252538;
  border-radius: 4px;
  overflow: hidden;
}

.efficiency-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.efficiency-pct {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  min-width: 40px;
  text-align: right;
}

/* ── Axis Bars ─────────────────────────────────────────────────────── */
.axis-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.axis-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.axis-label {
  width: 16px;
  font-weight: 700;
  color: #888;
}

.axis-bar-track {
  flex: 1;
  height: 10px;
  background: #252538;
  border-radius: 5px;
  overflow: hidden;
}

.axis-bar {
  height: 100%;
  border-radius: 5px;
  transition: width 0.3s ease;
}

.axis-bar.x { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.axis-bar.y { background: linear-gradient(90deg, #2ecc71, #27ae60); }
.axis-bar.z { background: linear-gradient(90deg, #3498db, #2980b9); }

.axis-value {
  min-width: 70px;
  text-align: right;
  color: #aaa;
}

/* ── Time Bar ──────────────────────────────────────────────────────── */
.time-bar-container {
  margin-top: 8px;
}

.time-bar-track {
  display: flex;
  height: 20px;
  border-radius: 10px;
  overflow: hidden;
}

.time-bar {
  transition: width 0.3s ease;
}

.time-bar.cut { background: linear-gradient(90deg, #2ecc71, #27ae60); }
.time-bar.rapid { background: linear-gradient(90deg, #e74c3c, #c0392b); }

.time-bar-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}

.cut-label { color: #2ecc71; }
.rapid-label { color: #e74c3c; }

/* ── Feed Histogram ────────────────────────────────────────────────── */
.feed-histogram {
  display: flex;
  align-items: flex-end;
  height: 80px;
  gap: 4px;
}

.histogram-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.histogram-bar {
  width: 100%;
  background: linear-gradient(180deg, #4a90d9, #2a5a8a);
  border-radius: 3px 3px 0 0;
  min-height: 4px;
}

.histogram-label {
  font-size: 8px;
  color: #666;
  margin-top: 4px;
}

/* ── Layers ────────────────────────────────────────────────────────── */
.layers-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layer-num {
  width: 24px;
  font-size: 9px;
  font-weight: 600;
  color: #666;
}

.layer-bar-track {
  flex: 1;
  height: 8px;
  background: #252538;
  border-radius: 4px;
  overflow: hidden;
}

.layer-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.layer-value {
  min-width: 60px;
  text-align: right;
  font-size: 10px;
  color: #aaa;
}

.layers-more {
  text-align: center;
  color: #666;
  font-size: 10px;
  padding: 4px 0;
}

/* ── Efficiency Main ───────────────────────────────────────────────── */
.efficiency-main {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.efficiency-circle {
  width: 100px;
  height: 100px;
  border: 4px solid;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
}

.efficiency-big-grade {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.efficiency-big-score {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.efficiency-big-label {
  font-size: 9px;
  color: #888;
}

.efficiency-breakdown {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.efficiency-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.eff-label {
  width: 120px;
  color: #888;
  font-size: 10px;
}

.eff-bar-track {
  flex: 1;
  height: 8px;
  background: #252538;
  border-radius: 4px;
  overflow: hidden;
}

.eff-bar {
  height: 100%;
  background: linear-gradient(90deg, #4a90d9, #2ecc71);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.eff-value {
  min-width: 45px;
  text-align: right;
  font-weight: 600;
  color: #fff;
}
</style>
