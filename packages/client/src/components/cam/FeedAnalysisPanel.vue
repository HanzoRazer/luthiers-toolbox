<script setup lang="ts">
/**
 * FeedAnalysisPanel — P6 Step 14: Feed Rate Analysis Display
 *
 * Shows detailed feed rate analysis:
 * - Efficiency score gauge
 * - Feed statistics (min/max/avg/median)
 * - Feed distribution breakdown
 * - Optimization hints with severity
 * - Feed timeline sparkline
 */

import { computed, ref } from "vue";
import type { MoveSegment } from "@/sdk/endpoints/cam";
import {
  FeedOptimizer,
  type FeedAnalysisReport,
  type FeedHint,
  type FeedBracket,
} from "@/util/feedOptimizer";

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  segments: MoveSegment[];
  toolDiameter?: number;
  spindleRpm?: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "hint-click", hint: FeedHint): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const showDetails = ref(true);
const selectedCategory = ref<string | null>(null);

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const analyzer = computed(() => new FeedOptimizer({
  toolDiameter: props.toolDiameter ?? 6,
  spindleRpm: props.spindleRpm ?? 18000,
}));

const report = computed<FeedAnalysisReport>(() =>
  analyzer.value.analyze(props.segments)
);

const filteredHints = computed(() => {
  if (!selectedCategory.value) return report.value.hints;
  return report.value.hints.filter(h => h.category === selectedCategory.value);
});

const categoryStats = computed(() => {
  const cats = new Map<string, number>();
  for (const hint of report.value.hints) {
    cats.set(hint.category, (cats.get(hint.category) ?? 0) + 1);
  }
  return Array.from(cats.entries()).map(([cat, count]) => ({ category: cat, count }));
});

const scoreColor = computed(() => {
  const score = report.value.efficiencyScore;
  if (score >= 80) return "#2ecc71";
  if (score >= 60) return "#f1c40f";
  if (score >= 40) return "#e67e22";
  return "#e74c3c";
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTime(ms: number): string {
  if (Math.abs(ms) < 1000) return `${Math.round(ms)}ms`;
  const secs = ms / 1000;
  if (Math.abs(secs) < 60) return `${secs.toFixed(1)}s`;
  const mins = Math.floor(Math.abs(secs) / 60);
  const s = Math.round(Math.abs(secs) % 60);
  const sign = ms < 0 ? "-" : "";
  return `${sign}${mins}m ${s}s`;
}

function severityIcon(severity: string): string {
  switch (severity) {
    case "critical": return "🛑";
    case "warning": return "⚠️";
    case "opportunity": return "💡";
    default: return "ℹ️";
  }
}

function categoryLabel(cat: string): string {
  const labels: Record<string, string> = {
    variation: "Feed Variation",
    conservative: "Conservative Feed",
    aggressive: "Aggressive Feed",
    plunge: "Plunge Rate",
    consistency: "Consistency",
    transition: "Transitions",
    idle: "Idle Feed",
  };
  return labels[cat] ?? cat;
}

function bracketColor(bracket: FeedBracket): string {
  switch (bracket.label) {
    case "Very Slow": return "#e74c3c";
    case "Slow": return "#e67e22";
    case "Medium": return "#f1c40f";
    case "Fast": return "#2ecc71";
    case "Very Fast": return "#3498db";
    default: return "#888";
  }
}

function handleHintClick(hint: FeedHint): void {
  emit("hint-click", hint);
}
</script>

<template>
  <div class="feed-analysis-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-title">
        <span class="icon">⚡</span>
        <span>Feed Analysis</span>
      </div>
      <button class="close-btn" @click="emit('close')">&times;</button>
    </div>

    <!-- Score Section -->
    <div class="score-section">
      <div class="score-gauge">
        <svg viewBox="0 0 100 60" class="gauge-svg">
          <!-- Background arc -->
          <path
            d="M 10 55 A 40 40 0 0 1 90 55"
            fill="none"
            stroke="#2a2a4a"
            stroke-width="8"
            stroke-linecap="round"
          />
          <!-- Score arc -->
          <path
            d="M 10 55 A 40 40 0 0 1 90 55"
            fill="none"
            :stroke="scoreColor"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="`${report.efficiencyScore * 1.26} 126`"
          />
        </svg>
        <div class="score-value" :style="{ color: scoreColor }">
          {{ report.efficiencyScore }}
        </div>
        <div class="score-label">Efficiency</div>
      </div>

      <div class="score-summary">
        <p>{{ report.summary }}</p>
        <div v-if="report.potentialSavings > 0" class="savings-badge">
          <span class="savings-icon">⏱️</span>
          <span>{{ formatTime(report.potentialSavings) }} potential savings</span>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">Min</span>
          <span class="stat-value">F{{ report.stats.minFeed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Max</span>
          <span class="stat-value">F{{ report.stats.maxFeed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Avg</span>
          <span class="stat-value">F{{ report.stats.avgFeed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Median</span>
          <span class="stat-value">F{{ report.stats.medianFeed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Changes</span>
          <span class="stat-value">{{ report.stats.feedChanges }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">/min</span>
          <span class="stat-value">{{ report.stats.changesPerMinute }}</span>
        </div>
      </div>
    </div>

    <!-- Distribution Section -->
    <div v-if="report.stats.feedDistribution.length > 0" class="distribution-section">
      <div class="section-header" @click="showDetails = !showDetails">
        <span>Feed Distribution</span>
        <span class="toggle">{{ showDetails ? '▼' : '▶' }}</span>
      </div>

      <div v-if="showDetails" class="distribution-bars">
        <div
          v-for="bracket in report.stats.feedDistribution"
          :key="bracket.label"
          class="dist-row"
        >
          <span class="dist-label">{{ bracket.label }}</span>
          <div class="dist-bar-track">
            <div
              class="dist-bar-fill"
              :style="{
                width: `${Math.min(100, bracket.percent)}%`,
                backgroundColor: bracketColor(bracket)
              }"
            />
          </div>
          <span class="dist-percent">{{ bracket.percent }}%</span>
        </div>
      </div>
    </div>

    <!-- Category Filter -->
    <div v-if="categoryStats.length > 1" class="category-filter">
      <button
        class="cat-btn"
        :class="{ active: selectedCategory === null }"
        @click="selectedCategory = null"
      >
        All ({{ report.hints.length }})
      </button>
      <button
        v-for="cat in categoryStats"
        :key="cat.category"
        class="cat-btn"
        :class="{ active: selectedCategory === cat.category }"
        @click="selectedCategory = cat.category"
      >
        {{ categoryLabel(cat.category) }} ({{ cat.count }})
      </button>
    </div>

    <!-- Hints List -->
    <div class="hints-section">
      <div
        v-for="(hint, i) in filteredHints"
        :key="i"
        class="hint-item"
        :class="'severity-' + hint.severity"
        @click="handleHintClick(hint)"
      >
        <div class="hint-header">
          <span class="hint-icon">{{ severityIcon(hint.severity) }}</span>
          <span class="hint-message">{{ hint.message }}</span>
          <span v-if="hint.timeImpact !== 0" class="hint-impact" :class="{ positive: hint.timeImpact > 0 }">
            {{ hint.timeImpact > 0 ? '+' : '' }}{{ formatTime(hint.timeImpact) }}
          </span>
        </div>
        <p class="hint-details">{{ hint.details }}</p>
        <div v-if="hint.suggestedFeed" class="hint-suggestion">
          <span class="current">F{{ hint.currentFeed }}</span>
          <span class="arrow">→</span>
          <span class="suggested">F{{ hint.suggestedFeed }}</span>
        </div>
        <div v-if="hint.lineNumbers.length > 0" class="hint-lines">
          Lines: {{ hint.lineNumbers.slice(0, 3).join(', ') }}{{ hint.lineNumbers.length > 3 ? '...' : '' }}
        </div>
      </div>

      <div v-if="filteredHints.length === 0" class="no-hints">
        <span class="check">✓</span>
        <span>No issues found{{ selectedCategory ? ' in this category' : '' }}</span>
      </div>
    </div>

    <!-- Footer -->
    <div class="panel-footer">
      <span class="confidence-note">Confidence varies by hint. Click hints for details.</span>
    </div>
  </div>
</template>

<style scoped>
.feed-analysis-panel {
  position: relative;
  background: var(--bg-primary, #1e1e2e);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 100%;
  font-size: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #1a1a2a;
  border-bottom: 1px solid #333;
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

/* Score Section */
.score-section {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #2a2a4a;
}

.score-gauge {
  position: relative;
  width: 100px;
  height: 70px;
  flex-shrink: 0;
}

.gauge-svg {
  width: 100%;
  height: 60px;
}

.score-value {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  font-size: 24px;
  font-weight: 700;
}

.score-label {
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.score-summary {
  flex: 1;
}

.score-summary p {
  margin: 0 0 8px;
  color: #ccc;
  line-height: 1.4;
}

.savings-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid #2ecc71;
  border-radius: 4px;
  color: #2ecc71;
  font-size: 11px;
}

/* Stats Section */
.stats-section {
  padding: 12px 16px;
  border-bottom: 1px solid #2a2a4a;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.stat-value {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #4a90d9;
  font-family: "JetBrains Mono", monospace;
}

/* Distribution Section */
.distribution-section {
  border-bottom: 1px solid #2a2a4a;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-header:hover {
  background: rgba(255, 255, 255, 0.03);
}

.toggle {
  font-size: 10px;
}

.distribution-bars {
  padding: 0 16px 12px;
}

.dist-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.dist-label {
  width: 70px;
  font-size: 11px;
  color: #888;
}

.dist-bar-track {
  flex: 1;
  height: 12px;
  background: #2a2a4a;
  border-radius: 6px;
  overflow: hidden;
}

.dist-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s ease;
}

.dist-percent {
  width: 40px;
  text-align: right;
  font-size: 11px;
  color: #aaa;
  font-family: "JetBrains Mono", monospace;
}

/* Category Filter */
.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 16px;
  border-bottom: 1px solid #2a2a4a;
}

.cat-btn {
  padding: 4px 10px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.cat-btn:hover {
  background: #33334a;
  color: #ccc;
}

.cat-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

/* Hints Section */
.hints-section {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.hint-item {
  padding: 10px 16px;
  border-bottom: 1px solid #252538;
  cursor: pointer;
  transition: background 0.15s;
}

.hint-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.hint-item.severity-critical {
  border-left: 3px solid #e74c3c;
}

.hint-item.severity-warning {
  border-left: 3px solid #f39c12;
}

.hint-item.severity-opportunity {
  border-left: 3px solid #2ecc71;
}

.hint-item.severity-info {
  border-left: 3px solid #3498db;
}

.hint-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.hint-icon {
  font-size: 14px;
}

.hint-message {
  flex: 1;
  font-weight: 600;
  color: #ddd;
}

.hint-impact {
  font-size: 11px;
  font-family: "JetBrains Mono", monospace;
  color: #888;
}

.hint-impact.positive {
  color: #2ecc71;
}

.hint-details {
  margin: 4px 0 0 22px;
  color: #888;
  font-size: 11px;
  line-height: 1.4;
}

.hint-suggestion {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0 0 22px;
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
}

.hint-suggestion .current {
  color: #e74c3c;
}

.hint-suggestion .arrow {
  color: #666;
}

.hint-suggestion .suggested {
  color: #2ecc71;
}

.hint-lines {
  margin: 4px 0 0 22px;
  color: #666;
  font-size: 10px;
  font-family: "JetBrains Mono", monospace;
}

.no-hints {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px;
  color: #2ecc71;
}

.no-hints .check {
  font-size: 20px;
}

/* Footer */
.panel-footer {
  padding: 8px 16px;
  border-top: 1px solid #2a2a4a;
  background: #1a1a2a;
}

.confidence-note {
  font-size: 10px;
  color: #666;
  font-style: italic;
}

/* Scrollbar */
.hints-section::-webkit-scrollbar {
  width: 6px;
}

.hints-section::-webkit-scrollbar-track {
  background: transparent;
}

.hints-section::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.hints-section::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
