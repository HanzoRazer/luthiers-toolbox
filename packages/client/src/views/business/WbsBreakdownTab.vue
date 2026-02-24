<script setup lang="ts">
/**
 * WBS Breakdown Tab - Work breakdown structure table
 * Extracted from EngineeringEstimatorView.vue
 */
import { businessEstimator } from "@/sdk/endpoints";
import type { WBSTask } from "@/types/businessEstimator";

defineProps<{
  tasks: WBSTask[];
  totalHours: number;
  laborCost: number;
}>();
</script>

<template>
  <div class="tab-content">
    <table class="wbs-table">
      <thead>
        <tr>
          <th>Task</th>
          <th class="num">Base</th>
          <th class="num">Adjusted</th>
          <th class="num">Cost</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.task_id">
          <td>
            <span
              class="group-indicator"
              :style="{ background: businessEstimator.getGroupColor(task.notes) }"
            ></span>
            {{ task.task_name }}
          </td>
          <td class="num">{{ task.base_hours.toFixed(1) }}h</td>
          <td class="num">{{ task.adjusted_hours.toFixed(1) }}h</td>
          <td class="num">${{ task.labor_cost.toFixed(0) }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td><strong>Total</strong></td>
          <td class="num">—</td>
          <td class="num"><strong>{{ totalHours.toFixed(1) }}h</strong></td>
          <td class="num"><strong>${{ laborCost.toFixed(0) }}</strong></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped>
.tab-content {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 3px;
  padding: 16px;
}

.wbs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.wbs-table th {
  text-align: left;
  font-size: 9px;
  letter-spacing: 2px;
  color: #404870;
  text-transform: uppercase;
  padding: 8px 4px;
  border-bottom: 1px solid #1e2438;
}

.wbs-table td {
  padding: 6px 4px;
  border-bottom: 1px solid #13172a;
  color: #a0a8c0;
}

.wbs-table .num {
  text-align: right;
  color: #7080a0;
}

.wbs-table tfoot td {
  border-top: 1px solid #2a3040;
  color: #60e0a0;
}

.group-indicator {
  display: inline-block;
  width: 3px;
  height: 12px;
  margin-right: 8px;
  border-radius: 1px;
  vertical-align: middle;
}
</style>
