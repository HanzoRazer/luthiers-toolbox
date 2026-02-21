<template>
  <div class="stats-grid">
    <div class="stat-card">
      <i class="pi pi-chart-line" />
      <div class="stat-value">
        {{ stats.contour_count }}
      </div>
      <div class="stat-label">
        Contours
      </div>
    </div>

    <div class="stat-card">
      <i class="pi pi-circle" />
      <div class="stat-value">
        {{ stats.total_points }}
      </div>
      <div class="stat-label">
        Points
      </div>
    </div>

    <div class="stat-card">
      <i class="pi pi-arrows-h" />
      <div class="stat-value">
        {{ stats.output_width_mm }}mm
      </div>
      <div class="stat-label">
        Width
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ConversionStats {
  contour_count: number
  total_points: number
  output_width_mm: number
}

defineProps<{
  stats: ConversionStats
}>()
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}

.stat-card i {
  font-size: 2rem;
  color: #007bff;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #495057;
}

.stat-label {
  color: #6c757d;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}
</style>
