<template>
  <div class="adaptive-bench-lab">
    <h2>Adaptive Benchmark Lab (N16)</h2>
    <p class="subtitle">
      Performance profiling for adaptive spiral algorithms - Trochoidal corner visualization
    </p>

    <div class="lab-grid">
      <!-- Left: Parameters & Controls -->
      <BenchParamsPanel
        :params="params"
        :loading="loading"
        @update:params="params = $event"
        @generate-spiral="generateSpiral"
        @generate-trochoid="generateTrochoid"
        @run-benchmark="runBenchmark"
      />

      <!-- Right: Visualization & Results -->
      <BenchOutputPanel
        :error="error"
        :svg-content="svgContent"
        :bench-result="benchResult"
      />
    </div>

    <BenchInfoSection />
  </div>
</template>

<script setup lang="ts">
/**
 * AdaptiveBenchLab.vue
 *
 * Performance profiling for adaptive spiral algorithms.
 *
 * REFACTORED: Child components and composable extracted:
 * - BenchParamsPanel: Parameter input panel
 * - BenchOutputPanel: Output visualization panel
 * - BenchInfoSection: Info cards section
 * - useAdaptiveBenchActions: API actions composable
 */
import { ref } from "vue"
import {
  BenchParamsPanel,
  BenchOutputPanel,
  BenchInfoSection,
  useAdaptiveBenchActions,
  type BenchParams
} from "./adaptive-bench"

// Parameters
const params = ref<BenchParams>({
  width: 100,
  height: 60,
  toolDia: 6.0,
  stepover: 2.4,
  cornerFillet: 0.6,
  loopPitch: 2.5,
  amplitude: 0.4,
  benchRuns: 20
})

// Actions composable
const {
  loading,
  error,
  svgContent,
  benchResult,
  generateSpiral,
  generateTrochoid,
  runBenchmark
} = useAdaptiveBenchActions(params)
</script>

<style scoped>
.adaptive-bench-lab {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.subtitle {
  color: #666;
  margin-bottom: 1.5rem;
}

.lab-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

@media (max-width: 1024px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>
