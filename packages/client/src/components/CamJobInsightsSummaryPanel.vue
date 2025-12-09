<template>
  <div class="border rounded-lg bg-white p-3 text-[11px] space-y-2">
    <div class="flex items-center justify-between gap-2">
      <div>
        <div class="font-semibold text-gray-800">Job Intelligence Summary</div>
        <div class="text-[10px] text-gray-500">Patterns across machines, woods, and review gates</div>
      </div>
      <div class="flex items-center gap-2 text-[10px]">
        <button
          type="button"
          class="px-2 py-1 rounded border text-gray-700 hover:bg-gray-50"
          :disabled="loading"
          @click="load"
        >
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 text-[10px]">
      <label class="flex items-center gap-1">
        Machine
        <select v-model="filterMachine" class="border rounded px-1 py-0.5 text-[10px] min-w-[140px]">
          <option value="">All</option>
          <option v-for="m in machineOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </label>

      <label class="flex items-center gap-1">
        Wood
        <select v-model="filterWood" class="border rounded px-1 py-0.5 text-[10px] min-w-[100px]">
          <option value="">All</option>
          <option v-for="w in woodOptions" :key="w" :value="w">{{ w }}</option>
        </select>
      </label>

      <label class="flex items-center gap-1">
        Limit
        <select v-model.number="limit" class="border rounded px-1 py-0.5 text-[10px]">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </label>

      <span class="text-[10px] text-gray-500">{{ insights.length }} insights loaded</span>
    </div>

    <div v-if="errorText" class="text-[10px] text-red-600">{{ errorText }}</div>

    <div v-if="!loading && !insights.length && !errorText" class="text-[10px] text-gray-500">
      No insights available yet. Run some jobs through the pipeline to populate this view.
    </div>

    <div v-else class="space-y-2">
      <div class="grid grid-cols-4 gap-2 text-[10px]">
        <div class="border rounded p-2 bg-gray-50">
          <div class="text-gray-500">Below gate</div>
          <div class="text-xs font-semibold text-emerald-800">{{ counts.below_gate }}</div>
        </div>
        <div class="border rounded p-2 bg-gray-50">
          <div class="text-gray-500">Near gate</div>
          <div class="text-xs font-semibold text-amber-800">{{ counts.near_gate }}</div>
        </div>
        <div class="border rounded p-2 bg-gray-50">
          <div class="text-gray-500">Over gate</div>
          <div class="text-xs font-semibold text-red-700">{{ counts.over_gate }}</div>
        </div>
        <div class="border rounded p-2 bg-gray-50">
          <div class="text-gray-500">Blocked</div>
          <div class="text-xs font-semibold text-red-700">{{ counts.blocked }}</div>
        </div>
      </div>

      <div class="overflow-x-auto max-h-64">
        <table class="min-w-full text-[10px] whitespace-nowrap">
          <thead class="border-b bg-gray-50">
            <tr>
              <th class="px-2 py-1 text-left">Job</th>
              <th class="px-2 py-1 text-left">Machine</th>
              <th class="px-2 py-1 text-left">Wood</th>
              <th class="px-2 py-1 text-right">Gate %</th>
              <th class="px-2 py-1 text-right">Review %</th>
              <th class="px-2 py-1 text-right">Δ %</th>
              <th class="px-2 py-1 text-left">Class</th>
              <th class="px-2 py-1 text-left">Tags</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in filteredInsights" :key="i.job_id" class="border-b last:border-0">
              <td class="px-2 py-1 max-w-[180px] truncate" :title="i.job_name || ''">{{ i.job_name || '(unnamed)' }}</td>
              <td class="px-2 py-1 max-w-[160px] truncate">{{ i.machine_name || i.machine_id || '—' }}</td>
              <td class="px-2 py-1">{{ i.wood_hint || '—' }}</td>
              <td class="px-2 py-1 text-right">
                <span v-if="i.gate_pct != null">{{ i.gate_pct.toFixed(1) }}</span>
                <span v-else>—</span>
              </td>
              <td class="px-2 py-1 text-right">
                <span v-if="i.review_pct != null">{{ i.review_pct.toFixed(1) }}</span>
                <span v-else>—</span>
              </td>
              <td class="px-2 py-1 text-right">
                <span v-if="i.delta_pct != null">{{ i.delta_pct.toFixed(1) }}</span>
                <span v-else>—</span>
              </td>
              <td class="px-2 py-1">
                <span class="px-2 py-0.5 rounded-full" :class="classificationClass(i)">{{ i.classification }}</span>
              </td>
              <td class="px-2 py-1 max-w-[180px] truncate" :title="i.tags.join(', ')">
                <span
                  v-for="tag in i.tags"
                  :key="tag"
                  class="inline-block px-1.5 py-0.5 mr-1 mb-0.5 rounded-full bg-gray-100 text-gray-600"
                >
                  {{ tag }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'

interface JobInsight {
  job_id: string
  job_name?: string | null
  machine_id?: string | null
  machine_name?: string | null
  wood_hint?: string | null
  gate_pct?: number | null
  review_pct?: number | null
  delta_pct?: number | null
  classification: 'below_gate' | 'near_gate' | 'over_gate' | 'blocked' | 'no_data'
  severity: 'ok' | 'warn' | 'error'
  recommendation: string
  tags: string[]
}

const insights = ref<JobInsight[]>([])
const loading = ref(false)
const errorText = ref<string | null>(null)

const limit = ref<number>(50)
const filterMachine = ref<string>('')
const filterWood = ref<string>('')

const machineOptions = computed(() => {
  const seen = new Map<string, string>()
  for (const i of insights.value) {
    const key = i.machine_name || i.machine_id
    if (!key) continue
    const label = i.machine_name || i.machine_id || 'Unknown'
    if (!seen.has(key)) {
      seen.set(key, label)
    }
  }
  return Array.from(seen.entries()).map(([value, label]) => ({ value, label }))
})

const woodOptions = computed(() => {
  const set = new Set<string>()
  for (const i of insights.value) {
    if (i.wood_hint) set.add(i.wood_hint)
  }
  return Array.from(set)
})

const filteredInsights = computed(() => {
  return insights.value.filter((i) => {
    if (filterMachine.value) {
      const label = i.machine_name || i.machine_id || ''
      if (label !== filterMachine.value) return false
    }
    if (filterWood.value) {
      if (!i.wood_hint || i.wood_hint !== filterWood.value) return false
    }
    return true
  })
})

const counts = computed(() => {
  let below_gate = 0
  let near_gate = 0
  let over_gate = 0
  let blocked = 0
  for (const i of filteredInsights.value) {
    switch (i.classification) {
      case 'below_gate':
        below_gate++
        break
      case 'near_gate':
        near_gate++
        break
      case 'over_gate':
        over_gate++
        break
      case 'blocked':
        blocked++
        break
      default:
        break
    }
  }
  return { below_gate, near_gate, over_gate, blocked }
})

function classificationClass(i: JobInsight): string {
  switch (i.classification) {
    case 'below_gate':
      return 'bg-emerald-50 text-emerald-800'
    case 'near_gate':
      return 'bg-amber-50 text-amber-800'
    case 'over_gate':
      return 'bg-red-50 text-red-700'
    case 'blocked':
      return 'bg-red-700 text-white'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

async function load() {
  loading.value = true
  errorText.value = null
  try {
    const params: Record<string, any> = { limit: limit.value }
    if (filterMachine.value) {
      params.machine_id = filterMachine.value
    }
    if (filterWood.value) {
      params.wood = filterWood.value
    }
    const res = await axios.get('/api/cam/job_log/insights', { params })
    insights.value = res.data || []
  } catch (err) {
    console.warn('[CamJobInsightsSummaryPanel] failed to load insights:', err)
    errorText.value = 'Failed to load job insight summary.'
  } finally {
    loading.value = false
  }
}

watch(limit, () => {
  load()
})

onMounted(() => {
  load()
})
</script>
