<template>
  <div class="border rounded-lg bg-white p-3 text-[11px] space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-semibold text-gray-800">Simulation Metrics</h3>
        <p class="text-[10px] text-gray-500">Time, power, energy (chip/tool/work), feed compliance</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-2 py-1 border rounded hover:bg-gray-50" :disabled="!metrics" @click="downloadJSON">
          Export JSON
        </button>
        <button class="px-2 py-1 border rounded hover:bg-gray-50" :disabled="!hasTS" @click="downloadCSV">
          Export CSV
        </button>
        <button class="px-2 py-1 border rounded hover:bg-gray-50" :disabled="!metrics" @click="downloadMarkdown">
          Export Markdown
        </button>
      </div>
    </div>

    <!-- Top cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="border rounded p-2">
        <div class="text-[10px] text-gray-500">Total Time</div>
        <div class="text-sm font-semibold">{{ fmt(metrics?.total_time_s ?? 0, 2) }} s</div>
      </div>
      <div class="border rounded p-2">
        <div class="text-[10px] text-gray-500">Peak Power</div>
        <div class="text-sm font-semibold">{{ fmt(metrics?.peak_power_w ?? 0, 0) }} W</div>
      </div>
      <div class="border rounded p-2">
        <div class="text-[10px] text-gray-500">Total Energy</div>
        <div class="text-sm font-semibold">{{ fmt(metrics?.total_energy_j ?? 0, 0) }} J</div>
      </div>
      <div class="border rounded p-2">
        <div class="text-[10px] text-gray-500">Feed Limited</div>
        <div class="text-sm font-semibold">{{ fmt(metrics?.feed_limited_pct ?? 0, 1) }}%</div>
      </div>
    </div>

    <!-- Tiny charts row (pure SVG) -->
    <div v-if="hasTS" class="grid grid-cols-1 md:grid-cols-2 gap-2">
      <!-- Power sparkline -->
      <div class="border rounded p-2">
        <div class="flex items-center justify-between mb-1">
          <div class="text-[10px] text-gray-500">Power (W)</div>
          <div class="text-[10px] text-gray-400">min {{ fmt(minP,0) }} · mean {{ fmt(metrics?.mean_power_w ?? 0,0) }} · max {{ fmt(maxP,0) }}</div>
        </div>
        <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-24">
          <polyline :points="powerPolyline" fill="none" stroke="currentColor" stroke-width="1.2" class="text-blue-600"/>
        </svg>
      </div>

      <!-- Feed sparkline -->
      <div class="border rounded p-2">
        <div class="flex items-center justify-between mb-1">
          <div class="text-[10px] text-gray-500">Feed ({{ metrics?.units }}/min)</div>
          <div class="text-[10px] text-gray-400">min {{ fmt(minF,0) }} · avg {{ fmt(metrics?.avg_feed_u_per_min ?? 0,0) }} · max {{ fmt(maxF,0) }}</div>
        </div>
        <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-24">
          <polyline :points="feedPolyline" fill="none" stroke="currentColor" stroke-width="1.2" class="text-emerald-600"/>
        </svg>
      </div>
    </div>

    <!-- Timeseries table -->
    <div v-if="hasTS" class="border rounded">
      <table class="w-full text-[10px]">
        <thead class="bg-gray-50 text-gray-600">
          <tr>
            <th class="px-2 py-1 text-left">#</th>
            <th class="px-2 py-1 text-left">Code</th>
            <th class="px-2 py-1 text-right">Length (mm)</th>
            <th class="px-2 py-1 text-right">Feed ({{ metrics?.units }}/min)</th>
            <th class="px-2 py-1 text-right">t (s)</th>
            <th class="px-2 py-1 text-right">P (W)</th>
            <th class="px-2 py-1 text-right">E (J)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pagedTS" :key="row.idx" class="border-t">
            <td class="px-2 py-1">{{ row.idx }}</td>
            <td class="px-2 py-1">{{ row.code }}</td>
            <td class="px-2 py-1 text-right">{{ fmt(row.length_mm, 3) }}</td>
            <td class="px-2 py-1 text-right">{{ fmt(row.feed_u_per_min, 1) }}</td>
            <td class="px-2 py-1 text-right">{{ fmt(row.time_s, 3) }}</td>
            <td class="px-2 py-1 text-right">{{ fmt(row.power_w, 1) }}</td>
            <td class="px-2 py-1 text-right">{{ fmt(row.energy_j, 3) }}</td>
          </tr>
          <tr v-if="pagedTS.length === 0">
            <td class="px-2 py-2 text-gray-500" colspan="7">No entries.</td>
          </tr>
        </tbody>
      </table>
      <div class="flex items-center justify-between px-2 py-1 bg-gray-50 border-t">
        <div class="text-[10px] text-gray-500">
          {{ start+1 }}–{{ Math.min(end, timeseries.length) }} of {{ timeseries.length }}
        </div>
        <div class="flex items-center gap-1">
          <button class="px-2 py-0.5 border rounded disabled:opacity-50" :disabled="page===0" @click="page--">Prev</button>
          <button class="px-2 py-0.5 border rounded disabled:opacity-50" :disabled="end>=timeseries.length" @click="page++">Next</button>
        </div>
      </div>
    </div>

    <!-- No TS note -->
    <div v-else class="text-[10px] text-gray-500">
      Timeseries not provided. Re-run simulate with <span class="font-mono">include_timeseries=true</span>.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type SegTS = { idx: number, code: string, length_mm: number, feed_u_per_min: number, time_s: number, power_w: number, energy_j: number }
type Metrics = {
  total_time_s: number
  total_length_mm: number
  avg_feed_u_per_min: number
  total_energy_j: number
  chip_energy_j: number
  tool_energy_j: number
  work_energy_j: number
  peak_power_w: number
  mean_power_w: number
  feed_limited_pct: number
  timeseries?: SegTS[]
  units: 'mm'|'inch'
}

const props = defineProps<{ metrics: Metrics | null }>()

const timeseries = computed<SegTS[]>(() => props.metrics?.timeseries ?? [])
const hasTS = computed(() => timeseries.value.length > 0)

function fmt(n: number, d = 0) {
  return n.toFixed(d)
}

/* paging */
const page = ref(0)
const pageSize = ref(50)
const start = computed(() => page.value * pageSize.value)
const end = computed(() => start.value + pageSize.value)
const pagedTS = computed(() => timeseries.value.slice(start.value, end.value))

/* chart setup */
const W = 300
const H = 72

const minP = computed(() => timeseries.value.reduce((m, r) => Math.min(m, r.power_w), Number.POSITIVE_INFINITY) || 0)
const maxP = computed(() => timeseries.value.reduce((m, r) => Math.max(m, r.power_w), 0))
const minF = computed(() => timeseries.value.reduce((m, r) => Math.min(m, r.feed_u_per_min), Number.POSITIVE_INFINITY) || 0)
const maxF = computed(() => timeseries.value.reduce((m, r) => Math.max(m, r.feed_u_per_min), 0))

function sparklinePoints(values: number[], ymin: number, ymax: number) {
  if (values.length === 0) return ''
  const n = values.length
  const xs = (i: number) => (i / (n - 1)) * (W - 6) + 3
  const ys = (v: number) => {
    const t = (v - ymin) / Math.max(1e-9, (ymax - ymin))
    return (1 - Math.min(1, Math.max(0, t))) * (H - 6) + 3
  }
  const pts: string[] = []
  for (let i = 0; i < n; i++) pts.push(`${xs(i)},${ys(values[i])}`)
  return pts.join(' ')
}

const powerPolyline = computed(() => sparklinePoints(timeseries.value.map(r => r.power_w), Math.min(minP.value, 0), Math.max(maxP.value, 1)))
const feedPolyline  = computed(() => sparklinePoints(timeseries.value.map(r => r.feed_u_per_min), Math.min(minF.value, 0), Math.max(maxF.value, 1)))

/* downloads */
function blobSave (filename: string, text: string, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadJSON () {
  if (!props.metrics) return
  blobSave('sim_metrics.json', JSON.stringify(props.metrics, null, 2), 'application/json;charset=utf-8')
}

function downloadCSV () {
  if (!hasTS.value) return
  const rows = [
    ['idx','code','length_mm','feed_units_per_min','time_s','power_w','energy_j'].join(',')
  ]
  for (const r of timeseries.value) {
    rows.push([r.idx, r.code, r.length_mm, r.feed_u_per_min, r.time_s, r.power_w, r.energy_j].join(','))
  }
  blobSave('sim_timeseries.csv', rows.join('\n'), 'text/csv;charset=utf-8')
}

function downloadMarkdown () {
  const m = props.metrics
  if (!m) return
  const md = `# Simulation Report

**Units:** ${m.units}

| Metric | Value |
|---|---:|
| Total time (s) | ${fmt(m.total_time_s,2)} |
| Total length (mm) | ${fmt(m.total_length_mm,2)} |
| Peak power (W) | ${fmt(m.peak_power_w,0)} |
| Mean power (W) | ${fmt(m.mean_power_w,0)} |
| Total energy (J) | ${fmt(m.total_energy_j,0)} |
| Chip energy (J) | ${fmt(m.chip_energy_j,0)} |
| Tool energy (J) | ${fmt(m.tool_energy_j,0)} |
| Work energy (J) | ${fmt(m.work_energy_j,0)} |
| Feed limited (%) | ${fmt(m.feed_limited_pct,1)} |

> Export CSV for per-segment details.
`
  blobSave('sim_report.md', md, 'text/markdown;charset=utf-8')
}
</script>
