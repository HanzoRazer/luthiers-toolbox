<script setup lang="ts">
/**
 * InlayBomPanel — Bill of Materials display for inlay patterns
 */

interface BomEntry {
  shape_type: string;
  material_key: string;
  count: number;
  area_mm2: number;
}

interface BomTotal {
  total_pieces: number;
  total_area_mm2: number;
}

defineProps<{
  entries: BomEntry[];
  total: BomTotal | null;
}>();
</script>

<template>
  <div
    v-if="total"
    class="bom-panel"
  >
    <h4>Bill of Materials</h4>
    <table class="bom-table">
      <thead>
        <tr>
          <th>Shape</th>
          <th>Material</th>
          <th>Count</th>
          <th>Area (mm²)</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(entry, idx) in entries"
          :key="idx"
        >
          <td>
            {{ entry.shape_type }}
          </td>
          <td>
            {{ entry.material_key }}
          </td>
          <td>
            {{ entry.count }}
          </td>
          <td>
            {{ entry.area_mm2.toFixed(1) }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="2">
            <strong>Total</strong>
          </td>
          <td>
            <strong>{{ total.total_pieces }}</strong>
          </td>
          <td>
            <strong>{{ total.total_area_mm2.toFixed(1) }}</strong>
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped>
.bom-panel {
  background: var(--color-bg-secondary, #1e1e2e);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
}

.bom-panel h4 {
  margin: 0 0 0.4rem;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary, #aaa);
}

.bom-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.bom-table th,
.bom-table td {
  padding: 0.3rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, #333);
}

.bom-table th {
  color: var(--color-text-secondary, #aaa);
  font-weight: 600;
}

.bom-table tfoot td {
  border-top: 2px solid var(--color-border, #555);
}
</style>
