<script setup lang="ts">
/**
 * PresetColumn.vue - Single preset column for A/B comparison
 * Extracted from ArtPresetCompareAB.vue
 */

export interface PresetAggRow {
  preset_id: string;
  preset_name: string;
  lane: string;
  parent_id: string | null;
  parent_name: string | null;
  diff_summary: string | null;
  rationale: string | null;
  source: string;
  job_count: number;
  risk_count: number;
  critical_count: number;
  avg_total_length: number;
  avg_total_lines: number;
  health_color: "green" | "yellow" | "red";
  trend_direction: "up" | "down" | "flat";
  trend_delta: number;
}

const props = defineProps<{
  preset: PresetAggRow | null;
  column: "A" | "B";
  accentColor: "blue" | "purple";
}>();

const emit = defineEmits<{
  navigate: [presetId: string];
}>();

function getTrendIcon(trend?: string): string {
  switch (trend) {
    case "up":
      return "▲";
    case "down":
      return "▼";
    case "flat":
      return "→";
    default:
      return "–";
  }
}

function handleNavigate() {
  if (props.preset?.preset_id) {
    emit("navigate", props.preset.preset_id);
  }
}
</script>

<template>
  <div
    class="preset-column"
    :class="`border-${accentColor} bg-${accentColor}`"
  >
    <div class="column-header">
      <span
        class="column-label"
        :class="`text-${accentColor}`"
      >Preset {{ column }}</span>
      <span :class="`badge badge-${preset?.health_color}`">
        {{ preset?.health_color?.toUpperCase() }}
      </span>
      <span
        class="trend-icon"
        :title="`Trend: ${preset?.trend_direction}`"
      >
        {{ getTrendIcon(preset?.trend_direction) }}
      </span>
    </div>

    <h3 class="preset-name">
      {{ preset?.preset_name }}
    </h3>
    <p class="preset-id">
      ID: {{ preset?.preset_id }}
    </p>

    <!-- Lineage -->
    <div
      v-if="preset?.parent_name"
      class="lineage-card"
    >
      <p class="lineage-label">
        Parent:
      </p>
      <p class="lineage-name">
        {{ preset.parent_name }}
      </p>
      <p class="lineage-diff">
        {{ preset.diff_summary }}
      </p>
      <p class="lineage-rationale">
        {{ preset.rationale }}
      </p>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <p class="stat-label">
          Jobs
        </p>
        <p class="stat-value">
          {{ preset?.job_count }}
        </p>
      </div>
      <div class="stat-card">
        <p class="stat-label">
          Risks
        </p>
        <p class="stat-value stat-yellow">
          {{ preset?.risk_count }}
        </p>
      </div>
      <div class="stat-card">
        <p class="stat-label">
          Critical
        </p>
        <p class="stat-value stat-red">
          {{ preset?.critical_count }}
        </p>
      </div>
    </div>

    <!-- Averages -->
    <div class="averages">
      <div class="avg-row">
        <span class="avg-label">Avg Length:</span>
        <span class="avg-value">{{ preset?.avg_total_length?.toFixed(1) }} mm</span>
      </div>
      <div class="avg-row">
        <span class="avg-label">Avg Lines:</span>
        <span class="avg-value">{{ preset?.avg_total_lines }}</span>
      </div>
    </div>

    <!-- Geometry Link -->
    <button
      class="nav-button"
      :class="`bg-${accentColor}`"
      @click="handleNavigate"
    >
      View Geometry Runs →
    </button>
  </div>
</template>

<style scoped>
.preset-column {
  border-width: 2px;
  border-style: solid;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.border-blue {
  border-color: #3b82f6;
}

.border-purple {
  border-color: #8b5cf6;
}

.bg-blue {
  background-color: #eff6ff;
}

.bg-purple {
  background-color: #f5f3ff;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.column-label {
  font-size: 1.125rem;
  font-weight: 700;
}

.text-blue {
  color: #2563eb;
}

.text-purple {
  color: #7c3aed;
}

.trend-icon {
  font-size: 1.5rem;
}

.preset-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.preset-id {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 1rem 0;
}

.lineage-card {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 0.25rem;
  border: 1px solid #e5e7eb;
}

.lineage-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.lineage-name {
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0;
}

.lineage-diff {
  font-size: 0.75rem;
  color: #4b5563;
  margin: 0.25rem 0 0 0;
}

.lineage-rationale {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  margin: 0.25rem 0 0 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.stat-card {
  background: white;
  border-radius: 0.5rem;
  padding: 0.75rem;
  text-align: center;
  border: 1px solid #e5e7eb;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0 0 0.25rem 0;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.stat-yellow {
  color: #ca8a04;
}

.stat-red {
  color: #dc2626;
}

.averages {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.avg-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
}

.avg-label {
  color: #6b7280;
}

.avg-value {
  font-weight: 500;
}

.nav-button {
  margin-top: 1rem;
  width: 100%;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: filter 0.2s;
}

.nav-button:hover {
  filter: brightness(0.9);
}

.nav-button.bg-blue {
  background-color: #3b82f6;
}

.nav-button.bg-purple {
  background-color: #7c3aed;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-green {
  background-color: #d1fae5;
  color: #065f46;
}

.badge-yellow {
  background-color: #fef3c7;
  color: #92400e;
}

.badge-red {
  background-color: #fee2e2;
  color: #991b1b;
}
</style>
