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
      <!-- Column A -->
      <div class="preset-column border-2 border-blue-500 rounded-lg p-6 bg-blue-50">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-lg font-bold text-blue-600">Preset A</span>
          <span :class="`badge badge-${presetA?.health_color}`">
            {{ presetA?.health_color?.toUpperCase() }}
          </span>
          <span
            class="text-2xl"
            :title="`Trend: ${presetA?.trend_direction}`"
          >
            {{ getTrendIcon(presetA?.trend_direction) }}
          </span>
        </div>
        
        <h3 class="text-xl font-semibold mb-2">
          {{ presetA?.preset_name }}
        </h3>
        <p class="text-sm text-gray-600 mb-4">
          ID: {{ presetA?.preset_id }}
        </p>

        <!-- Lineage -->
        <div
          v-if="presetA?.parent_name"
          class="mb-4 p-3 bg-white rounded border"
        >
          <p class="text-xs text-gray-500">
            Parent:
          </p>
          <p class="text-sm font-medium">
            {{ presetA.parent_name }}
          </p>
          <p class="text-xs text-gray-600 mt-1">
            {{ presetA.diff_summary }}
          </p>
          <p class="text-xs text-gray-500 italic mt-1">
            {{ presetA.rationale }}
          </p>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <p class="stat-label">
              Jobs
            </p>
            <p class="stat-value">
              {{ presetA?.job_count }}
            </p>
          </div>
          <div class="stat-card">
            <p class="stat-label">
              Risks
            </p>
            <p class="stat-value text-yellow-600">
              {{ presetA?.risk_count }}
            </p>
          </div>
          <div class="stat-card">
            <p class="stat-label">
              Critical
            </p>
            <p class="stat-value text-red-600">
              {{ presetA?.critical_count }}
            </p>
          </div>
        </div>

        <!-- Averages -->
        <div class="mt-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Avg Length:</span>
            <span class="font-medium">{{ presetA?.avg_total_length?.toFixed(1) }} mm</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Avg Lines:</span>
            <span class="font-medium">{{ presetA?.avg_total_lines }}</span>
          </div>
        </div>

        <!-- Geometry Link -->
        <button 
          class="mt-4 w-full btn-primary"
          @click="navigateToRosetteCompare(presetA?.preset_id, 'A')"
        >
          View Geometry Runs →
        </button>
      </div>

      <!-- Column B -->
      <div class="preset-column border-2 border-purple-500 rounded-lg p-6 bg-purple-50">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-lg font-bold text-purple-600">Preset B</span>
          <span :class="`badge badge-${presetB?.health_color}`">
            {{ presetB?.health_color?.toUpperCase() }}
          </span>
          <span
            class="text-2xl"
            :title="`Trend: ${presetB?.trend_direction}`"
          >
            {{ getTrendIcon(presetB?.trend_direction) }}
          </span>
        </div>
        
        <h3 class="text-xl font-semibold mb-2">
          {{ presetB?.preset_name }}
        </h3>
        <p class="text-sm text-gray-600 mb-4">
          ID: {{ presetB?.preset_id }}
        </p>

        <!-- Lineage -->
        <div
          v-if="presetB?.parent_name"
          class="mb-4 p-3 bg-white rounded border"
        >
          <p class="text-xs text-gray-500">
            Parent:
          </p>
          <p class="text-sm font-medium">
            {{ presetB.parent_name }}
          </p>
          <p class="text-xs text-gray-600 mt-1">
            {{ presetB.diff_summary }}
          </p>
          <p class="text-xs text-gray-500 italic mt-1">
            {{ presetB.rationale }}
          </p>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <p class="stat-label">
              Jobs
            </p>
            <p class="stat-value">
              {{ presetB?.job_count }}
            </p>
          </div>
          <div class="stat-card">
            <p class="stat-label">
              Risks
            </p>
            <p class="stat-value text-yellow-600">
              {{ presetB?.risk_count }}
            </p>
          </div>
          <div class="stat-card">
            <p class="stat-label">
              Critical
            </p>
            <p class="stat-value text-red-600">
              {{ presetB?.critical_count }}
            </p>
          </div>
        </div>

        <!-- Averages -->
        <div class="mt-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Avg Length:</span>
            <span class="font-medium">{{ presetB?.avg_total_length?.toFixed(1) }} mm</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Avg Lines:</span>
            <span class="font-medium">{{ presetB?.avg_total_lines }}</span>
          </div>
        </div>

        <!-- Geometry Link -->
        <button 
          class="mt-4 w-full btn-primary bg-purple-600 hover:bg-purple-700"
          @click="navigateToRosetteCompare(presetB?.preset_id, 'B')"
        >
          View Geometry Runs →
        </button>
      </div>
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

interface PresetAggRow {
  preset_id: string
  preset_name: string
  lane: string
  parent_id: string | null
  parent_name: string | null
  diff_summary: string | null
  rationale: string | null
  source: string
  job_count: number
  risk_count: number
  critical_count: number
  avg_total_length: number
  avg_total_lines: number
  health_color: 'green' | 'yellow' | 'red'
  trend_direction: 'up' | 'down' | 'flat'
  trend_delta: number
}

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

function getTrendIcon(trend?: string): string {
  switch (trend) {
    case 'up': return '▲'
    case 'down': return '▼'
    case 'flat': return '→'
    default: return '–'
  }
}

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

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-green {
  background-color: #d1fae5;
  color: #065f46;
}

.badge-yellow {
  background-color: #fef3c7;
  color: #92400e;
}

.badge-red {
  background-color: #fee2e2;
  color: #991b1b;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.stat-card {
  background: white;
  border-radius: 0.5rem;
  padding: 0.75rem;
  text-align: center;
  border: 1px solid #e5e7eb;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #2563eb;
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
