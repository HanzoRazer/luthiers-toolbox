<template>
  <div class="preset-compare-ab">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900">
        Preset A/B Compare
      </h2>
      <button
        class="btn-secondary"
        @click="$router.back()"
      >
        ← Back to Tuning Tree
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex justify-center py-12"
    >
      <div class="loader" />
    </div>

    <!-- Comparison Grid -->
    <div
      v-else
      class="grid grid-cols-2 gap-6"
    >
      <PresetColumn
        :preset="presetA"
        column="A"
        accent-color="blue"
        @navigate="navigateToRosetteCompare($event, 'A')"
      />
      <PresetColumn
        :preset="presetB"
        column="B"
        accent-color="purple"
        @navigate="navigateToRosetteCompare($event, 'B')"
      />
    </div>

    <!-- Comparison Summary -->
    <div
      v-if="!loading"
      class="mt-6 p-6 bg-gray-50 rounded-lg border"
    >
      <h3 class="text-lg font-bold mb-4">
        Comparison Summary
      </h3>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <p class="text-sm text-gray-600">
            Job Count Δ
          </p>
          <p
            :class="getComparisonClass(jobDelta)"
            class="text-xl font-bold"
          >
            {{ jobDelta > 0 ? '+' : '' }}{{ jobDelta }}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-600">
            Risk Count Δ
          </p>
          <p
            :class="getComparisonClass(riskDelta, true)"
            class="text-xl font-bold"
          >
            {{ riskDelta > 0 ? '+' : '' }}{{ riskDelta }}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-600">
            Avg Length Δ
          </p>
          <p
            :class="getComparisonClass(lengthDelta)"
            class="text-xl font-bold"
          >
            {{ lengthDelta > 0 ? '+' : '' }}{{ lengthDelta.toFixed(1) }} mm
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PresetColumn, type PresetAggRow } from './art/preset-compare'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const presetA = ref<PresetAggRow | null>(null)
const presetB = ref<PresetAggRow | null>(null)

// Computed deltas
const jobDelta = computed(() => 
  (presetB.value?.job_count || 0) - (presetA.value?.job_count || 0)
)
const riskDelta = computed(() => 
  (presetB.value?.risk_count || 0) - (presetA.value?.risk_count || 0)
)
const lengthDelta = computed(() => 
  (presetB.value?.avg_total_length || 0) - (presetA.value?.avg_total_length || 0)
)

function getComparisonClass(value: number, inverse = false): string {
  if (value === 0) return 'text-gray-600'
  const isPositive = value > 0
  const isBad = inverse ? isPositive : !isPositive
  return isBad ? 'text-red-600' : 'text-green-600'
}

function navigateToRosetteCompare(presetId: string | undefined, column: 'A' | 'B') {
  if (!presetId) return
  
  router.push({
    path: '/art/rosette/compare',
    query: {
      [`preset${column}`]: presetId
    }
  })
}

async function fetchData() {
  loading.value = true
  try {
    const presetAId = route.query.presetA as string
    const presetBId = route.query.presetB as string
    
    const response = await api('/api/art/presets_aggregate')
    const data: PresetAggRow[] = await response.json()
    
    presetA.value = data.find(p => p.preset_id === presetAId) || null
    presetB.value = data.find(p => p.preset_id === presetBId) || null
  } catch (error) {
    console.error('Failed to load preset comparison:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.preset-compare-ab {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.loader {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-secondary {
  background-color: white;
  color: #374151;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}
</style>
