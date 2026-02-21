<template>
  <div
    v-if="toolpathResult"
    class="toolpath-results"
  >
    <h4>Toolpath Generated</h4>
    <div class="stats-grid">
      <div class="stat-item">
        <span class="label">Moves:</span>
        <span class="value">{{ toolpathResult.stats?.move_count || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="label">Length:</span>
        <span class="value">{{ (toolpathResult.stats?.length_mm || 0).toFixed(1) }} mm</span>
      </div>
      <div class="stat-item">
        <span class="label">Time:</span>
        <span class="value">{{ (toolpathResult.stats?.time_s || 0).toFixed(1) }} s</span>
      </div>
      <div class="stat-item">
        <span class="label">Area:</span>
        <span class="value">{{ (toolpathResult.stats?.area_mm2 || 0).toFixed(1) }} mm²</span>
      </div>
    </div>

    <!-- Backplot Viewer -->
    <div class="backplot-container">
      <CamBackplotViewer
        :moves="toolpathResult.moves || []"
        :stats="toolpathResult.stats"
        :units="units"
        :machine-limits="machineLimits"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import CamBackplotViewer from '@/components/CamBackplotViewer.vue'

interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

interface ToolpathStats {
  move_count?: number
  length_mm?: number
  time_s?: number
  area_mm2?: number
}

interface ToolpathResult {
  moves?: any[]
  stats?: ToolpathStats
}

defineProps<{
  toolpathResult: ToolpathResult | null
  units: 'mm' | 'inch'
  machineLimits: MachineLimits | null
}>()
</script>

<style scoped>
.toolpath-results {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.toolpath-results h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.stat-item .label {
  font-weight: 500;
  color: #6b7280;
}

.stat-item .value {
  color: #1f2937;
  font-weight: 600;
}

.backplot-container {
  margin-top: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}
</style>
