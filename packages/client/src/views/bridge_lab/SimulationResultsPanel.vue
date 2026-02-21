<template>
  <div
    v-if="simResult"
    class="sim-results"
  >
    <h4>Simulation Results</h4>
    <div class="stats-grid">
      <div class="stat-item">
        <span class="label">Moves:</span>
        <span class="value">{{ simResult.move_count || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="label">Length:</span>
        <span class="value">{{ (simResult.length_mm || 0).toFixed(1) }} mm</span>
      </div>
      <div class="stat-item">
        <span class="label">Time:</span>
        <span class="value">{{ (simResult.time_s || 0).toFixed(1) }} s</span>
      </div>
      <div class="stat-item">
        <span class="label">Units:</span>
        <span class="value">{{ simResult.units }}</span>
      </div>
    </div>

    <!-- Simulation Backplot -->
    <div class="backplot-container">
      <CamBackplotViewer
        :moves="simResult.moves || []"
        :stats="{ move_count: simResult.move_count, time_s: simResult.time_s }"
        :sim-issues="simResult.issues"
        :units="(simResult.units as 'mm' | 'inch') || 'mm'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import CamBackplotViewer from '@/components/CamBackplotViewer.vue'

interface SimulationResult {
  move_count?: number
  length_mm?: number
  time_s?: number
  units?: string
  moves?: any[]
  issues?: any[]
}

defineProps<{
  simResult: SimulationResult | null
}>()
</script>

<style scoped>
.sim-results {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.sim-results h4 {
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
