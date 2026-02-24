<script setup lang="ts">
/**
 * BenchResultsPanel - Benchmark results display
 * Extracted from AdaptiveBenchLab.vue
 */
interface BenchResult {
  runs: number
  total_ms: number
  avg_ms: number
  width: number
  height: number
}

defineProps<{
  result: BenchResult
}>()
</script>

<template>
  <div class="bench-results">
    <h4>Benchmark Results</h4>
    <div class="stats-grid">
      <div class="stat">
        <div class="stat-label">
          Total Time
        </div>
        <div class="stat-value">
          {{ result.total_ms.toFixed(2) }} ms
        </div>
      </div>
      <div class="stat">
        <div class="stat-label">
          Average Time
        </div>
        <div class="stat-value">
          {{ result.avg_ms.toFixed(3) }} ms
        </div>
      </div>
      <div class="stat">
        <div class="stat-label">
          Runs
        </div>
        <div class="stat-value">
          {{ result.runs }}
        </div>
      </div>
      <div class="stat">
        <div class="stat-label">
          Geometry
        </div>
        <div class="stat-value">
          {{ result.width }}×{{ result.height }} mm
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bench-results {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
}

.bench-results h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #555;
  font-size: 0.95rem;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat {
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.stat-label {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
}
</style>
