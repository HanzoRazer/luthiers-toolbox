<script setup lang="ts">
/**
 * BenchInfoSection.vue - Info cards section
 * Extracted from AdaptiveBenchLab.vue
 */
</script>

<template>
  <section class="info-section">
    <h3>About N16 Benchmark Suite</h3>
    <div class="info-grid">
      <div class="info-card">
        <h4>Offset Spiral</h4>
        <p>Generates inward offset rings stitched into continuous spiral path. Tests adaptive toolpath algorithm performance.</p>
      </div>
      <div class="info-card">
        <h4>Trochoidal Corners</h4>
        <p>Small sine-modulated loops around corners to reduce chip load. Illustrates corner load management technique.</p>
      </div>
      <div class="info-card">
        <h4>Performance Benchmark</h4>
        <p>Measures algorithm execution time over multiple runs. Helps validate Module L.3 performance characteristics.</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.info-section {
  margin-top: 3rem;
}

.info-section h3 {
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
}

.info-card h4 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #0f172a;
  font-size: 0.95rem;
}

.info-card p {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
}
</style>
