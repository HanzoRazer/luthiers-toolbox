<script setup lang="ts">
/**
 * EstimatorAnalyticsDashboard - Analytics and insights from estimate history
 *
 * Features:
 * - Cost trends over time
 * - Instrument type distribution
 * - Hours breakdown by category
 * - Key metrics summary
 */
import { ref, computed, onMounted } from "vue";
import type { EstimateRequest, EstimateResult } from "@/types/businessEstimator";

// ============================================================================
// TYPES
// ============================================================================

interface HistoryEntry {
  id: string;
  request: EstimateRequest;
  result: EstimateResult;
  createdAt: string;
}

interface TrendPoint {
  date: string;
  avgCost: number;
  avgHours: number;
  count: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = "ltb:estimator:history:v1";

// ============================================================================
// STATE
// ============================================================================

const history = ref<HistoryEntry[]>([]);
const timeRange = ref<"7d" | "30d" | "90d" | "all">("30d");

// ============================================================================
// COMPUTED - Core Metrics
// ============================================================================

const filteredHistory = computed(() => {
  if (timeRange.value === "all") return history.value;

  const now = Date.now();
  const days = timeRange.value === "7d" ? 7 : timeRange.value === "30d" ? 30 : 90;
  const cutoff = now - days * 24 * 60 * 60 * 1000;

  return history.value.filter((e) => new Date(e.createdAt).getTime() >= cutoff);
});

const totalEstimates = computed(() => filteredHistory.value.length);

const avgCost = computed(() => {
  if (filteredHistory.value.length === 0) return 0;
  const sum = filteredHistory.value.reduce((acc, e) => acc + e.result.total_cost_per_unit, 0);
  return sum / filteredHistory.value.length;
});

const avgHours = computed(() => {
  if (filteredHistory.value.length === 0) return 0;
  const sum = filteredHistory.value.reduce((acc, e) => acc + e.result.total_hours, 0);
  return sum / filteredHistory.value.length;
});

const avgComplexity = computed(() => {
  if (filteredHistory.value.length === 0) return 0;
  const sum = filteredHistory.value.reduce(
    (acc, e) => acc + e.result.total_complexity_multiplier,
    0
  );
  return sum / filteredHistory.value.length;
});

// ============================================================================
// COMPUTED - Instrument Distribution
// ============================================================================

const instrumentDistribution = computed(() => {
  const counts: Record<string, number> = {};
  filteredHistory.value.forEach((e) => {
    const type = e.request.instrument_type;
    counts[type] = (counts[type] || 0) + 1;
  });

  const total = filteredHistory.value.length || 1;
  return Object.entries(counts)
    .map(([type, count]) => ({
      type,
      count,
      pct: (count / total) * 100,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
});

// ============================================================================
// COMPUTED - Cost Breakdown
// ============================================================================

const costBreakdown = computed(() => {
  if (filteredHistory.value.length === 0) {
    return { labor: 0, materials: 0, laborPct: 50, materialsPct: 50 };
  }

  const totalLabor = filteredHistory.value.reduce(
    (acc, e) => acc + e.result.labor_cost_per_unit,
    0
  );
  const totalMaterials = filteredHistory.value.reduce(
    (acc, e) => acc + e.result.material_cost_per_unit,
    0
  );
  const total = totalLabor + totalMaterials || 1;

  return {
    labor: totalLabor / filteredHistory.value.length,
    materials: totalMaterials / filteredHistory.value.length,
    laborPct: (totalLabor / total) * 100,
    materialsPct: (totalMaterials / total) * 100,
  };
});

// ============================================================================
// COMPUTED - Trends (weekly aggregation)
// ============================================================================

const trendData = computed((): TrendPoint[] => {
  if (filteredHistory.value.length === 0) return [];

  // Group by week
  const weeks: Record<string, { costs: number[]; hours: number[] }> = {};

  filteredHistory.value.forEach((e) => {
    const date = new Date(e.createdAt);
    // Get week start (Sunday)
    const weekStart = new Date(date);
    weekStart.setDate(date.getDate() - date.getDay());
    const key = weekStart.toISOString().slice(0, 10);

    if (!weeks[key]) weeks[key] = { costs: [], hours: [] };
    weeks[key].costs.push(e.result.total_cost_per_unit);
    weeks[key].hours.push(e.result.total_hours);
  });

  return Object.entries(weeks)
    .map(([date, data]) => ({
      date,
      avgCost: data.costs.reduce((a, b) => a + b, 0) / data.costs.length,
      avgHours: data.hours.reduce((a, b) => a + b, 0) / data.hours.length,
      count: data.costs.length,
    }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-8); // Last 8 weeks
});

const maxTrendCost = computed(() => {
  if (trendData.value.length === 0) return 1000;
  return Math.max(...trendData.value.map((t) => t.avgCost)) * 1.1;
});

// ============================================================================
// COMPUTED - Experience Distribution
// ============================================================================

const experienceDistribution = computed(() => {
  const counts: Record<string, number> = {};
  filteredHistory.value.forEach((e) => {
    const exp = e.request.builder_experience;
    counts[exp] = (counts[exp] || 0) + 1;
  });

  const total = filteredHistory.value.length || 1;
  const order = ["beginner", "intermediate", "experienced", "master"];

  return order
    .filter((exp) => counts[exp])
    .map((exp) => ({
      level: exp,
      count: counts[exp],
      pct: (counts[exp] / total) * 100,
    }));
});

// ============================================================================
// PERSISTENCE
// ============================================================================

function loadHistory(): void {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      history.value = JSON.parse(stored);
    }
  } catch (e) {
    console.warn("[EstimatorAnalyticsDashboard] Failed to load history:", e);
    history.value = [];
  }
}

// ============================================================================
// FORMATTERS
// ============================================================================

function formatCurrency(value: number): string {
  return `$${value.toFixed(0)}`;
}

function formatInstrumentType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatExperience(level: string): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  loadHistory();
});
</script>

<template>
  <div class="analytics-dashboard">
    <!-- Header -->
    <header class="dashboard-header">
      <h3>Analytics</h3>
      <div class="time-filter">
        <button
          v-for="range in (['7d', '30d', '90d', 'all'] as const)"
          :key="range"
          :class="{ active: timeRange === range }"
          @click="timeRange = range"
        >
          {{ range === 'all' ? 'All' : range }}
        </button>
      </div>
    </header>

    <!-- Empty State -->
    <div
      v-if="totalEstimates === 0"
      class="empty-state"
    >
      <p>No estimate data available for this period.</p>
      <p class="hint">
        Run some estimates to see analytics here.
      </p>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">
            {{ totalEstimates }}
          </div>
          <div class="kpi-label">
            Estimates
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">
            {{ formatCurrency(avgCost) }}
          </div>
          <div class="kpi-label">
            Avg Cost
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">
            {{ avgHours.toFixed(1) }}h
          </div>
          <div class="kpi-label">
            Avg Hours
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">
            {{ avgComplexity.toFixed(2) }}x
          </div>
          <div class="kpi-label">
            Avg Complexity
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <!-- Cost Trend -->
        <div class="chart-card">
          <h4>Cost Trend</h4>
          <div
            v-if="trendData.length > 1"
            class="trend-chart"
          >
            <div
              v-for="point in trendData"
              :key="point.date"
              class="trend-bar"
              :style="{ height: `${(point.avgCost / maxTrendCost) * 100}%` }"
              :title="`${formatDate(point.date)}: ${formatCurrency(point.avgCost)} (${point.count} estimates)`"
            >
              <span class="bar-label">{{ formatDate(point.date) }}</span>
            </div>
          </div>
          <p
            v-else
            class="chart-empty"
          >
            Need more data points
          </p>
        </div>

        <!-- Cost Breakdown -->
        <div class="chart-card">
          <h4>Cost Breakdown</h4>
          <div class="breakdown-chart">
            <div class="breakdown-bar">
              <div
                class="bar-segment labor"
                :style="{ width: `${costBreakdown.laborPct}%` }"
              />
              <div
                class="bar-segment materials"
                :style="{ width: `${costBreakdown.materialsPct}%` }"
              />
            </div>
            <div class="breakdown-legend">
              <div class="legend-item">
                <span class="legend-dot labor" />
                <span class="legend-label">Labor</span>
                <span class="legend-value">{{ formatCurrency(costBreakdown.labor) }}</span>
                <span class="legend-pct">({{ costBreakdown.laborPct.toFixed(0) }}%)</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot materials" />
                <span class="legend-label">Materials</span>
                <span class="legend-value">{{ formatCurrency(costBreakdown.materials) }}</span>
                <span class="legend-pct">({{ costBreakdown.materialsPct.toFixed(0) }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Distribution Row -->
      <div class="distribution-row">
        <!-- Instrument Types -->
        <div class="dist-card">
          <h4>Top Instruments</h4>
          <div class="dist-list">
            <div
              v-for="item in instrumentDistribution"
              :key="item.type"
              class="dist-item"
            >
              <span class="dist-name">{{ formatInstrumentType(item.type) }}</span>
              <div class="dist-bar-container">
                <div
                  class="dist-bar"
                  :style="{ width: `${item.pct}%` }"
                />
              </div>
              <span class="dist-count">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <!-- Experience Levels -->
        <div class="dist-card">
          <h4>Experience Levels</h4>
          <div class="dist-list">
            <div
              v-for="item in experienceDistribution"
              :key="item.level"
              class="dist-item"
            >
              <span class="dist-name">{{ formatExperience(item.level) }}</span>
              <div class="dist-bar-container">
                <div
                  class="dist-bar experience"
                  :style="{ width: `${item.pct}%` }"
                />
              </div>
              <span class="dist-count">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.analytics-dashboard {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.dashboard-header h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0;
}

/* Time Filter */
.time-filter {
  display: flex;
  gap: 0;
}

.time-filter button {
  padding: 4px 10px;
  font-size: 9px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: #14192a;
  border: 1px solid #1e2438;
  color: #506090;
  cursor: pointer;
  transition: all 0.15s;
}

.time-filter button:first-child {
  border-radius: 3px 0 0 3px;
}

.time-filter button:last-child {
  border-radius: 0 3px 3px 0;
}

.time-filter button:not(:first-child) {
  border-left: none;
}

.time-filter button.active {
  background: #1e2438;
  color: #f0c060;
  border-color: #4060c0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: #506090;
}

.empty-state p {
  margin: 0;
  font-size: 12px;
}

.empty-state .hint {
  font-size: 11px;
  color: #404870;
  margin-top: 8px;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.kpi-card {
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 12px;
  text-align: center;
}

.kpi-value {
  font-size: 18px;
  font-weight: 700;
  color: #60e0a0;
}

.kpi-label {
  font-size: 9px;
  color: #506090;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 4px;
}

/* Charts Row */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-card {
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 12px;
}

.chart-card h4 {
  font-size: 9px;
  letter-spacing: 1px;
  color: #6080b0;
  text-transform: uppercase;
  margin: 0 0 12px;
}

.chart-empty {
  font-size: 11px;
  color: #404870;
  text-align: center;
  padding: 20px;
  margin: 0;
}

/* Trend Chart */
.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 80px;
}

.trend-bar {
  flex: 1;
  background: linear-gradient(to top, #2050a0, #4080f0);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  position: relative;
  cursor: default;
}

.trend-bar .bar-label {
  position: absolute;
  bottom: -16px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 7px;
  color: #404870;
  white-space: nowrap;
}

/* Cost Breakdown */
.breakdown-chart {
  padding: 8px 0;
}

.breakdown-bar {
  display: flex;
  height: 24px;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 12px;
}

.bar-segment {
  transition: width 0.3s;
}

.bar-segment.labor {
  background: linear-gradient(90deg, #2050a0, #4080f0);
}

.bar-segment.materials {
  background: linear-gradient(90deg, #206060, #40a0a0);
}

.breakdown-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.labor {
  background: #4080f0;
}

.legend-dot.materials {
  background: #40a0a0;
}

.legend-label {
  color: #8090b0;
  width: 60px;
}

.legend-value {
  color: #c0c8e0;
  font-weight: 600;
}

.legend-pct {
  color: #506090;
  font-size: 9px;
}

/* Distribution Row */
.distribution-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.dist-card {
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 12px;
}

.dist-card h4 {
  font-size: 9px;
  letter-spacing: 1px;
  color: #6080b0;
  text-transform: uppercase;
  margin: 0 0 12px;
}

.dist-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dist-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dist-name {
  font-size: 10px;
  color: #8090b0;
  width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dist-bar-container {
  flex: 1;
  height: 8px;
  background: #0d1020;
  border-radius: 2px;
  overflow: hidden;
}

.dist-bar {
  height: 100%;
  background: linear-gradient(90deg, #f0c060, #f0a040);
  border-radius: 2px;
  transition: width 0.3s;
}

.dist-bar.experience {
  background: linear-gradient(90deg, #60a0e0, #4080c0);
}

.dist-count {
  font-size: 10px;
  color: #c0c8e0;
  font-weight: 600;
  width: 24px;
  text-align: right;
}
</style>
