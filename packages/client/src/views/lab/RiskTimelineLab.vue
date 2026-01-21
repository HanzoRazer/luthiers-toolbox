<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  getRecentRiskReports,
  type RiskReportSummary
} from '@/api/camRisk'

const loading = ref(false)
const errorMsg = ref<string | null>(null)
const reports = ref<RiskReportSummary[]>([])
const selectedReport = ref<RiskReportSummary | null>(null)

async function loadRecent() {
  loading.value = true
  errorMsg.value = null
  try {
    const data = await getRecentRiskReports(100)
    reports.value = data
    if (!selectedReport.value && data.length) {
      selectedReport.value = data[0]
    }
  } catch (err: any) {
    console.error(err)
    errorMsg.value = err?.message || 'Failed to load risk reports'
  } finally {
    loading.value = false
  }
}

function selectReport(row: RiskReportSummary) {
  selectedReport.value = row
}

onMounted(() => {
  loadRecent()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Risk Timeline Lab
      </h1>
      <p class="text-sm text-gray-600">
        Browse recent jobs and their CAM risk analytics: severity counts, risk score, and extra time.
      </p>
    </header>

    <section class="border rounded p-4 bg-white space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">
          Recent Risk Reports
        </h2>
        <button
          type="button"
          class="border rounded px-3 py-1 text-xs bg-white hover:bg-gray-100"
          :disabled="loading"
          @click="loadRecent"
        >
          {{ loading ? 'Reloading...' : 'Reload' }}
        </button>
      </div>

      <div
        v-if="errorMsg"
        class="text-xs text-red-600"
      >
        {{ errorMsg }}
      </div>

      <div
        v-if="!reports.length && !loading && !errorMsg"
        class="text-xs text-gray-500"
      >
        No risk reports found yet.
      </div>

      <div class="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1.5fr)]">
        <div class="border rounded bg-gray-50 overflow-auto max-h-[420px]">
          <table class="w-full text-[11px]">
            <thead class="bg-gray-100 border-b text-gray-600 sticky top-0">
              <tr>
                <th class="px-2 py-1 text-left">
                  When
                </th>
                <th class="px-2 py-1 text-left">
                  Job
                </th>
                <th class="px-2 py-1 text-right">
                  Risk
                </th>
                <th class="px-2 py-1 text-right">
                  Issues
                </th>
                <th class="px-2 py-1 text-right">
                  Crit
                </th>
                <th class="px-2 py-1 text-right">
                  H
                </th>
                <th class="px-2 py-1 text-right">
                  M
                </th>
                <th class="px-2 py-1 text-right">
                  L
                </th>
                <th class="px-2 py-1 text-right">
                  Time Δ (s)
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in reports"
                :key="row.id"
                class="border-b cursor-pointer"
                :class="{
                  'bg-white hover:bg-gray-50': selectedReport?.id !== row.id,
                  'bg-blue-50 hover:bg-blue-100': selectedReport?.id === row.id
                }"
                @click="selectReport(row)"
              >
                <td class="px-2 py-1">
                  {{ new Date(row.created_at).toLocaleString() }}
                </td>
                <td class="px-2 py-1">
                  <div class="flex flex-col">
                    <span class="font-semibold">{{ row.job_id }}</span>
                    <span class="text-[10px] text-gray-500">
                      {{ row.pipeline_id || '—' }} · {{ row.op_id || '—' }}
                    </span>
                  </div>
                </td>
                <td class="px-2 py-1 text-right tabular-nums">
                  {{ row.risk_score.toFixed(1) }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums">
                  {{ row.total_issues }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums text-red-600">
                  {{ row.critical_count }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums text-red-500">
                  {{ row.high_count }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums text-orange-500">
                  {{ row.medium_count }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums text-yellow-500">
                  {{ row.low_count }}
                </td>
                <td class="px-2 py-1 text-right tabular-nums">
                  {{ row.total_extra_time_s.toFixed(1) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="border rounded p-3 bg-gray-50 text-xs min-h-[200px]">
          <div
            v-if="!selectedReport"
            class="text-gray-500"
          >
            Select a row to see details.
          </div>

          <div
            v-else
            class="space-y-2"
          >
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-sm">
                Job: {{ selectedReport.job_id }}
              </h3>
              <span class="text-[10px] text-gray-500">
                {{ new Date(selectedReport.created_at).toLocaleString() }}
              </span>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div class="space-y-0.5">
                <div>
                  Risk score:
                  <span class="font-semibold">
                    {{ selectedReport.risk_score.toFixed(1) }}
                  </span>
                </div>
                <div>
                  Total issues:
                  <span class="font-semibold">
                    {{ selectedReport.total_issues }}
                  </span>
                </div>
                <div>
                  Extra time (s):
                  <span class="font-semibold">
                    {{ selectedReport.total_extra_time_s.toFixed(1) }}
                  </span>
                </div>
              </div>
              <div class="space-y-0.5">
                <div>
                  Crit:
                  <span class="font-semibold text-red-600">
                    {{ selectedReport.critical_count }}
                  </span>
                </div>
                <div>
                  High:
                  <span class="font-semibold text-red-500">
                    {{ selectedReport.high_count }}
                  </span>
                </div>
                <div>
                  Medium:
                  <span class="font-semibold text-orange-500">
                    {{ selectedReport.medium_count }}
                  </span>
                </div>
                <div>
                  Low:
                  <span class="font-semibold text-yellow-500">
                    {{ selectedReport.low_count }}
                  </span>
                </div>
              </div>
            </div>

            <div class="pt-2 border-t text-[10px] text-gray-600 space-y-1">
              <div>
                Pipeline:
                <span class="font-semibold">
                  {{ selectedReport.pipeline_id || '—' }}
                </span>
              </div>
              <div>
                Op:
                <span class="font-semibold">
                  {{ selectedReport.op_id || '—' }}
                </span>
              </div>
              <div>
                Machine:
                <span class="font-semibold">
                  {{ selectedReport.machine_profile_id || '—' }}
                </span>
              </div>
              <div>
                Post:
                <span class="font-semibold">
                  {{ selectedReport.post_preset || '—' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
