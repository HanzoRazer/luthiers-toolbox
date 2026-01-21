<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import axios from 'axios';

type ArtPreset = {
  id: string;
  lane: string;
  name: string;
  params: Record<string, any>;
  created_at: number;
};

const filters = reactive({
  lane: '',
});

const presets = ref<ArtPreset[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const form = reactive({
  lane: 'rosette',
  name: '',
  paramsText: '{}',
});

const createLoading = ref(false);
const createError = ref<string | null>(null);

async function loadPresets() {
  loading.value = true;
  error.value = null;
  try {
    const params: Record<string, any> = {};
    if (filters.lane.trim()) {
      params.lane = filters.lane.trim();
    }
    const { data } = await axios.get('/api/art/presets', { params });
    presets.value = data || [];
  } catch (err: any) {
    error.value = err?.message || 'Failed to load presets.';
  } finally {
    loading.value = false;
  }
}

async function createPreset() {
  createLoading.value = true;
  createError.value = null;
  try {
    let paramsObj: Record<string, any> = {};
    try {
      paramsObj = JSON.parse(form.paramsText || '{}');
    } catch {
      throw new Error('Params must be valid JSON.');
    }

    const payload = {
      lane: form.lane,
      name: form.name.trim() || 'Untitled Preset',
      params: paramsObj,
    };

    await axios.post('/api/art/presets', payload);
    form.name = '';
    form.paramsText = '{}';
    await loadPresets();
  } catch (err: any) {
    createError.value = err?.message || 'Failed to create preset.';
  } finally {
    createLoading.value = false;
  }
}

async function deletePreset(preset: ArtPreset) {
  if (!confirm(`Delete preset "${preset.name}"?`)) return;
  try {
    await axios.delete(`/api/art/presets/${preset.id}`);
    await loadPresets();
  } catch (err: any) {
    alert(err?.message || 'Failed to delete preset.');
  }
}

const groupedByLane = computed(() => {
  const out: Record<string, ArtPreset[]> = {};
  for (const preset of presets.value) {
    const lane = preset.lane || 'unknown';
    if (!out[lane]) {
      out[lane] = [];
    }
    out[lane].push(preset);
  }
  return out;
});

function fmtDate(ts: number) {
  if (!ts) return '—';
  return new Date(ts * 1000).toLocaleString();
}

onMounted(loadPresets);
</script>

<template>
  <div class="p-4 text-xs flex flex-col gap-4">
    <header>
      <h1 class="text-sm font-semibold text-gray-900">
        Art Studio Preset Manager
      </h1>
      <p class="text-[11px] text-gray-600">
        Create and manage presets shared across Rosette, Adaptive, and Relief lanes.
      </p>
    </header>

    <section class="rounded border bg-white p-3 space-y-2">
      <h2 class="text-xs font-semibold text-gray-900">
        Create preset
      </h2>
      <div class="flex flex-wrap gap-3 items-end">
        <div class="flex flex-col">
          <label class="text-[11px] text-gray-600">Lane</label>
          <select
            v-model="form.lane"
            class="border rounded px-2 py-1 text-xs bg-white"
          >
            <option value="rosette">
              rosette
            </option>
            <option value="adaptive">
              adaptive
            </option>
            <option value="relief">
              relief
            </option>
            <option value="all">
              all
            </option>
          </select>
        </div>
        <div class="flex flex-col min-w-[220px]">
          <label class="text-[11px] text-gray-600">Name</label>
          <input
            v-model="form.name"
            placeholder="e.g. &quot;GRBL Safe&quot;"
            class="border rounded px-2 py-1 text-xs"
          >
        </div>
      </div>
      <div class="flex flex-col">
        <label class="text-[11px] text-gray-600">Params (JSON)</label>
        <textarea
          v-model="form.paramsText"
          rows="4"
          class="border rounded px-2 py-1 text-[11px] font-mono bg-gray-50"
        />
      </div>
      <div class="flex items-center gap-2">
        <button
          class="rounded bg-sky-600 text-white px-3 py-1 hover:bg-sky-700 disabled:opacity-50"
          :disabled="createLoading"
          @click="createPreset"
        >
          <span v-if="!createLoading">Create</span>
          <span v-else>Creating…</span>
        </button>
        <span
          v-if="createError"
          class="text-red-600 text-[11px]"
        >{{ createError }}</span>
      </div>
    </section>

    <section class="rounded border bg-white p-3 space-y-2">
      <div class="flex flex-wrap gap-3 items-end">
        <div class="flex flex-col">
          <label class="text-[11px] text-gray-600">Filter lane</label>
          <input
            v-model="filters.lane"
            placeholder="rosette / adaptive / relief / all"
            class="border rounded px-2 py-1 text-xs"
          >
        </div>
        <button
          class="rounded border bg-gray-50 px-3 py-1 hover:bg-gray-100"
          :disabled="loading"
          @click="loadPresets"
        >
          Refresh list
        </button>
        <span
          v-if="error"
          class="text-red-600 text-[11px]"
        >{{ error }}</span>
      </div>
    </section>

    <section class="rounded border bg-white p-3">
      <div
        v-if="loading"
        class="text-gray-500"
      >
        Loading…
      </div>
      <div
        v-else-if="presets.length === 0"
        class="text-gray-500"
      >
        No presets found.
      </div>
      <div
        v-else
        class="space-y-3"
      >
        <div
          v-for="(rows, lane) in groupedByLane"
          :key="lane"
          class="border rounded"
        >
          <div class="p-2 font-semibold bg-gray-50">
            {{ lane }}
          </div>
          <div class="divide-y">
            <div
              v-for="preset in rows"
              :key="preset.id"
              class="p-2 flex flex-wrap justify-between items-center gap-2"
            >
              <div>
                <div class="font-semibold">
                  {{ preset.name }}
                </div>
                <div class="text-[10px] text-gray-500">
                  {{ fmtDate(preset.created_at) }}
                </div>
                <pre class="text-[10px] bg-gray-50 p-1 rounded border mt-1 max-w-xl overflow-auto">
{{ JSON.stringify(preset.params, null, 2) }}
                </pre>
              </div>
              <button
                class="text-[11px] text-red-600 hover:underline"
                @click="deletePreset(preset)"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
