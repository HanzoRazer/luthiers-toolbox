<template>
  <div class="p-4 space-y-4 text-xs" v-if="analytics">
    <!-- GLOBAL SUMMARY -->
    <section class="border rounded p-3 bg-white space-y-1">
      <h2 class="text-sm font-semibold">Global RMOS Risk</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div>
          <div class="text-[11px] text-gray-500">Total jobs</div>
          <div class="text-sm font-semibold">{{ analytics.global_summary.total_jobs }}</div>
        </div>
        <div>
          <div class="text-[11px] text-gray-500">Total presets</div>
          <div class="text-sm font-semibold">{{ analytics.global_summary.total_presets }}</div>
        </div>
        <div>
          <div class="text-[11px] text-gray-500">Avg risk score</div>
          <div class="text-sm font-semibold">
            {{ formatNumber(analytics.global_summary.avg_risk_score) }}
          </div>
        </div>
        <div>
          <div class="text-[11px] text-gray-500">Overall fragility</div>
          <div class="text-sm font-semibold" :class="fragilityColorClass(analytics.global_summary.overall_fragility_score)">
            {{ formatNumber(analytics.global_summary.overall_fragility_score) }}
          </div>
        </div>
      </div>
      
      <!-- Grade counts badges -->
      <div class="flex gap-2 pt-2">
        <div v-for="(count, grade) in analytics.global_summary.grade_counts" :key="grade" 
             class="px-2 py-1 rounded text-[10px] font-mono"
             :class="gradeColorClass(grade as RiskGrade)">
          {{ grade }}: {{ count }}
        </div>
      </div>
    </section>

    <!-- MATERIAL RISK GLOBAL -->
    <section class="border rounded p-3 bg-white space-y-2">
      <h2 class="text-sm font-semibold">Material Risk (Global)</h2>
      <div class="max-h-44 overflow-auto">
        <table class="w-full border-collapse text-[11px]">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">Material type</th>
              <th class="text-right p-1">Jobs</th>
              <th class="text-right p-1">Avg fragility</th>
              <th class="text-right p-1">Worst fragility</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="m in analytics.material_risk_global"
              :key="m.material_type"
              class="border-b last:border-0 hover:bg-gray-50"
            >
              <td class="p-1 font-mono">{{ m.material_type }}</td>
              <td class="p-1 text-right">{{ m.job_count }}</td>
              <td class="p-1 text-right" :class="fragilityColorClass(m.avg_fragility)">
                {{ formatNumber(m.avg_fragility) }}
              </td>
              <td class="p-1 text-right font-semibold" :class="fragilityColorClass(m.worst_fragility)">
                {{ formatNumber(m.worst_fragility) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-[11px] text-gray-500 pt-1">
        Fragility scores near 1.0 indicate brittle or delicate combinations (shell, metals, charred wood).
      </p>
    </section>

    <!-- LANE SUMMARIES -->
    <section class="border rounded p-3 bg-white space-y-2">
      <h2 class="text-sm font-semibold">Lane Risk & Materials</h2>
      <div class="max-h-56 overflow-auto">
        <table class="w-full border-collapse text-[11px]">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">Lane</th>
              <th class="text-right p-1">Jobs</th>
              <th class="text-right p-1">Avg risk</th>
              <th class="text-right p-1">Avg fragility</th>
              <th class="text-left p-1">Top materials</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="lane in analytics.lane_summaries"
              :key="lane.lane"
              class="border-b last:border-0 hover:bg-gray-50"
            >
              <td class="p-1 font-mono">{{ lane.lane }}</td>
              <td class="p-1 text-right">{{ lane.job_count }}</td>
              <td class="p-1 text-right">{{ formatNumber(lane.avg_risk_score) }}</td>
              <td class="p-1 text-right" :class="fragilityColorClass(lane.avg_fragility_score)">
                {{ formatNumber(lane.avg_fragility_score) }}
              </td>
              <td class="p-1">
                <span v-if="lane.dominant_material_types.length" class="font-mono text-[10px]">
                  {{ lane.dominant_material_types.join(', ') }}
                </span>
                <span v-else class="text-gray-400">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- LANE TRANSITIONS -->
    <section class="border rounded p-3 bg-white space-y-2" v-if="analytics.lane_transitions.length > 0">
      <h2 class="text-sm font-semibold">Lane Transitions</h2>
      <div class="max-h-40 overflow-auto">
        <table class="w-full border-collapse text-[11px]">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">From lane</th>
              <th class="text-left p-1">To lane</th>
              <th class="text-right p-1">Count</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(t, idx) in analytics.lane_transitions"
              :key="idx"
              class="border-b last:border-0"
            >
              <td class="p-1 font-mono">{{ t.from_lane }}</td>
              <td class="p-1 font-mono">{{ t.to_lane }}</td>
              <td class="p-1 text-right">{{ t.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- RECENT RUNS -->
    <section class="border rounded p-3 bg-white space-y-2">
      <h2 class="text-sm font-semibold">Recent Runs</h2>
      <div class="max-h-64 overflow-auto">
        <table class="w-full border-collapse text-[11px]">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">Time</th>
              <th class="text-left p-1">Preset</th>
              <th class="text-left p-1">Lane</th>
              <th class="text-left p-1">Job type</th>
              <th class="text-left p-1">Risk</th>
              <th class="text-right p-1">Fragility</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in analytics.recent_runs"
              :key="r.job_id"
              class="border-b last:border-0 hover:bg-gray-50"
            >
              <td class="p-1 font-mono truncate max-w-[120px]">{{ formatTimestamp(r.created_at) }}</td>
              <td class="p-1 font-mono text-[10px]">{{ r.preset_id || '—' }}</td>
              <td class="p-1 font-mono">{{ r.lane }}</td>
              <td class="p-1 text-[10px]">{{ r.job_type }}</td>
              <td class="p-1">
                <span class="px-1 rounded text-[9px] font-mono" :class="gradeColorClass(r.risk_grade)">
                  {{ r.risk_grade }}
                </span>
              </td>
              <td class="p-1 text-right" :class="fragilityColorClass(r.worst_fragility_score)">
                {{ formatNumber(r.worst_fragility_score) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <div v-else-if="loading" class="p-4 text-xs text-gray-500">
    Loading analytics data...
  </div>

  <div v-else-if="error" class="p-4 text-xs text-red-600">
    Error loading analytics: {{ error }}
  </div>

  <div v-else class="p-4 space-y-2">
    <p class="text-xs text-gray-500">No analytics data loaded yet.</p>
    <button 
      @click="store.fetchRiskAnalytics()"
      class="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
    >
      Load Analytics
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRmosAnalyticsStore } from '@/stores/useRmosAnalyticsStore';
import type { RiskGrade } from '@/models/rmos_analytics';

const store = useRmosAnalyticsStore();
const analytics = computed(() => store.riskAnalytics);
const loading = computed(() => store.loading);
const error = computed(() => store.error);

function formatNumber(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(2);
}

function formatTimestamp(ts: string): string {
  if (!ts) return '—';
  try {
    const date = new Date(ts);
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  } catch {
    return ts.substring(0, 16);
  }
}

function fragilityColorClass(score: number | null | undefined): string {
  if (score === null || score === undefined) return '';
  if (score >= 0.75) return 'text-red-600 font-semibold';
  if (score >= 0.50) return 'text-orange-600';
  if (score >= 0.30) return 'text-yellow-600';
  return 'text-green-600';
}

function gradeColorClass(grade: RiskGrade | string): string {
  switch (grade) {
    case 'GREEN':
      return 'bg-green-100 text-green-800';
    case 'YELLOW':
      return 'bg-yellow-100 text-yellow-800';
    case 'RED':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

onMounted(() => {
  if (!store.riskAnalytics) {
    store.fetchRiskAnalytics();
  }
});
</script>
