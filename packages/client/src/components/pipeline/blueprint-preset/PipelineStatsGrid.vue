<script setup lang="ts">
/**
 * PipelineStatsGrid - Display grid for pipeline run statistics
 * Extracted from BlueprintPresetPanel.vue
 */

interface PipelineStats {
  move_count?: number
  length_mm?: number
  area_mm2?: number
  time_s?: number
}

defineProps<{
  stats: PipelineStats
}>()
</script>

<template>
  <div>
    <h3 class="section-title">Stats</h3>
    <div class="stats-grid">
      <div class="stat-box">
        <span class="stat-label">Moves:</span>
        <strong class="stat-value">{{ stats.move_count }}</strong>
      </div>
      <div
        v-if="stats.length_mm"
        class="stat-box"
      >
        <span class="stat-label">Length:</span>
        <strong class="stat-value">{{ stats.length_mm }} mm</strong>
      </div>
      <div
        v-if="stats.area_mm2"
        class="stat-box"
      >
        <span class="stat-label">Area:</span>
        <strong class="stat-value">{{ stats.area_mm2 }} mm²</strong>
      </div>
      <div
        v-if="stats.time_s"
        class="stat-box"
      >
        <span class="stat-label">Time:</span>
        <strong class="stat-value">{{ stats.time_s }} s</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 1.1em;
  margin-bottom: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.stat-box {
  padding: 10px;
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-label {
  font-size: 0.85em;
  color: #666;
}

.stat-value {
  font-size: 1.2em;
  color: #333;
}
</style>
