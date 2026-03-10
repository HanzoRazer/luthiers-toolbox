<script setup lang="ts">
/**
 * ChipLoadPanel — P6 Step 16: Chip Load Analysis with S-code Tracking
 *
 * Displays real-time chip load analysis:
 * - Health score gauge (0-100)
 * - Per-segment chip load values
 * - RPM tracking from S-codes
 * - Issue identification and recommendations
 * - Material-specific optimal ranges
 */

import { ref, computed, watch } from "vue";
import type { MoveSegment } from "@/sdk/endpoints/cam";
import {
  ChipLoadAnalyzer,
  type ChipLoadReport,
  type ChipLoadIssue,
  type MaterialType,
  MATERIAL_CHIP_LOADS,
} from "@/util/chipLoadAnalyzer";

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  segments: MoveSegment[];
  toolDiameter?: number;
  fluteCount?: number;
  defaultRpm?: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "issue-click", issue: ChipLoadIssue): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const selectedMaterial = ref<MaterialType>("softwood");
const report = ref<ChipLoadReport | null>(null);
const showAllIssues = ref(false);
const issueFilter = ref<"all" | "critical" | "warning">("all");

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const materialOptions = computed(() => {
  return Object.entries(MATERIAL_CHIP_LOADS).map(([key, data]) => ({
    value: key as MaterialType,
    label: data.description.split(",")[0], // First material name
    range: `${data.optimal[0].toFixed(3)}–${data.optimal[1].toFixed(3)} mm`,
  }));
});

const healthColor = computed(() => {
  const score = report.value?.healthScore ?? 0;
  if (score >= 80) return "#2ecc71";
  if (score >= 60) return "#f1c40f";
  if (score >= 40) return "#e67e22";
  return "#e74c3c";
});

const healthLabel = computed(() => {
  const score = report.value?.healthScore ?? 0;
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Poor";
});

const filteredIssues = computed(() => {
  if (!report.value) return [];

  let issues = report.value.issues;

  if (issueFilter.value === "critical") {
    issues = issues.filter(i => i.severity === "critical");
  } else if (issueFilter.value === "warning") {
    issues = issues.filter(i => i.severity === "warning");
  }

  if (!showAllIssues.value) {
    issues = issues.slice(0, 5);
  }

  return issues;
});

const hasMoreIssues = computed(() => {
  if (!report.value) return false;
  return report.value.issues.length > 5 && !showAllIssues.value;
});

const rpmSummary = computed(() => {
  if (!report.value || report.value.stats.uniqueRpms.length === 0) return null;

  const rpms = report.value.stats.uniqueRpms;
  const min = Math.min(...rpms);
  const max = Math.max(...rpms);

  return {
    min,
    max,
    unique: rpms.length,
    hasVariation: min !== max,
    changes: report.value.stats.rpmChanges,
  };
});

const chipLoadDistribution = computed(() => {
  if (!report.value || report.value.timeline.length === 0) return [];

  const materialData = MATERIAL_CHIP_LOADS[selectedMaterial.value];
  const [optMin, optMax] = materialData.optimal;

  const ranges = [
    { label: "Too Low", min: 0, max: optMin * 0.5, color: "#3498db", count: 0 },
    { label: "Low", min: optMin * 0.5, max: optMin, color: "#5dade2", count: 0 },
    { label: "Optimal", min: optMin, max: optMax, color: "#2ecc71", count: 0 },
    { label: "High", min: optMax, max: optMax * 1.5, color: "#f39c12", count: 0 },
    { label: "Too High", min: optMax * 1.5, max: Infinity, color: "#e74c3c", count: 0 },
  ];

  for (const point of report.value.timeline) {
    if (point.chipLoad <= 0) continue;
    for (const range of ranges) {
      if (point.chipLoad >= range.min && point.chipLoad < range.max) {
        range.count++;
        break;
      }
    }
  }

  const total = ranges.reduce((sum, r) => sum + r.count, 0);
  return ranges.map(r => ({
    ...r,
    percent: total > 0 ? (r.count / total) * 100 : 0,
  }));
});

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------

function analyzeChipLoad(): void {
  const materialData = MATERIAL_CHIP_LOADS[selectedMaterial.value];

  const analyzer = new ChipLoadAnalyzer({
    toolDiameter: props.toolDiameter ?? 6,
    fluteCount: props.fluteCount ?? 2,
    defaultRpm: props.defaultRpm ?? 18000,
    materialType: selectedMaterial.value,
    optimalRange: materialData.optimal,
  });

  report.value = analyzer.analyze(props.segments);
}

function handleIssueClick(issue: ChipLoadIssue): void {
  emit("issue-click", issue);
}

function getSeverityIcon(severity: ChipLoadIssue["severity"]): string {
  switch (severity) {
    case "critical": return "🔥";
    case "warning": return "⚠️";
    case "info": return "ℹ️";
    default: return "✅";
  }
}

function getSeverityColor(severity: ChipLoadIssue["severity"]): string {
  switch (severity) {
    case "critical": return "#e74c3c";
    case "warning": return "#f39c12";
    case "info": return "#3498db";
    default: return "#2ecc71";
  }
}

// ---------------------------------------------------------------------------
// Watchers
// ---------------------------------------------------------------------------

watch(
  [() => props.segments, () => selectedMaterial.value],
  () => {
    if (props.segments.length > 0) {
      analyzeChipLoad();
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="chip-load-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-title">
        <span class="icon">⚙️</span>
        <span>Chip Load Analysis</span>
      </div>
      <button class="close-btn" @click="emit('close')">&times;</button>
    </div>

    <!-- Material Selector -->
    <div class="material-section">
      <label class="material-label">Material:</label>
      <select v-model="selectedMaterial" class="material-select">
        <option
          v-for="opt in materialOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }} ({{ opt.range }})
        </option>
      </select>
    </div>

    <!-- Health Score -->
    <div v-if="report" class="health-section">
      <div class="health-gauge">
        <svg viewBox="0 0 120 70" class="gauge-svg">
          <!-- Background arc -->
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            stroke="#2a2a4a"
            stroke-width="12"
            stroke-linecap="round"
          />
          <!-- Value arc -->
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            :stroke="healthColor"
            stroke-width="12"
            stroke-linecap="round"
            :stroke-dasharray="`${(report.healthScore / 100) * 157} 157`"
          />
        </svg>
        <div class="health-value">
          <span class="score">{{ report.healthScore }}</span>
          <span class="label">{{ healthLabel }}</span>
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div v-if="report" class="stats-grid">
      <div class="stat-item">
        <span class="stat-label">Avg Chip Load</span>
        <span class="stat-value">{{ report.stats.avgChipLoad.toFixed(4) }} mm</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Min / Max</span>
        <span class="stat-value">
          {{ report.stats.minChipLoad.toFixed(4) }} / {{ report.stats.maxChipLoad.toFixed(4) }}
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Optimal Time</span>
        <span class="stat-value optimal">{{ report.stats.timeInOptimalPct.toFixed(1) }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Points Analyzed</span>
        <span class="stat-value">{{ report.timeline.length }}</span>
      </div>
    </div>

    <!-- RPM Summary -->
    <div v-if="rpmSummary" class="rpm-section">
      <div class="rpm-header">
        <span class="icon">🔄</span>
        <span>Spindle RPM (S-codes)</span>
      </div>
      <div class="rpm-info">
        <span v-if="rpmSummary.hasVariation">
          Range: {{ rpmSummary.min.toLocaleString() }} – {{ rpmSummary.max.toLocaleString() }} RPM
          ({{ rpmSummary.unique }} settings, {{ rpmSummary.changes }} changes)
        </span>
        <span v-else>
          Constant: {{ rpmSummary.min.toLocaleString() }} RPM
        </span>
      </div>
    </div>

    <!-- Distribution -->
    <div v-if="chipLoadDistribution.length > 0" class="distribution-section">
      <div class="dist-header">Distribution</div>
      <div class="dist-bars">
        <div
          v-for="range in chipLoadDistribution"
          :key="range.label"
          class="dist-bar-wrapper"
        >
          <div class="dist-label">{{ range.label }}</div>
          <div class="dist-bar-bg">
            <div
              class="dist-bar-fill"
              :style="{
                width: `${range.percent}%`,
                backgroundColor: range.color
              }"
            />
          </div>
          <div class="dist-percent">{{ range.percent.toFixed(0) }}%</div>
        </div>
      </div>
    </div>

    <!-- Issues -->
    <div v-if="report && report.issues.length > 0" class="issues-section">
      <div class="issues-header">
        <span>Issues ({{ report.issues.length }})</span>
        <div class="issue-filters">
          <button
            class="filter-btn"
            :class="{ active: issueFilter === 'all' }"
            @click="issueFilter = 'all'"
          >
            All
          </button>
          <button
            class="filter-btn"
            :class="{ active: issueFilter === 'critical' }"
            @click="issueFilter = 'critical'"
          >
            Critical
          </button>
          <button
            class="filter-btn"
            :class="{ active: issueFilter === 'warning' }"
            @click="issueFilter = 'warning'"
          >
            Warning
          </button>
        </div>
      </div>

      <div class="issues-list">
        <div
          v-for="(issue, idx) in filteredIssues"
          :key="idx"
          class="issue-item"
          @click="handleIssueClick(issue)"
        >
          <span class="issue-icon">{{ getSeverityIcon(issue.severity) }}</span>
          <div class="issue-content">
            <div class="issue-main">
              <span class="issue-segment">Seg {{ issue.segmentRange[0] + 1 }}–{{ issue.segmentRange[1] + 1 }}</span>
              <span
                class="issue-severity"
                :style="{ color: getSeverityColor(issue.severity) }"
              >
                {{ issue.severity }}
              </span>
            </div>
            <div class="issue-message">{{ issue.message }}</div>
            <div class="issue-fix">{{ issue.suggestedFix }}</div>
          </div>
        </div>
      </div>

      <button
        v-if="hasMoreIssues"
        class="show-more-btn"
        @click="showAllIssues = true"
      >
        Show {{ report.issues.length - 5 }} more issues
      </button>
    </div>

    <!-- No Issues -->
    <div v-else-if="report" class="no-issues">
      <span class="icon">✅</span>
      <span>All chip loads within optimal range!</span>
    </div>

    <!-- Summary -->
    <div v-if="report" class="summary-section">
      <div class="summary-text">{{ report.summary }}</div>
    </div>

    <!-- Recommendations -->
    <div v-if="report && report.recommendations.length > 0" class="recommendations-section">
      <div class="rec-header">Recommendations</div>
      <ul class="rec-list">
        <li v-for="(rec, idx) in report.recommendations" :key="idx">
          {{ rec }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.chip-load-panel {
  background: #1e1e2e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-size: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #1a1a2a;
  border-bottom: 1px solid #333;
  position: sticky;
  top: 0;
  z-index: 1;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #f39c12;
}

.header-title .icon {
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
}

.close-btn:hover {
  color: #fff;
}

/* Material Selector */
.material-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.material-label {
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
}

.material-select {
  flex: 1;
  padding: 6px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ddd;
  font-size: 11px;
}

.material-select:focus {
  outline: none;
  border-color: #f39c12;
}

/* Health Score */
.health-section {
  padding: 12px;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid #2a2a4a;
}

.health-gauge {
  position: relative;
  width: 120px;
  height: 70px;
}

.gauge-svg {
  width: 100%;
  height: 100%;
}

.health-value {
  position: absolute;
  bottom: 5px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}

.health-value .score {
  font-size: 24px;
  font-weight: bold;
  color: #fff;
  display: block;
}

.health-value .label {
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 8px;
  background: #252538;
  border-radius: 4px;
}

.stat-label {
  font-size: 9px;
  color: #666;
  text-transform: uppercase;
}

.stat-value {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: #ddd;
}

.stat-value.optimal {
  color: #2ecc71;
}

/* RPM Section */
.rpm-section {
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
  background: #1a1a2a;
}

.rpm-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #888;
  margin-bottom: 4px;
}

.rpm-header .icon {
  font-size: 12px;
}

.rpm-info {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: #f39c12;
}

/* Distribution */
.distribution-section {
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.dist-header {
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.dist-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dist-bar-wrapper {
  display: grid;
  grid-template-columns: 60px 1fr 40px;
  gap: 8px;
  align-items: center;
}

.dist-label {
  font-size: 10px;
  color: #888;
}

.dist-bar-bg {
  height: 8px;
  background: #2a2a4a;
  border-radius: 4px;
  overflow: hidden;
}

.dist-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.dist-percent {
  font-size: 10px;
  color: #666;
  text-align: right;
}

/* Issues */
.issues-section {
  border-bottom: 1px solid #2a2a4a;
}

.issues-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #1a1a2a;
  font-size: 11px;
  color: #888;
}

.issue-filters {
  display: flex;
  gap: 4px;
}

.filter-btn {
  padding: 3px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  font-size: 9px;
  cursor: pointer;
  transition: all 0.15s;
}

.filter-btn:hover {
  background: #33334a;
  color: #ccc;
}

.filter-btn.active {
  background: #f39c12;
  border-color: #f39c12;
  color: #1a1a2a;
}

.issues-list {
  max-height: 150px;
  overflow-y: auto;
}

.issue-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #252538;
  cursor: pointer;
  transition: background 0.15s;
}

.issue-item:hover {
  background: #252538;
}

.issue-icon {
  font-size: 14px;
  padding-top: 2px;
}

.issue-content {
  flex: 1;
  min-width: 0;
}

.issue-main {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 2px;
}

.issue-segment {
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
  color: #888;
}

.issue-severity {
  font-size: 10px;
  text-transform: capitalize;
}

.issue-message {
  font-size: 11px;
  color: #ddd;
  margin-bottom: 2px;
}

.issue-fix {
  font-size: 10px;
  color: #666;
  font-style: italic;
}

.show-more-btn {
  width: 100%;
  padding: 8px;
  background: #252538;
  border: none;
  color: #888;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.show-more-btn:hover {
  background: #33334a;
  color: #ccc;
}

/* No Issues */
.no-issues {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 12px;
  color: #2ecc71;
  font-size: 12px;
  border-bottom: 1px solid #2a2a4a;
}

.no-issues .icon {
  font-size: 16px;
}

/* Summary */
.summary-section {
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.summary-text {
  font-size: 11px;
  color: #888;
  font-style: italic;
}

/* Recommendations */
.recommendations-section {
  padding: 10px 12px;
}

.rec-header {
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.rec-list {
  margin: 0;
  padding-left: 16px;
  font-size: 11px;
  color: #888;
  line-height: 1.5;
}

.rec-list li {
  margin-bottom: 4px;
}

.rec-list li:last-child {
  margin-bottom: 0;
}
</style>
