<template>
  <div class="p-4 flex flex-col gap-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div>
        <h1 class="text-base font-semibold text-gray-900">
          Art Studio · Rosette
        </h1>
        <p class="text-xs text-gray-600 max-w-xl">
          Design a rosette pattern, preview the geometry, and save jobs with presets.
          This MVP uses a simple ring stub geometry; later we can plug in the full
          Art Studio kernel without changing this UI.
        </p>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-gray-600">
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="refreshPresets"
        >
          Reload presets
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="refreshJobs"
        >
          Recent jobs
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="grid grid-cols-1 md:grid-cols-[280px,1fr] gap-4">
      <!-- Left: form -->
      <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-3 text-[11px] text-gray-800">
        <div>
          <label class="block text-[11px] font-semibold mb-1">Job name</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. OM_rosette_maple_001"
            class="w-full px-2 py-1 border rounded text-[11px]"
          />
        </div>

        <div>
          <label class="block text-[11px] font-semibold mb-1">Preset</label>
          <select
            v-model="form.preset"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option :value="''">(none)</option>
            <option
              v-for="p in presets"
              :key="p.name"
              :value="p.name"
            >
              {{ p.name }} · {{ p.pattern_type }} · {{ p.segments }} seg
            </option>
          </select>
          <p class="text-[10px] text-gray-500 mt-0.5" v-if="selectedPresetDescription">
            {{ selectedPresetDescription }}
          </p>
        </div>

        <div>
          <label class="block text-[11px] font-semibold mb-1">Pattern type</label>
          <select
            v-model="form.pattern_type"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="simple_ring">simple_ring (stub)</option>
            <option value="herringbone">herringbone (stub)</option>
            <option value="rope">rope (stub)</option>
          </select>
        </div>

        <div class="flex gap-2">
          <div class="flex-1">
            <label class="block text-[11px] font-semibold mb-1">Segments</label>
            <input
              v-model.number="form.segments"
              type="number"
              min="8"
              max="720"
              class="w-full px-2 py-1 border rounded text-[11px]"
            />
          </div>
          <div class="flex-1">
            <label class="block text-[11px] font-semibold mb-1">Inner radius</label>
            <input
              v-model.number="form.inner_radius"
              type="number"
              step="0.1"
              class="w-full px-2 py-1 border rounded text-[11px]"
            />
          </div>
          <div class="flex-1">
            <label class="block text-[11px] font-semibold mb-1">Outer radius</label>
            <input
              v-model.number="form.outer_radius"
              type="number"
              step="0.1"
              class="w-full px-2 py-1 border rounded text-[11px]"
            />
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-semibold mb-1">Units</label>
          <select
            v-model="form.units"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="mm">mm</option>
            <option value="inch">inch</option>
          </select>
        </div>

        <div class="flex flex-wrap gap-2 mt-2">
          <button
            class="px-3 py-1 rounded bg-indigo-600 text-white text-[11px] hover:bg-indigo-700 disabled:opacity-50"
            :disabled="previewLoading"
            @click="runPreview"
          >
            {{ previewLoading ? 'Previewing…' : 'Preview Rosette' }}
          </button>
          <button
            class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            :disabled="!preview || saveLoading"
            @click="saveJob"
          >
            {{ saveLoading ? 'Saving…' : 'Save Job' }}
          </button>
        </div>

        <p v-if="statusMessage" class="text-[10px] mt-1" :class="statusClass">
          {{ statusMessage }}
        </p>
      </div>

      <!-- Right: preview + jobs -->
      <div class="flex flex-col gap-3">
        <!-- Preview panel -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[12px] font-semibold text-gray-900">
                Geometry Preview
              </h2>
              <p class="text-[10px] text-gray-500">
                Simple SVG backplot of the returned paths. This is wired to
                <span class="font-mono">POST /api/art/rosette/preview</span>.
              </p>
            </div>
            <div class="text-[10px] text-gray-500">
              <div v-if="preview">
                Job: <span class="font-mono">{{ preview.job_id }}</span>
              </div>
            </div>
          </div>

          <div
            class="border rounded bg-gray-50 flex items-center justify-center"
            style="height: 260px;"
          >
            <div v-if="preview && preview.paths.length" class="w-full h-full">
              <svg
                :viewBox="svgViewBox"
                preserveAspectRatio="xMidYMid meet"
                class="w-full h-full"
              >
                <rect
                  v-if="previewBBox"
                  :x="previewBBox[0]"
                  :y="previewBBox[1]"
                  :width="previewBBox[2] - previewBBox[0]"
                  :height="previewBBox[3] - previewBBox[1]"
                  fill="none"
                  stroke="#e5e7eb"
                  stroke-width="0.2"
                />
                <g>
                  <polyline
                    v-for="(path, idx) in preview.paths"
                    :key="idx"
                    :points="polylinePoints(path.points)"
                    fill="none"
                    stroke="#111827"
                    stroke-width="0.4"
                  />
                </g>
              </svg>
            </div>
            <svg v-else viewBox="-60 -60 120 120" class="w-full h-full" style="max-width: 240px; max-height: 240px;">
              <!-- Placeholder rosette graphic -->
              <defs>
                <pattern id="herringbone" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
                  <line x1="0" y1="0" x2="0" y2="8" stroke="#d1d5db" stroke-width="2"/>
                </pattern>
              </defs>
              <!-- Outer ring -->
              <circle cx="0" cy="0" r="50" fill="none" stroke="#9ca3af" stroke-width="0.5" stroke-dasharray="2,2"/>
              <!-- Decorative band -->
              <circle cx="0" cy="0" r="45" fill="none" stroke="#6b7280" stroke-width="8"/>
              <circle cx="0" cy="0" r="45" fill="url(#herringbone)" opacity="0.3"/>
              <!-- Middle ring -->
              <circle cx="0" cy="0" r="35" fill="none" stroke="#9ca3af" stroke-width="0.5" stroke-dasharray="2,2"/>
              <!-- Inner decorative -->
              <circle cx="0" cy="0" r="30" fill="none" stroke="#6b7280" stroke-width="6"/>
              <!-- Center circle -->
              <circle cx="0" cy="0" r="20" fill="none" stroke="#9ca3af" stroke-width="0.5" stroke-dasharray="2,2"/>
              <!-- Radial segments (12 divisions) -->
              <g opacity="0.2">
                <line v-for="i in 12" :key="i" x1="0" y1="0" :x2="Math.cos((i * 30 - 90) * Math.PI / 180) * 50" :y2="Math.sin((i * 30 - 90) * Math.PI / 180) * 50" stroke="#6b7280" stroke-width="0.3"/>
              </g>
              <!-- Center dot -->
              <circle cx="0" cy="0" r="2" fill="#9ca3af"/>
              <!-- Placeholder text -->
              <text x="0" y="68" text-anchor="middle" class="fill-gray-400 text-[8px]" font-family="system-ui">
                Click "Preview Rosette" to generate
              </text>
            </svg>
          </div>
        </div>

        <!-- Recent jobs -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 text-[11px] text-gray-800">
          <div class="flex items-center justify-between">
            <h2 class="text-[12px] font-semibold text-gray-900">
              Recent Rosette Jobs
            </h2>
            <button
              class="px-2 py-1 rounded border text-[10px] text-gray-700 hover:bg-gray-50"
              @click="refreshJobs"
            >
              Reload
            </button>
          </div>

          <div v-if="jobsLoading" class="text-[10px] text-gray-500 italic">
            Loading jobs…
          </div>
          <div v-else-if="jobsError" class="text-[10px] text-rose-600">
            {{ jobsError }}
          </div>
          <div v-else-if="!jobs.length" class="text-[10px] text-gray-500 italic">
            No saved rosette jobs yet.
          </div>
          <div v-else class="max-h-48 overflow-auto space-y-1">
            <div
              v-for="job in jobs"
              :key="job.job_id"
              class="flex items-center justify-between gap-2 px-2 py-1 rounded hover:bg-gray-50 cursor-pointer"
              @click="loadJobPreview(job)"
            >
              <div class="flex flex-col">
                <span class="text-[11px] font-medium text-gray-900">
                  {{ job.name || job.job_id }}
                </span>
                <span class="text-[10px] text-gray-500">
                  {{ job.preset || '(no preset)' }} ·
                  {{ formatDate(job.created_at) }}
                </span>
              </div>
              <div class="text-[10px] font-mono text-gray-500">
                {{ job.preview.segments }} seg ·
                {{ job.preview.pattern_type }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";

interface RosettePreset {
  name: string;
  pattern_type: string;
  segments: number;
  inner_radius: number;
  outer_radius: number;
  metadata: Record<string, any>;
}

interface RosettePath {
  points: [number, number][];
}

interface RosettePreview {
  job_id: string;
  pattern_type: string;
  segments: number;
  inner_radius: number;
  outer_radius: number;
  units: string;
  preset: string | null;
  name: string | null;
  paths: RosettePath[];
  bbox: [number, number, number, number];
}

interface RosetteJob {
  job_id: string;
  name: string | null;
  preset: string | null;
  created_at: string;
  preview: RosettePreview;
}

const form = reactive({
  name: "",
  preset: "",
  pattern_type: "simple_ring",
  segments: 64,
  inner_radius: 40.0,
  outer_radius: 45.0,
  units: "mm",
});

const presets = ref<RosettePreset[]>([]);
const preview = ref<RosettePreview | null>(null);
const previewLoading = ref(false);
const saveLoading = ref(false);

const statusMessage = ref("");
const statusIsError = ref(false);

const jobs = ref<RosetteJob[]>([]);
const jobsLoading = ref(false);
const jobsError = ref<string | null>(null);

const selectedPresetDescription = computed(() => {
  if (!form.preset) return "";
  const p = presets.value.find((x) => x.name === form.preset);
  if (!p) return "";
  const meta = p.metadata || {};
  if (meta.description) return meta.description as string;
  return `${p.pattern_type} · ${p.segments} segments`;
});

const previewBBox = computed<[number, number, number, number] | null>(() => {
  if (!preview.value) return null;
  return preview.value.bbox;
});

const svgViewBox = computed(() => {
  if (!previewBBox.value) {
    return "-60 -60 120 120";
  }
  const [minX, minY, maxX, maxY] = previewBBox.value;
  const pad = 5;
  const width = maxX - minX || 1;
  const height = maxY - minY || 1;
  const x = minX - pad;
  const y = minY - pad;
  const w = width + pad * 2;
  const h = height + pad * 2;
  return `${x} ${y} ${w} ${h}`;
});

const statusClass = computed(() =>
  statusIsError.value
    ? "text-[10px] text-rose-600"
    : "text-[10px] text-emerald-700"
);

function setStatus(msg: string, isError = false) {
  statusMessage.value = msg;
  statusIsError.value = isError;
}

function polylinePoints(pts: [number, number][]): string {
  return pts.map(([x, y]) => `${x},${y}`).join(" ");
}

function applyPresetToForm(p: RosettePreset) {
  form.pattern_type = p.pattern_type || "simple_ring";
  form.segments = p.segments;
  form.inner_radius = p.inner_radius;
  form.outer_radius = p.outer_radius;
}

async function refreshPresets() {
  try {
    const res = await axios.get<RosettePreset[]>("/api/art/rosette/presets");
    presets.value = res.data || [];
    // if a preset is selected, update the form parameters to match
    if (form.preset) {
      const p = presets.value.find((x) => x.name === form.preset);
      if (p) applyPresetToForm(p);
    }
  } catch (err) {
    console.error("Failed to load rosette presets", err);
    setStatus("Failed to load presets.", true);
  }
}

async function runPreview() {
  setStatus("");
  previewLoading.value = true;
  try {
    const payload = {
      pattern_type: form.pattern_type,
      segments: form.segments,
      inner_radius: form.inner_radius,
      outer_radius: form.outer_radius,
      units: form.units,
      preset: form.preset || null,
      name: form.name || null,
    };
    const res = await axios.post<RosettePreview>("/api/art/rosette/preview", payload);
    preview.value = res.data;
    setStatus("Preview generated.", false);
  } catch (err: any) {
    console.error("Preview failed", err);
    const msg =
      err?.response?.data?.detail ||
      "Failed to generate preview.";
    setStatus(msg, true);
  } finally {
    previewLoading.value = false;
  }
}

async function saveJob() {
  if (!preview.value) return;
  saveLoading.value = true;
  setStatus("");
  try {
    const payload = {
      job_id: preview.value.job_id,
      name: form.name || preview.value.name,
      preset: form.preset || preview.value.preset,
    };
    const res = await axios.post<RosetteJob>("/api/art/rosette/save", payload);
    // reflect returned preview in UI
    preview.value = res.data.preview;
    form.name = res.data.name || form.name;
    if (res.data.preset) form.preset = res.data.preset;
    setStatus("Rosette job saved.", false);
    await refreshJobs();
  } catch (err: any) {
    console.error("Save failed", err);
    const msg =
      err?.response?.data?.detail ||
      "Failed to save rosette job.";
    setStatus(msg, true);
  } finally {
    saveLoading.value = false;
  }
}

async function refreshJobs() {
  jobsLoading.value = true;
  jobsError.value = null;
  try {
    const res = await axios.get<RosetteJob[]>("/api/art/rosette/jobs", {
      params: { limit: 25 },
    });
    jobs.value = res.data || [];
  } catch (err) {
    console.error("Failed to load jobs", err);
    jobsError.value = "Failed to load rosette jobs.";
  } finally {
    jobsLoading.value = false;
  }
}

function loadJobPreview(job: RosetteJob) {
  preview.value = job.preview;
  form.name = job.name || "";
  form.preset = job.preset || "";
  if (form.preset) {
    const p = presets.value.find((x) => x.name === form.preset);
    if (p) applyPresetToForm(p);
  } else {
    // fall back to whatever the preview contains
    form.pattern_type = job.preview.pattern_type;
    form.segments = job.preview.segments;
    form.inner_radius = job.preview.inner_radius;
    form.outer_radius = job.preview.outer_radius;
  }
}

function formatDate(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

onMounted(async () => {
  await refreshPresets();
  await refreshJobs();
});
</script>

4️⃣ Frontend: Add route for Art Studio Rosette

In your Vue router (e.g. packages/client/src/router/index.ts), add a route pointing to this view.

Somewhere in your routes array:

// packages/client/src/router/index.ts
