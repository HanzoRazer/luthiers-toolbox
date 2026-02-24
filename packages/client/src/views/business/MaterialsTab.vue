<script setup lang="ts">
/**
 * Materials Tab - Material cost breakdown table
 * Extracted from EngineeringEstimatorView.vue
 */
import type { MaterialEstimate } from "@/types/businessEstimator";

defineProps<{
  materials: MaterialEstimate[];
  totalMaterialCost: number;
}>();
</script>

<template>
  <div class="tab-content">
    <table class="materials-table">
      <thead>
        <tr>
          <th>Category</th>
          <th class="num">Base Cost</th>
          <th class="num">Waste Factor</th>
          <th class="num">Adjusted</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(mat, i) in materials" :key="i">
          <td>{{ mat.category }}</td>
          <td class="num">${{ mat.base_cost.toFixed(0) }}</td>
          <td class="num">{{ mat.waste_factor.toFixed(2) }}×</td>
          <td class="num">${{ mat.adjusted_cost.toFixed(0) }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="3"><strong>Total Materials</strong></td>
          <td class="num"><strong>${{ totalMaterialCost.toFixed(0) }}</strong></td>
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

.materials-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.materials-table th {
  text-align: left;
  font-size: 9px;
  letter-spacing: 2px;
  color: #404870;
  text-transform: uppercase;
  padding: 8px 4px;
  border-bottom: 1px solid #1e2438;
}

.materials-table td {
  padding: 6px 4px;
  border-bottom: 1px solid #13172a;
  color: #a0a8c0;
}

.materials-table .num {
  text-align: right;
  color: #7080a0;
}

.materials-table tfoot td {
  border-top: 1px solid #2a3040;
  color: #60e0a0;
}
</style>
