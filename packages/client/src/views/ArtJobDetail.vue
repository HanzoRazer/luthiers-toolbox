<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

const jobId = route.params.job_id as string;
const job = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function loadJob() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await axios.get(`/api/art/jobs/${jobId}`);
    if (data?.error) {
      error.value = data.error;
      job.value = null;
    } else {
      job.value = data;
    }
  } catch (err: any) {
    error.value = err?.message || 'Failed to load job.';
  } finally {
    loading.value = false;
  }
}

function goToLab() {
  if (!job.value) return;
  router.push({
    path: `/art/${job.value.lane}`,
    query: { job_id: job.value.id },
  });
}

function goToPipeline() {
  if (!job.value) return;
  router.push({
    path: '/lab/pipeline',
    query: { lane: job.value.lane, job_id: job.value.id },
  });
}

function goToRisk() {
  if (!job.value) return;
  router.push({
    path: '/lab/risk',
    query: { job_id: job.value.id },
  });
}

onMounted(loadJob);
</script>

<template>
  <div class="p-4 text-xs flex flex-col gap-4">
    <header>
      <h1 class="text-sm font-semibold text-gray-900">Art Studio Job Inspector</h1>
      <p class="text-[11px] text-gray-600">
        Job ID: <span class="font-mono">{{ jobId }}</span>
      </p>
    </header>

    <div v-if="loading" class="text-gray-500">Loading…</div>
    <div v-if="error" class="text-red-600">{{ error }}</div>

    <div v-if="job" class="space-y-4">
      <div class="rounded border bg-white p-3">
        <h2 class="font-semibold text-gray-900 text-xs mb-1">Metadata</h2>
        <p><strong>Lane:</strong> {{ job.lane }}</p>
        <p><strong>Created:</strong> {{ new Date(job.created_at * 1000).toLocaleString() }}</p>
      </div>

      <div class="rounded border bg-white p-3">
        <h2 class="font-semibold text-gray-900 text-xs mb-1">Payload</h2>
        <pre class="text-[10px] bg-gray-50 p-2 overflow-auto rounded border">
{{ JSON.stringify(job.payload, null, 2) }}
        </pre>
      </div>

      <div class="flex flex-wrap gap-2 text-[11px]">
        <button
          class="rounded bg-sky-600 text-white px-2 py-1 hover:bg-sky-700"
          @click="goToLab"
        >
          Open in Lab
        </button>
        <button
          class="rounded bg-amber-600 text-white px-2 py-1 hover:bg-amber-700"
          @click="goToPipeline"
        >
          Open in PipelineLab
        </button>
        <button
          class="rounded bg-indigo-600 text-white px-2 py-1 hover:bg-indigo-700"
          @click="goToRisk"
        >
          View in Risk Timeline
        </button>
      </div>
    </div>
  </div>
</template>
