<template>
  <div class="space-y-4 p-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-sm font-semibold text-gray-900">CAM Risk Timeline</h1>
        <p class="text-[11px] text-gray-600">
          View saved pipeline snapshots with lane / preset filters and jump back into PipelineLab.
        </p>
      </div>
      <div class="flex items-center gap-2 text-[11px]">
        <button
          class="rounded border px-3 py-1 hover:bg-gray-50"
          :disabled="loading"
          @click="loadReports"
        >
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
        <span class="text-gray-400">/cam/risk/timeline-enhanced</span>
      </div>
    </header>

    <section class="rounded border border-gray-200 bg-white p-3 text-[11px] space-y-2">
      <div class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col gap-1">
          <span class="text-gray-600">Lane</span>
          <select v-model="laneFilter" class="rounded border px-2 py-1">
            <option value="rosette">Rosette</option>
            <option value="all">All lanes</option>
            <option
              v-for="lane in additionalLaneOptions"
              :key="lane"
              :value="lane"
            >
              {{ lane }}
            </option>
          </select>
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-gray-600">Preset</span>
          <select v-model="presetFilter" class="rounded border px-2 py-1 min-w-[140px]">
            <option value="all">All presets</option>
            <option
              v-for="preset in presetOptions"
              :key="preset"
              :value="preset"
            >
              {{ preset }}
            </option>
          </select>
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-gray-600">Window</span>
          <select v-model.number="daysBack" class="rounded border px-2 py-1">
            <option :value="3">Last 3 days</option>
            <option :value="7">Last 7 days</option>
            <option :value="14">Last 14 days</option>
            <option :value="30">Last 30 days</option>
            <option :value="0">All time</option>
          </select>
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-gray-600">Limit</span>
          <input
            type="number"
            v-model.number="limit"
            min="5"
            max="200"
            step="5"
            class="rounded border px-2 py-1 w-20"
          />
        </label>

        <button
          class="rounded bg-gray-900 px-3 py-1 font-semibold text-white hover:bg-gray-800"
          :disabled="loading"
          @click="loadReports"
        >
          Apply Filters
        </button>
      </div>

      <div v-if="errorMsg" class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">
        {{ errorMsg }}
      </div>
      <div v-else-if="loading" class="text-gray-500">Loading reports…</div>
      <div v-else-if="!reports.length" class="text-gray-500">
        No reports found for this window.
      </div>

      <div v-if="presetTrends.length" class="grid gap-2 md:grid-cols-2">
        <div
          v-for="trend in presetTrends"
          :key="trend.preset"
          class="rounded border border-sky-100 bg-sky-50 px-3 py-2"
        >
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sky-900">Preset: {{ trend.preset }}</span>
            <span class="text-[10px] text-sky-700">{{ trend.count }} reports</span>
          </div>
          <div class="text-gray-700">
            Avg length: {{ formatLength(trend.avgLength) }} · Avg lines: {{ formatLines(trend.avgLines) }}
          </div>
        </div>
      </div>
    </section>

    <section v-if="reports.length" class="rounded border border-gray-200 bg-white">
      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-[11px]">
          <thead class="border-b bg-gray-50 text-gray-600">
            <tr>
              <th class="px-3 py-2">Created</th>
              <th class="px-3 py-2">Lane</th>
              <th class="px-3 py-2">Preset</th>
              <th class="px-3 py-2">Job</th>
              <th class="px-3 py-2">Summary</th>
              <th class="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="report in reports"
              :key="report.id"
              class="border-b last:border-b-0 hover:bg-gray-50"
            >
              <td class="px-3 py-2 whitespace-nowrap">
                {{ formatTimestamp(report.created_at) }}
              </td>
              <td class="px-3 py-2">
                <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase">
                  {{ report.lane }}
                </span>
              </td>
              <td class="px-3 py-2">
                <span class="font-mono text-[10px]">{{ report.preset ?? '—' }}</span>
              </td>
              <td class="px-3 py-2">
                <div class="font-mono text-[10px]">{{ report.job_id ?? '—' }}</div>
              </td>
              <td class="px-3 py-2">
                <div class="flex flex-wrap gap-2 text-gray-800">
                  <span class="rounded bg-gray-100 px-2 py-0.5">Steps: {{ report.summary.steps_count ?? '—' }}</span>
                  <span class="rounded bg-gray-100 px-2 py-0.5">Rings: {{ report.summary.rings ?? '—' }}</span>
                  <span class="rounded bg-gray-100 px-2 py-0.5">Z: {{ report.summary.z_passes ?? '—' }}</span>
                  <span class="rounded bg-gray-100 px-2 py-0.5">Len: {{ formatLength(report.summary.total_length) }}</span>
                  <span class="rounded bg-gray-100 px-2 py-0.5">Lines: {{ formatLines(report.summary.total_lines) }}</span>
                </div>
              </td>
              <td class="px-3 py-2">
                <div class="flex justify-end gap-2">
                  <button
                    class="rounded border border-gray-300 px-2 py-0.5 text-[10px] hover:bg-gray-100"
                    @click="openPipeline(report)"
                  >
                    Pipeline
                  </button>
                  <button
                    v-if="report.lane === 'rosette'"
                    class="rounded border border-amber-300 px-2 py-0.5 text-[10px] text-amber-800 hover:bg-amber-50"
                    @click="openArtStudio(report)"
                  >
                    Art Studio
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchCamRiskTimelineReports,
  type CamRiskTimelineReport,
} from '@/api/camRisk'

const router = useRouter()

const reports = ref<CamRiskTimelineReport[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)

const laneFilter = ref<'rosette' | 'all' | string>('rosette')
const presetFilter = ref<string>('all')
const daysBack = ref<number>(7)
const limit = ref<number>(40)

const additionalLaneOptions = computed(() => {
  const options = new Set<string>()
  reports.value.forEach((r) => {
    if (r.lane !== 'rosette') {
      options.add(r.lane)
    }
  })
  return Array.from(options)
})

const presetOptions = computed(() => {
  const options = new Set<string>()
  reports.value.forEach((r) => {
    if (r.preset) {
      options.add(r.preset)
    }
  })
  return Array.from(options).sort((a, b) => a.localeCompare(b))
})

const presetTrends = computed(() => {
  const map = new Map<string, { count: number; totalLength: number; totalLines: number }>()
  for (const report of reports.value) {
    const key = report.preset || 'unset'
    if (!map.has(key)) {
      map.set(key, { count: 0, totalLength: 0, totalLines: 0 })
    }
    const bucket = map.get(key)!
    bucket.count += 1
    if (typeof report.summary.total_length === 'number') {
      bucket.totalLength += report.summary.total_length
    }
    if (typeof report.summary.total_lines === 'number') {
      bucket.totalLines += report.summary.total_lines
    }
  }

  return Array.from(map.entries()).map(([preset, info]) => ({
    preset,
    count: info.count,
    avgLength: info.count ? info.totalLength / info.count : 0,
    avgLines: info.count ? info.totalLines / info.count : 0,
  }))
})

function formatTimestamp(ts: number): string {
  return new Date(ts * 1000).toLocaleString()
}

function formatLength(value?: number): string {
  if (typeof value !== 'number') return '—'
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)} m`
  }
  return `${value.toFixed(1)} mm`
}

function formatLines(value?: number): string {
  if (typeof value !== 'number') return '—'
  return `${value.toFixed(0)} lines`
}

async function loadReports() {
  loading.value = true
  errorMsg.value = null

  try {
    const nowSeconds = Date.now() / 1000
    const startTs = daysBack.value > 0 ? nowSeconds - daysBack.value * 86400 : undefined
    const lane = laneFilter.value === 'all' ? null : laneFilter.value
    const preset = presetFilter.value === 'all' ? null : presetFilter.value
    const data = await fetchCamRiskTimelineReports({
      lane,
      preset,
      limit: limit.value,
      startTs,
    })
    reports.value = data
  } catch (err: any) {
    console.error('Failed to load risk reports', err)
    errorMsg.value = err?.message || 'Failed to load risk reports.'
  } finally {
    loading.value = false
  }
}

function openPipeline(report: CamRiskTimelineReport) {
  const query: Record<string, string> = { lane: report.lane }
  if (report.job_id) query.job_id = report.job_id
  if (report.preset) query.preset = report.preset
  router.push({ path: '/lab/pipeline', query })
}

function openArtStudio(report: CamRiskTimelineReport) {
  const query: Record<string, string> = {}
  if (report.job_id) query.job_id = report.job_id
  router.push({ path: '/art/rosette', query })
}

onMounted(() => {
  loadReports()
})
</script>
