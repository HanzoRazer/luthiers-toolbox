<!-- File: client/src/components/cam/JobIntHistoryPanel.vue -->
<!-- NEW – Job Intelligence history panel with stats header, filters, and pagination -->

<template>
  <div class="flex flex-col h-full text-xs gap-3">
    <header class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-semibold">Job Intelligence History</h3>
        <p class="text-[11px] text-gray-500">
          Recent pipeline runs with sim time, energy, and deviation.
        </p>
      </div>

      <button
        type="button"
        class="px-2 py-1 rounded border border-slate-300 text-[11px] hover:bg-slate-50"
        @click="reload"
      >
        Reload
      </button>
    </header>

    <!-- Quick Stats Header -->
    <section class="border rounded-lg p-2 bg-white flex flex-col gap-1 text-[11px]">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Current page:</span>
          <span class="font-mono">{{ items.length }}</span>
          <span class="text-gray-400">jobs</span>
        </div>

        <div class="flex items-center gap-2">
          <span
            class="px-2 py-0.5 rounded-full border text-[10px] border-emerald-200 bg-emerald-50 text-emerald-700"
          >
            Helical:
            <span class="font-mono">
              {{ helicalCount }} ({{ helicalPct.toFixed(0) }}%)
            </span>
          </span>
          <span
            class="px-2 py-0.5 rounded-full border text-[10px] border-slate-200 bg-slate-50 text-slate-700"
          >
            Non-helical:
            <span class="font-mono">
              {{ nonHelicalCount }} ({{ nonHelicalPct.toFixed(0) }}%)
            </span>
          </span>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1">
            <span class="text-gray-500">Avg time:</span>
            <span class="font-mono">
              {{ avgTimeLabel }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span class="text-gray-500">Avg max dev:</span>
            <span class="font-mono">
              <span v-if="avgMaxDevPct != null">
                {{ avgMaxDevPct.toFixed(1) }}%
              </span>
              <span v-else>—</span>
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Filters -->
    <section class="border rounded-lg p-2 bg-slate-50 flex flex-col gap-2">
      <div class="grid grid-cols-3 gap-2 text-[11px]">
        <label class="flex flex-col gap-1">
          <span>Machine</span>
          <input
            v-model="filters.machine_id"
            type="text"
            class="border rounded px-2 py-1"
            placeholder="haas_vf2, shopbot, ..."
          />
        </label>

        <label class="flex flex-col gap-1">
          <span>Post</span>
          <input
            v-model="filters.post_id"
            type="text"
            class="border rounded px-2 py-1"
            placeholder="haas_ngc, grbl, ..."
          />
        </label>

        <div class="flex flex-col gap-1 mt-1">
          <label class="flex items-center gap-2">
            <input
              v-model="filters.helical_only"
              type="checkbox"
              class="w-3 h-3"
            />
            <span>Helical only</span>
          </label>

          <label class="flex items-center gap-2">
            <input
              v-model="filters.favorites_only"
              type="checkbox"
              class="w-3 h-3"
            />
            <span>⭐ Favorites only</span>
          </label>
        </div>
      </div>

      <div class="flex items-center gap-2 text-[11px]">
        <label class="flex items-center gap-2">
          <input
            v-model="filters.favorites_only"
            type="checkbox"
            class="w-3 h-3"
          />
          <span>⭐ Favorites only</span>
        </label>
      </div>

      <div class="flex items-center justify-between mt-1 text-[11px]">
        <span class="text-gray-500">
          Total:
          <span class="font-mono">{{ total }}</span>
        </span>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100"
            @click="applyFilters"
          >
            Apply
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>
    </section>

    <!-- Table -->
    <section class="flex-1 border rounded-lg overflow-hidden flex flex-col">
      <div class="border-b bg-slate-50 px-2 py-1 text-[11px] font-semibold flex">
        <div class="w-[22%]">Job</div>
        <div class="w-[12%]">Machine</div>
        <div class="w-[12%]">Post</div>
        <div class="w-[9%] text-center">Helical</div>
        <div class="w-[12%] text-right">Time</div>
        <div class="w-[9%] text-right">Issues</div>
        <div class="w-[9%] text-right">Max dev</div>
        <div class="w-[15%] text-right pr-1">Actions</div>
      </div>

      <div class="flex-1 overflow-auto">
        <div
          v-for="entry in items"
          :key="entry.run_id"
          class="px-2 py-1 text-[11px] flex items-center border-b hover:bg-slate-50"
        >
          <div class="w-[22%] truncate">
            <div class="flex items-center gap-1">
              <button
                type="button"
                class="text-[12px] leading-none"
                @click.stop="toggleFavorite(entry)"
                :title="entry.favorite ? 'Unmark favorite' : 'Mark as favorite'"
              >
                <span v-if="entry.favorite">⭐</span>
                <span v-else>☆</span>
              </button>
              <div class="truncate flex-1 cursor-pointer" @click="selectEntry(entry)">
                <div class="font-semibold">
                  {{ entry.job_name || "(unnamed job)" }}
                </div>
                <div class="text-[10px] text-gray-500">
                  {{ entry.run_id }}
                </div>
              </div>
            </div>
          </div>

          <div class="w-[12%] truncate">
            {{ entry.machine_id || "—" }}
          </div>

          <div class="w-[12%] truncate">
            {{ entry.post_id || "—" }}
          </div>

          <div class="w-[9%] text-center">
            <span
              :class="[
                'px-2 py-0.5 rounded-full text-[10px]',
                entry.use_helical
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-slate-50 text-slate-500 border border-slate-200',
              ]"
            >
              {{ entry.use_helical ? "Yes" : "No" }}
            </span>
          </div>

          <div class="w-[12%] text-right font-mono">
            {{ formatTime(entry.sim_time_s) }}
          </div>

          <div class="w-[9%] text-right font-mono">
            {{ entry.sim_issue_count ?? 0 }}
          </div>

          <div class="w-[9%] text-right font-mono">
            <span v-if="entry.sim_max_dev_pct != null">
              {{ entry.sim_max_dev_pct.toFixed(1) }}%
            </span>
            <span v-else>—</span>
          </div>

          <div class="w-[15%] text-right pr-1">
            <button
              type="button"
              class="px-2 py-1 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 text-[10px]"
              @click.stop="openCloneModal(entry)"
              title="Clone as preset (B19)"
            >
              📋 Clone
            </button>
          </div>
        </div>

        <div
          v-if="!loading && items.length === 0"
          class="px-3 py-4 text-[11px] text-gray-400"
        >
          No jobs found. Run a pipeline or relax the filters.
        </div>
      </div>

      <div class="border-t px-2 py-1 flex items-center justify-between text-[11px] bg-slate-50">
        <span class="text-gray-500">
          Showing
          <span class="font-mono">{{ items.length }}</span>
          of
          <span class="font-mono">{{ total }}</span>
        </span>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-40"
            :disabled="offset === 0 || loading"
            @click="prevPage"
          >
            Prev
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-40"
            :disabled="offset + limit >= total || loading"
            @click="nextPage"
          >
            Next
          </button>
        </div>
      </div>
    </section>

    <p v-if="errorMessage" class="text-[11px] text-rose-600">
      {{ errorMessage }}
    </p>

    <!-- Clone as Preset Modal -->
    <div
      v-if="showCloneModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      @click.self="closeCloneModal"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div class="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h3 class="text-sm font-semibold">📋 Clone Job as Preset (B19)</h3>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 text-lg leading-none"
            @click="closeCloneModal"
          >
            ✕
          </button>
        </div>

        <div class="p-4">
          <div v-if="selectedEntry" class="flex flex-col gap-3 text-xs">
            <!-- Source Job Info -->
            <div class="p-3 bg-slate-50 rounded border">
              <div class="font-semibold mb-2">Source Job</div>
              <div class="grid grid-cols-2 gap-2 text-[11px]">
                <div><span class="text-gray-500">Job:</span> {{ selectedEntry.job_name || '(unnamed)' }}</div>
                <div><span class="text-gray-500">Run ID:</span> <span class="font-mono">{{ selectedEntry.run_id }}</span></div>
                <div><span class="text-gray-500">Machine:</span> {{ selectedEntry.machine_id || '—' }}</div>
                <div><span class="text-gray-500">Post:</span> {{ selectedEntry.post_id || '—' }}</div>
                <div><span class="text-gray-500">Time:</span> {{ formatTime(selectedEntry.sim_time_s) }}</div>
                <div><span class="text-gray-500">Helical:</span> {{ selectedEntry.use_helical ? 'Yes' : 'No' }}</div>
              </div>
            </div>

            <!-- Preset Configuration -->
            <div class="flex flex-col gap-2">
              <label class="flex flex-col gap-1">
                <span class="font-semibold">Preset Name *</span>
                <input
                  v-model="cloneForm.name"
                  type="text"
                  class="border rounded px-2 py-1"
                  placeholder="e.g., Helical Pocket - VF2 - GRBL"
                />
              </label>

              <label class="flex flex-col gap-1">
                <span class="font-semibold">Description</span>
                <textarea
                  v-model="cloneForm.description"
                  class="border rounded px-2 py-1 h-16"
                  placeholder="Optional description of this preset..."
                ></textarea>
              </label>

              <div class="grid grid-cols-2 gap-2">
                <label class="flex flex-col gap-1">
                  <span class="font-semibold">Preset Kind</span>
                  <select v-model="cloneForm.kind" class="border rounded px-2 py-1">
                    <option value="cam">CAM</option>
                    <option value="combo">Combo (CAM + Export)</option>
                  </select>
                </label>

                <label class="flex flex-col gap-1">
                  <span class="font-semibold">Tags</span>
                  <input
                    v-model="cloneForm.tagsInput"
                    type="text"
                    class="border rounded px-2 py-1"
                    placeholder="helical, production, test"
                  />
                  <span class="text-[10px] text-gray-500">Comma-separated</span>
                </label>
              </div>
            </div>

            <!-- CAM Parameters Preview (from job) -->
            <div class="p-3 bg-blue-50 rounded border border-blue-200">
              <div class="font-semibold mb-2">CAM Parameters (auto-filled from job)</div>
              <div class="grid grid-cols-2 gap-2 text-[11px]">
                <div><span class="text-gray-600">Machine:</span> {{ selectedEntry.machine_id || 'Not specified' }}</div>
                <div><span class="text-gray-600">Post:</span> {{ selectedEntry.post_id || 'Not specified' }}</div>
                <div><span class="text-gray-600">Strategy:</span> {{ cloneForm.cam_params?.strategy || 'Spiral (default)' }}</div>
                <div><span class="text-gray-600">Helical:</span> {{ selectedEntry.use_helical ? 'Enabled' : 'Disabled' }}</div>
              </div>
              <p class="text-[10px] text-blue-700 mt-2">ℹ Full CAM params will be loaded from job detail on save</p>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-2 pt-2 border-t">
              <button
                type="button"
                class="px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50"
                @click="closeCloneModal"
              >
                Cancel
              </button>
              <button
                type="button"
                class="px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                @click="executeClone"
                :disabled="!cloneForm.name || cloning"
              >
                {{ cloning ? '⏳ Cloning...' : '📋 Create Preset' }}
              </button>
            </div>

            <!-- Success/Error Messages -->
            <div v-if="cloneSuccess" class="p-2 bg-green-50 border border-green-200 rounded text-green-700 text-[11px]">
              ✅ Preset created successfully! <a :href="`#/lab/preset-hub`" class="underline">View in Preset Hub →</a>
            </div>
            <div v-if="cloneError" class="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-[11px]">
              ❌ {{ cloneError }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from "vue";
import {
  fetchJobIntLog,
  updateJobIntFavorite,
  type JobIntLogEntry,
  type JobIntLogListResponse,
} from "@/api/job_int";

const items = ref<JobIntLogEntry[]>([]);
const total = ref(0);
const loading = ref(false);
const errorMessage = ref<string | null>(null);

const filters = reactive({
  machine_id: "",
  post_id: "",
  helical_only: false,
  favorites_only: false,
});

const limit = ref(50);
const offset = ref(0);

// Clone modal state
const showCloneModal = ref(false);
const selectedEntry = ref<JobIntLogEntry | null>(null);
const cloning = ref(false);
const cloneSuccess = ref(false);
const cloneError = ref<string | null>(null);
const cloneForm = reactive({
  name: '',
  description: '',
  kind: 'cam' as 'cam' | 'combo',
  tagsInput: '',
  cam_params: {} as Record<string, any>,
});

// Stats computed properties
const helicalCount = computed(() => {
  return items.value.filter((e) => e.use_helical).length;
});

const nonHelicalCount = computed(() => {
  return items.value.filter((e) => !e.use_helical).length;
});

const helicalPct = computed(() => {
  if (items.value.length === 0) return 0;
  return (helicalCount.value / items.value.length) * 100;
});

const nonHelicalPct = computed(() => {
  if (items.value.length === 0) return 0;
  return (nonHelicalCount.value / items.value.length) * 100;
});

const avgTimeSeconds = computed(() => {
  const vals = items.value
    .map((e) => e.sim_time_s)
    .filter((v): v is number => v != null && !Number.isNaN(v));
  if (vals.length === 0) return null;
  const sum = vals.reduce((a, b) => a + b, 0);
  return sum / vals.length;
});

const avgTimeLabel = computed(() => {
  const v = avgTimeSeconds.value;
  if (v == null) return "—";
  if (v < 1) return `${(v * 1000).toFixed(0)} ms`;
  if (v < 60) return `${v.toFixed(2)} s`;
  const m = Math.floor(v / 60);
  const s = v - m * 60;
  return `${m}m ${s.toFixed(0)}s`;
});

const avgMaxDevPct = computed(() => {
  const vals = items.value
    .map((e) => e.sim_max_dev_pct)
    .filter((v): v is number => v != null && !Number.isNaN(v));
  if (vals.length === 0) return null;
  const sum = vals.reduce((a, b) => a + b, 0);
  return sum / vals.length;
});

// Load function
async function load() {
  loading.value = true;
  errorMessage.value = null;

  try {
    const res: JobIntLogListResponse = await fetchJobIntLog({
      machine_id: filters.machine_id || undefined,
      post_id: filters.post_id || undefined,
      helical_only: filters.helical_only || undefined,
      favorites_only: filters.favorites_only || undefined,
      limit: limit.value,
      offset: offset.value,
    });
    items.value = res.items;
    total.value = res.total;
  } catch (err: any) {
    console.error("JobIntHistory load error", err);
    errorMessage.value = err?.message ?? "Failed to load job history.";
  } finally {
    loading.value = false;
  }
}

function reload() {
  offset.value = 0;
  load();
}

function applyFilters() {
  offset.value = 0;
  load();
}

function resetFilters() {
  filters.machine_id = "";
  filters.post_id = "";
  filters.helical_only = false;
  filters.favorites_only = false;
  offset.value = 0;
  load();
}

function prevPage() {
  if (offset.value >= limit.value) {
    offset.value -= limit.value;
    load();
  }
}

function nextPage() {
  if (offset.value + limit.value < total.value) {
    offset.value += limit.value;
    load();
  }
}

function selectEntry(entry: JobIntLogEntry) {
  console.log("Selected job:", entry.run_id);
  // TODO: Open detail modal or navigate to detail view
}

async function toggleFavorite(entry: JobIntLogEntry) {
  const target = !entry.favorite;
  try {
    const detail = await updateJobIntFavorite(entry.run_id, target);
    // Prefer server's value, but fallback to requested target
    entry.favorite = detail.favorite ?? target;
    errorMessage.value = null;
  } catch (err: any) {
    console.error("Failed to update favorite", err);
    errorMessage.value =
      err?.message ?? "Failed to update favorite flag for this job.";
  }
}

function openCloneModal(entry: JobIntLogEntry) {
  selectedEntry.value = entry;
  cloneForm.name = `${entry.job_name || 'Job'} - ${entry.machine_id || 'Machine'}`;
  cloneForm.description = `Cloned from job run ${entry.run_id.slice(0, 8)} on ${new Date().toLocaleDateString()}`;
  cloneForm.kind = 'cam';
  cloneForm.tagsInput = entry.use_helical ? 'helical, cloned' : 'cloned';
  cloneSuccess.value = false;
  cloneError.value = null;
  showCloneModal.value = true;
}

function closeCloneModal() {
  showCloneModal.value = false;
  selectedEntry.value = null;
  cloneForm.name = '';
  cloneForm.description = '';
  cloneForm.tagsInput = '';
  cloneSuccess.value = false;
  cloneError.value = null;
}

async function executeClone() {
  if (!selectedEntry.value || !cloneForm.name) return;
  
  cloning.value = true;
  cloneError.value = null;
  cloneSuccess.value = false;
  
  try {
    // First fetch detailed job data
    const detailResponse = await fetch(`/api/cam/job-int/log/${encodeURIComponent(selectedEntry.value.run_id)}`);
    if (!detailResponse.ok) {
      throw new Error(`Failed to fetch job details: ${detailResponse.statusText}`);
    }
    const jobDetail = await detailResponse.json();
    
    // Build preset payload
    const tags = cloneForm.tagsInput
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0);
    
    const presetPayload = {
      name: cloneForm.name,
      kind: cloneForm.kind,
      description: cloneForm.description,
      tags: tags,
      machine_id: selectedEntry.value.machine_id || null,
      post_id: selectedEntry.value.post_id || null,
      units: 'mm', // Default, could be extracted from job if available
      job_source_id: selectedEntry.value.run_id,
      cam_params: {
        strategy: 'Spiral', // Default, could be extracted from job
        use_helical: selectedEntry.value.use_helical,
        // Add more params from jobDetail.sim_stats if available
        ...(jobDetail.sim_stats || {}),
      },
    };
    
    // Create preset via API
    const createResponse = await fetch('/api/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(presetPayload),
    });
    
    if (!createResponse.ok) {
      const errorData = await createResponse.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create preset: ${createResponse.statusText}`);
    }
    
    cloneSuccess.value = true;
    
    // Auto-close after 2 seconds on success
    setTimeout(() => {
      closeCloneModal();
    }, 2000);
    
  } catch (err: any) {
    console.error('Clone preset error:', err);
    cloneError.value = err?.message || 'Failed to clone job as preset';
  } finally {
    cloning.value = false;
  }
}

function formatTime(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`;
  if (seconds < 60) return `${seconds.toFixed(2)} s`;
  const m = Math.floor(seconds / 60);
  const s = seconds - m * 60;
  return `${m}m ${s.toFixed(0)}s`;
}

onMounted(load);
</script>
