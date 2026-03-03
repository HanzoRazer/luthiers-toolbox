<script setup lang="ts">
/**
 * EstimatorDiffPanel - Compare two estimates side-by-side
 *
 * Shows differences between estimate A and B:
 * - Total hours delta
 * - Cost delta
 * - WBS task changes
 * - Complexity factor delta
 */
import { computed } from "vue";
import type { EstimateResult } from "@/types/businessEstimator";

const props = defineProps<{
  before: EstimateResult;
  after: EstimateResult;
}>();

// ============================================================================
// COMPUTED
// ============================================================================

const hoursDelta = computed(() => {
  return props.after.total_hours - props.before.total_hours;
});

const costDelta = computed(() => {
  return props.after.total_cost_per_unit - props.before.total_cost_per_unit;
});

const complexityDelta = computed(() => {
  return props.after.total_complexity_multiplier - props.before.total_complexity_multiplier;
});

const laborDelta = computed(() => {
  return props.after.labor_cost_per_unit - props.before.labor_cost_per_unit;
});

const materialDelta = computed(() => {
  return props.after.material_cost_per_unit - props.before.material_cost_per_unit;
});

// Find changed WBS tasks
const changedTasks = computed(() => {
  const beforeMap = new Map(props.before.wbs_tasks.map(t => [t.task_id, t]));
  const afterMap = new Map(props.after.wbs_tasks.map(t => [t.task_id, t]));

  const changes: Array<{
    task_id: string;
    task_name: string;
    before_hours: number;
    after_hours: number;
    delta: number;
  }> = [];

  for (const [id, afterTask] of afterMap) {
    const beforeTask = beforeMap.get(id);
    if (beforeTask) {
      const delta = afterTask.adjusted_hours - beforeTask.adjusted_hours;
      if (Math.abs(delta) > 0.01) {
        changes.push({
          task_id: id,
          task_name: afterTask.task_name,
          before_hours: beforeTask.adjusted_hours,
          after_hours: afterTask.adjusted_hours,
          delta,
        });
      }
    }
  }

  return changes.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
});

// Find changed complexity factors
const changedFactors = computed(() => {
  const before = props.before.complexity_factors_applied;
  const after = props.after.complexity_factors_applied;

  const changes: Array<{
    factor: string;
    before: number;
    after: number;
    delta: number;
  }> = [];

  const allKeys = new Set([...Object.keys(before), ...Object.keys(after)]);
  for (const key of allKeys) {
    const bVal = before[key] ?? 1;
    const aVal = after[key] ?? 1;
    if (Math.abs(aVal - bVal) > 0.001) {
      changes.push({
        factor: key,
        before: bVal,
        after: aVal,
        delta: aVal - bVal,
      });
    }
  }

  return changes;
});

// ============================================================================
// HELPERS
// ============================================================================

function formatDelta(value: number, prefix = ""): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${prefix}${value.toFixed(1)}`;
}

function formatCurrency(value: number): string {
  return `$${value.toFixed(0)}`;
}

function deltaClass(value: number): string {
  if (value > 0) return "delta-up";
  if (value < 0) return "delta-down";
  return "delta-neutral";
}
</script>

<template>
  <div class="diff-panel">
    <h3 class="diff-title">
      Estimate Comparison
    </h3>

    <!-- Summary Deltas -->
    <div class="delta-grid">
      <div class="delta-item">
        <span class="delta-label">Hours</span>
        <span
          class="delta-value"
          :class="deltaClass(hoursDelta)"
        >
          {{ formatDelta(hoursDelta) }}h
        </span>
        <span class="delta-context">
          {{ before.total_hours.toFixed(1) }}h → {{ after.total_hours.toFixed(1) }}h
        </span>
      </div>

      <div class="delta-item">
        <span class="delta-label">Total Cost</span>
        <span
          class="delta-value"
          :class="deltaClass(costDelta)"
        >
          {{ formatDelta(costDelta, "$") }}
        </span>
        <span class="delta-context">
          {{ formatCurrency(before.total_cost_per_unit) }} → {{ formatCurrency(after.total_cost_per_unit) }}
        </span>
      </div>

      <div class="delta-item">
        <span class="delta-label">Labor</span>
        <span
          class="delta-value"
          :class="deltaClass(laborDelta)"
        >
          {{ formatDelta(laborDelta, "$") }}
        </span>
        <span class="delta-context">
          {{ formatCurrency(before.labor_cost_per_unit) }} → {{ formatCurrency(after.labor_cost_per_unit) }}
        </span>
      </div>

      <div class="delta-item">
        <span class="delta-label">Materials</span>
        <span
          class="delta-value"
          :class="deltaClass(materialDelta)"
        >
          {{ formatDelta(materialDelta, "$") }}
        </span>
        <span class="delta-context">
          {{ formatCurrency(before.material_cost_per_unit) }} → {{ formatCurrency(after.material_cost_per_unit) }}
        </span>
      </div>

      <div class="delta-item">
        <span class="delta-label">Complexity</span>
        <span
          class="delta-value"
          :class="deltaClass(complexityDelta)"
        >
          {{ formatDelta(complexityDelta) }}x
        </span>
        <span class="delta-context">
          {{ before.total_complexity_multiplier.toFixed(2) }}x → {{ after.total_complexity_multiplier.toFixed(2) }}x
        </span>
      </div>
    </div>

    <!-- Changed Complexity Factors -->
    <div
      v-if="changedFactors.length > 0"
      class="diff-section"
    >
      <h4>Complexity Factor Changes</h4>
      <div class="factor-list">
        <div
          v-for="f in changedFactors"
          :key="f.factor"
          class="factor-item"
        >
          <span class="factor-name">{{ f.factor }}</span>
          <span
            class="factor-change"
            :class="deltaClass(f.delta)"
          >
            {{ f.before.toFixed(2) }}x → {{ f.after.toFixed(2) }}x
          </span>
        </div>
      </div>
    </div>

    <!-- Changed WBS Tasks -->
    <div
      v-if="changedTasks.length > 0"
      class="diff-section"
    >
      <h4>WBS Task Changes</h4>
      <table class="task-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Before</th>
            <th>After</th>
            <th>Delta</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="t in changedTasks"
            :key="t.task_id"
          >
            <td class="task-name">
              {{ t.task_name }}
            </td>
            <td class="task-hours">
              {{ t.before_hours.toFixed(1) }}h
            </td>
            <td class="task-hours">
              {{ t.after_hours.toFixed(1) }}h
            </td>
            <td
              class="task-delta"
              :class="deltaClass(t.delta)"
            >
              {{ formatDelta(t.delta) }}h
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Changes -->
    <div
      v-if="changedFactors.length === 0 && changedTasks.length === 0"
      class="no-changes"
    >
      No significant differences detected.
    </div>
  </div>
</template>

<style scoped>
.diff-panel {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.diff-title {
  font-size: 11px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #1e2438;
}

/* Delta Grid */
.delta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.delta-item {
  background: #14192a;
  border-radius: 4px;
  padding: 10px;
  text-align: center;
}

.delta-label {
  display: block;
  font-size: 9px;
  letter-spacing: 1px;
  color: #506090;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.delta-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 2px;
}

.delta-context {
  display: block;
  font-size: 10px;
  color: #606888;
}

/* Delta Colors */
.delta-up {
  color: #f0a060;
}

.delta-down {
  color: #60e0a0;
}

.delta-neutral {
  color: #8090b0;
}

/* Sections */
.diff-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #1e2438;
}

.diff-section h4 {
  font-size: 10px;
  letter-spacing: 1px;
  color: #6080b0;
  text-transform: uppercase;
  margin: 0 0 10px;
}

/* Factor List */
.factor-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.factor-item {
  background: #14192a;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
}

.factor-name {
  color: #8090b0;
  margin-right: 8px;
}

.factor-change {
  font-weight: 600;
}

/* Task Table */
.task-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.task-table th {
  text-align: left;
  font-size: 9px;
  letter-spacing: 1px;
  color: #506090;
  text-transform: uppercase;
  padding: 6px 8px;
  border-bottom: 1px solid #1e2438;
}

.task-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #14192a;
}

.task-name {
  color: #a0a8c0;
}

.task-hours {
  color: #8090b0;
  text-align: right;
  width: 60px;
}

.task-delta {
  text-align: right;
  font-weight: 600;
  width: 70px;
}

.no-changes {
  color: #506090;
  font-style: italic;
  text-align: center;
  padding: 20px;
}
</style>
