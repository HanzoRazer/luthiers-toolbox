<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

type ArtJob = {
  id: string;
  lane: string;
  created_at: number;
  payload: Record<string, any>;
};

const router = useRouter();

const filters = reactive({
  lane: '',
  limit: 200,
});

const jobs = ref<ArtJob[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const latestRiskIndex = ref<Record<string, any>>({});

async function loadJobs() {
  loading.value = true;
  error.value = null;
  try {
    const params: Record<string, any> = { limit: filters.limit };
    if (filters.lane.trim()) {
      params.lane = filters.lane.trim();
    }
    const { data } = await axios.get('/api/art/jobs', { params });
    jobs.value = data || [];

    const ids = jobs.value.map((job) => job.id).filter(Boolean);
    if (ids.length) {
      const riskResp = await axios.get('/api/cam/risk/reports_index', {
        params: ids.map((id) => ['job_ids', id]),
      });
      latestRiskIndex.value = riskResp.data || {};
    } else {
      latestRiskIndex.value = {};
    }
  } catch (err: any) {
    error.value = err?.message || 'Failed to load jobs.';
  } finally {
    loading.value = false;
  }
}

function riskForJob(jobId: string) {
  return latestRiskIndex.value?.[jobId] || null;
}

function goJob(job: ArtJob) {
  router.push(`/art/job/${job.id}`);
}

function goLab(job: ArtJob) {
  router.push({
    path: `/art/${job.lane}`,
    query: { job_id: job.id },
  });
}

function goPipeline(job: ArtJob) {
  router.push({
    path: '/lab/pipeline',
    query: { lane: job.lane, job_id: job.id },
  });
}

function goRisk(job: ArtJob) {
  router.push({
    path: '/lab/risk',
    query: { job_id: job.id, lane: job.lane },
  });
}

onMounted(loadJobs);
</script>

<template>
  <div class="p-4 text-xs flex flex-col gap-4">
    <header>
      <h1 class="text-sm font-semibold text-gray-900">Art Studio — Job Timeline</h1>
      <p class="text-[11px] text-gray-600">
        Aggregated job history across Rosette, Adaptive, and Relief lanes.
      </p>
    </header>

    <section class="rounded border bg-white p-3 space-y-2">
      <div class="flex flex-wrap gap-4 items-end">
        <div class="flex flex-col">
          <label class="text-[11px] text-gray-600">Lane</label>
          <input
            v-model="filters.lane"
            placeholder="rosette / adaptive / relief"
            class="border rounded px-2 py-1 text-xs"
          />
        </div>

        <div class="flex flex-col">
          <label class="text-[11px] text-gray-600">Limit</label>
          <input
            v-model.number="filters.limit"
            type="number"
            min="1"
            max="500"
            class="border rounded px-2 py-1 text-xs"
          />
        </div>

        <button
          class="rounded bg-sky-600 text-white px-3 py-1 hover:bg-sky-700"
          :disabled="loading"
          @click="loadJobs"
        >
          <span v-if="!loading">Refresh</span>
          <span v-else>Loading…</span>
        </button>

        <span v-if="error" class="text-red-600">{{ error }}</span>
      </div>
    </section>

    <section class="rounded border bg-white p-3">
      <div v-if="jobs.length === 0" class="text-gray-500">No jobs found.</div>

      <div v-else class="space-y-2">
        <div
          v-for="job in jobs"
          :key="job.id"
          class="rounded border bg-gray-50 p-2 flex flex-col gap-2 hover:bg-gray-100"
        >
          <div class="flex justify-between items-center">
            <div>
              <span class="font-semibold">{{ job.lane }}</span>
              <span class="mx-1 text-gray-400">·</span>
              <span class="font-mono">{{ job.id }}</span>
            </div>
            <div class="text-[11px] text-gray-500">
              {{ new Date(job.created_at * 1000).toLocaleString() }}
            </div>
          </div>

          <div v-if="riskForJob(job.id)" class="text-[11px] flex flex-wrap gap-2 items-center">
            <span class="rounded-full px-2 py-0.5 bg-emerald-100 text-emerald-800">
              Risk saved
            </span>
            <span class="text-gray-700">
              len:
              <span class="font-mono">
                {{
                  riskForJob(job.id).summary?.total_length?.toFixed?.(1)
                    ?? riskForJob(job.id).summary?.total_length
                    ?? '—'
                }}
              </span>
            </span>
            <span class="text-gray-700">
              lines:
              <span class="font-mono">
                {{ riskForJob(job.id).summary?.total_lines ?? '—' }}
              </span>
            </span>
            <span class="text-gray-700">
              steps:
              <span class="font-mono">
                {{ riskForJob(job.id).summary?.steps_count ?? '—' }}
              </span>
            </span>
            <button
              class="rounded border px-2 py-0.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-800"
              @click="goRisk(job)"
            >
              View risk
            </button>
          </div>
          <div v-else class="text-[11px] text-gray-400">No risk snapshot yet</div>

          <div class="flex flex-wrap gap-2 text-[11px]">
            <button
              class="rounded border px-2 py-1 bg-sky-50 hover:bg-sky-100 text-sky-700"
              @click="goJob(job)"
            >
              Inspect Job
            </button>
            <button
              class="rounded border px-2 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700"
              @click="goLab(job)"
            >
              Open in Lab
            </button>
            <button
              class="rounded border px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700"
              @click="goPipeline(job)"
            >
              Open in PipelineLab
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
