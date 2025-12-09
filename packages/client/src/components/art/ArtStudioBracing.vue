<script setup lang="ts">
/**
 * ArtStudioBracing.vue
 *
 * Guitar bracing section calculator.
 * Computes section properties, mass, and stiffness for various brace profiles.
 */
import { ref, computed, watch, onMounted } from "vue";
import {
  previewBracing,
  batchBracing,
  exportBracingDXF,
  listBracingPresets,
  downloadBlob,
  COMMON_WOODS,
  type BracingPreviewResponse,
  type BracingPresetInfo,
  type BraceProfileType,
  type BracingPreviewRequest,
} from "@/api/art-studio";

// Types
interface BraceEntry extends BracingPreviewRequest {
  id: number;
  name: string;
  x_mm: number;
  y_mm: number;
  angle_deg: number;
  result?: BracingPreviewResponse;
}

// State
const loading = ref(false);
const error = ref<string | null>(null);
const presets = ref<BracingPresetInfo[]>([]);

// Single brace preview
const profileType = ref<BraceProfileType>("parabolic");
const width = ref(12.0);
const height = ref(8.0);
const length = ref(300.0);
const density = ref(420.0);
const singleResult = ref<BracingPreviewResponse | null>(null);

// Batch mode
const braces = ref<BraceEntry[]>([]);
const batchName = ref("X-Brace Set");
const batchResult = ref<{
  total_mass_grams: number;
  total_stiffness: number;
} | null>(null);
const nextBraceId = ref(1);

// Export options
const dxfVersion = ref("R12");
const includeCenterlines = ref(true);
const includeLabels = ref(true);

// Profile types
const profileTypes: { value: BraceProfileType; label: string; desc: string }[] =
  [
    {
      value: "rectangular",
      label: "Rectangular",
      desc: "Standard rectangular cross-section",
    },
    {
      value: "triangular",
      label: "Triangular",
      desc: "Peaked top for stiffness",
    },
    {
      value: "parabolic",
      label: "Parabolic",
      desc: "Curved top, classic design",
    },
    {
      value: "scalloped",
      label: "Scalloped",
      desc: "Tapered ends for flexibility",
    },
  ];

// Computed
const selectedWood = computed({
  get: () => {
    const found = COMMON_WOODS.find(
      (w) => Math.abs(w.density - density.value) < 5
    );
    return found?.name || null;
  },
  set: (name: string | null) => {
    const found = COMMON_WOODS.find((w) => w.name === name);
    if (found) density.value = found.density;
  },
});

// Methods
async function loadPresets() {
  try {
    presets.value = await listBracingPresets();
  } catch (e: any) {
    console.warn("Failed to load presets:", e);
  }
}

async function previewSingle() {
  loading.value = true;
  error.value = null;
  try {
    singleResult.value = await previewBracing({
      profile_type: profileType.value,
      width_mm: width.value,
      height_mm: height.value,
      length_mm: length.value,
      density_kg_m3: density.value,
    });
  } catch (e: any) {
    error.value = e.message || "Preview failed";
  } finally {
    loading.value = false;
  }
}

function addBrace() {
  const newBrace: BraceEntry = {
    id: nextBraceId.value++,
    name: `Brace ${braces.value.length + 1}`,
    profile_type: profileType.value,
    width_mm: width.value,
    height_mm: height.value,
    length_mm: length.value,
    density_kg_m3: density.value,
    x_mm: 0,
    y_mm: 0,
    angle_deg: 0,
  };
  braces.value.push(newBrace);
}

function removeBrace(id: number) {
  const idx = braces.value.findIndex((b) => b.id === id);
  if (idx >= 0) braces.value.splice(idx, 1);
}

function copyCurrentToBrace() {
  addBrace();
}

async function calculateBatch() {
  if (braces.value.length === 0) {
    error.value = "Add at least one brace to calculate batch";
    return;
  }

  loading.value = true;
  error.value = null;
  try {
    const result = await batchBracing({
      name: batchName.value,
      braces: braces.value.map((b) => ({
        profile_type: b.profile_type,
        width_mm: b.width_mm,
        height_mm: b.height_mm,
        length_mm: b.length_mm,
        density_kg_m3: b.density_kg_m3,
      })),
    });

    // Update individual brace results
    result.braces.forEach((res, idx) => {
      if (braces.value[idx]) {
        braces.value[idx].result = res;
      }
    });

    batchResult.value = {
      total_mass_grams: result.total_mass_grams,
      total_stiffness: result.total_stiffness,
    };
  } catch (e: any) {
    error.value = e.message || "Batch calculation failed";
  } finally {
    loading.value = false;
  }
}

async function exportDXF() {
  if (braces.value.length === 0) {
    error.value = "Add at least one brace to export";
    return;
  }

  loading.value = true;
  error.value = null;
  try {
    const blob = await exportBracingDXF({
      braces: braces.value.map((b) => ({
        profile_type: b.profile_type,
        width_mm: b.width_mm,
        height_mm: b.height_mm,
        length_mm: b.length_mm,
        x_mm: b.x_mm,
        y_mm: b.y_mm,
        angle_deg: b.angle_deg,
      })),
      dxf_version: dxfVersion.value,
      include_centerlines: includeCenterlines.value,
      include_labels: includeLabels.value,
    });
    downloadBlob(blob, `bracing_${batchName.value.replace(/\s+/g, "_")}.dxf`);
  } catch (e: any) {
    error.value = e.message || "Export failed";
  } finally {
    loading.value = false;
  }
}

function applyPresetProfile(preset: BracingPresetInfo) {
  profileType.value = preset.profile_type;
  const wood = COMMON_WOODS.find((w) =>
    w.name.toLowerCase().includes(preset.typical_wood.toLowerCase())
  );
  if (wood) density.value = wood.density;
}

// Watchers
watch([profileType, width, height, length, density], () => previewSingle(), {
  debounce: 300,
} as any);

onMounted(() => {
  loadPresets();
  previewSingle();
});
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">🪵</span>
      Bracing Calculator
    </h1>

    <!-- Error Banner -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4"
    >
      {{ error }}
      <button class="ml-2 underline" @click="error = null">Dismiss</button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Panel: Single Brace Calculator -->
      <div class="space-y-4">
        <h2 class="text-lg font-semibold text-gray-800">
          Single Brace Calculator
        </h2>

        <!-- Preset Quick-Apply -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Quick Presets</label
          >
          <div class="flex flex-wrap gap-2">
            <button
              v-for="p in presets"
              :key="p.name"
              class="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-100"
              :title="p.description"
              @click="applyPresetProfile(p)"
            >
              {{ p.name }}
            </button>
          </div>
        </div>

        <!-- Profile Type -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Profile Type</h3>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="pt in profileTypes"
              :key="pt.value"
              class="p-3 rounded-lg border-2 text-left transition-all"
              :class="
                profileType === pt.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-400'
              "
              @click="profileType = pt.value"
            >
              <div class="font-medium text-sm">{{ pt.label }}</div>
              <div class="text-xs text-gray-500">{{ pt.desc }}</div>
            </button>
          </div>
        </div>

        <!-- Dimensions -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Dimensions</h3>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Width (mm)</label>
            <input
              v-model.number="width"
              type="range"
              min="5"
              max="30"
              step="0.5"
              class="w-full"
            />
            <div class="text-sm text-gray-700 text-right">
              {{ width.toFixed(1) }} mm
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Height (mm)</label>
            <input
              v-model.number="height"
              type="range"
              min="3"
              max="20"
              step="0.5"
              class="w-full"
            />
            <div class="text-sm text-gray-700 text-right">
              {{ height.toFixed(1) }} mm
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Length (mm)</label>
            <input
              v-model.number="length"
              type="range"
              min="50"
              max="500"
              step="5"
              class="w-full"
            />
            <div class="text-sm text-gray-700 text-right">
              {{ length.toFixed(0) }} mm
            </div>
          </div>
        </div>

        <!-- Wood Selection -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Wood Type</h3>

          <select
            v-model="selectedWood"
            class="w-full border rounded px-3 py-2 text-sm"
          >
            <option :value="null">Custom</option>
            <option v-for="w in COMMON_WOODS" :key="w.name" :value="w.name">
              {{ w.name }} ({{ w.density }} kg/m³)
            </option>
          </select>

          <div>
            <label class="block text-xs text-gray-600 mb-1"
              >Density (kg/m³)</label
            >
            <input
              v-model.number="density"
              type="number"
              min="200"
              max="1200"
              step="10"
              class="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
        </div>

        <!-- Single Brace Results -->
        <div v-if="singleResult" class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Section Properties</h3>

          <table class="w-full text-sm">
            <tbody>
              <tr class="border-b">
                <td class="py-2 text-gray-600">Cross-Section Area</td>
                <td class="py-2 text-right font-mono">
                  {{ singleResult.section.area_mm2.toFixed(2) }} mm²
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">Centroid Height</td>
                <td class="py-2 text-right font-mono">
                  {{ singleResult.section.centroid_y_mm.toFixed(2) }} mm
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">Moment of Inertia</td>
                <td class="py-2 text-right font-mono">
                  {{ singleResult.section.inertia_mm4.toFixed(1) }} mm⁴
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">Section Modulus</td>
                <td class="py-2 text-right font-mono">
                  {{ singleResult.section.section_modulus_mm3.toFixed(1) }} mm³
                </td>
              </tr>
              <tr class="border-b bg-amber-50">
                <td class="py-2 text-gray-700 font-medium">Mass</td>
                <td class="py-2 text-right font-mono font-bold">
                  {{ singleResult.mass_grams.toFixed(2) }} g
                </td>
              </tr>
              <tr v-if="singleResult.stiffness_estimate" class="bg-blue-50">
                <td class="py-2 text-gray-700 font-medium">Stiffness Index</td>
                <td class="py-2 text-right font-mono font-bold">
                  {{ singleResult.stiffness_estimate.toFixed(0) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Add to Batch Button -->
        <button
          class="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
          @click="copyCurrentToBrace"
        >
          + Add to Batch
        </button>
      </div>

      <!-- Middle Panel: Batch List -->
      <div class="space-y-4">
        <h2 class="text-lg font-semibold text-gray-800">Bracing Set</h2>

        <!-- Batch Name -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="block text-xs text-gray-600 mb-1">Set Name</label>
          <input
            v-model="batchName"
            type="text"
            class="w-full border rounded px-3 py-2 text-sm"
            placeholder="X-Brace Set"
          />
        </div>

        <!-- Brace List -->
        <div v-if="braces.length > 0" class="space-y-2">
          <div
            v-for="brace in braces"
            :key="brace.id"
            class="bg-white border rounded-lg p-3"
          >
            <div class="flex justify-between items-start mb-2">
              <input
                v-model="brace.name"
                type="text"
                class="font-medium text-sm border-b border-transparent hover:border-gray-300 focus:border-blue-500 outline-none"
              />
              <button
                class="text-red-500 hover:text-red-700 text-sm"
                @click="removeBrace(brace.id)"
              >
                ✕
              </button>
            </div>

            <div class="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label class="text-gray-500">Profile</label>
                <select
                  v-model="brace.profile_type"
                  class="w-full border rounded px-1 py-0.5"
                >
                  <option
                    v-for="pt in profileTypes"
                    :key="pt.value"
                    :value="pt.value"
                  >
                    {{ pt.label }}
                  </option>
                </select>
              </div>
              <div>
                <label class="text-gray-500">Length (mm)</label>
                <input
                  v-model.number="brace.length_mm"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
              <div>
                <label class="text-gray-500">Width (mm)</label>
                <input
                  v-model.number="brace.width_mm"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
              <div>
                <label class="text-gray-500">Height (mm)</label>
                <input
                  v-model.number="brace.height_mm"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
            </div>

            <!-- Position for DXF export -->
            <div class="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div>
                <label class="text-gray-500">X</label>
                <input
                  v-model.number="brace.x_mm"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
              <div>
                <label class="text-gray-500">Y</label>
                <input
                  v-model.number="brace.y_mm"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
              <div>
                <label class="text-gray-500">Angle (°)</label>
                <input
                  v-model.number="brace.angle_deg"
                  type="number"
                  class="w-full border rounded px-1 py-0.5"
                />
              </div>
            </div>

            <!-- Individual Result -->
            <div
              v-if="brace.result"
              class="mt-2 text-xs bg-gray-50 rounded p-2"
            >
              <span class="text-gray-600">Mass:</span>
              <span class="font-mono ml-1"
                >{{ brace.result.mass_grams.toFixed(2) }}g</span
              >
              <span class="mx-2 text-gray-300">|</span>
              <span class="text-gray-600">Stiffness:</span>
              <span class="font-mono ml-1">{{
                brace.result.stiffness_estimate?.toFixed(0) || "—"
              }}</span>
            </div>
          </div>
        </div>

        <div
          v-else
          class="bg-gray-100 rounded-lg p-8 text-center text-gray-400"
        >
          <div class="text-4xl mb-2">📦</div>
          <div>No braces added yet</div>
          <div class="text-xs mt-1">
            Use the calculator on the left, then click "Add to Batch"
          </div>
        </div>

        <!-- Batch Action Buttons -->
        <div class="flex gap-3">
          <button
            class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            :disabled="loading || braces.length === 0"
            @click="calculateBatch"
          >
            Calculate All
          </button>
        </div>
      </div>

      <!-- Right Panel: Batch Results & Export -->
      <div class="space-y-4">
        <h2 class="text-lg font-semibold text-gray-800">Results & Export</h2>

        <!-- Batch Summary -->
        <div v-if="batchResult" class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Batch Summary</h3>

          <div class="grid grid-cols-2 gap-4">
            <div class="bg-amber-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-amber-700">
                {{ batchResult.total_mass_grams.toFixed(1) }}
              </div>
              <div class="text-xs text-amber-600 mt-1">Total Mass (grams)</div>
            </div>
            <div class="bg-blue-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-blue-700">
                {{ batchResult.total_stiffness.toFixed(0) }}
              </div>
              <div class="text-xs text-blue-600 mt-1">
                Total Stiffness Index
              </div>
            </div>
          </div>

          <div class="mt-4 text-xs text-gray-500">
            <strong>{{ braces.length }}</strong> braces in set "{{ batchName }}"
          </div>
        </div>

        <!-- Export Options -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Export Options</h3>

          <div>
            <label class="block text-xs text-gray-600 mb-1">DXF Version</label>
            <select
              v-model="dxfVersion"
              class="w-full border rounded px-3 py-2 text-sm"
            >
              <option value="R12">R12 (Most Compatible)</option>
              <option value="R2000">R2000</option>
              <option value="R2010">R2010</option>
            </select>
          </div>

          <label class="flex items-center gap-2 text-sm">
            <input v-model="includeCenterlines" type="checkbox" />
            Include centerlines
          </label>

          <label class="flex items-center gap-2 text-sm">
            <input v-model="includeLabels" type="checkbox" />
            Include labels
          </label>
        </div>

        <!-- Export Button -->
        <button
          class="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
          :disabled="loading || braces.length === 0"
          @click="exportDXF"
        >
          Export DXF Layout
        </button>

        <!-- Profile Diagram -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Profile Reference</h3>

          <div class="grid grid-cols-2 gap-4 text-center text-xs">
            <div class="bg-gray-50 rounded p-2">
              <div class="text-lg mb-1">▬</div>
              <div>Rectangular</div>
              <div class="text-gray-500">Max stiffness</div>
            </div>
            <div class="bg-gray-50 rounded p-2">
              <div class="text-lg mb-1">▲</div>
              <div>Triangular</div>
              <div class="text-gray-500">Good stiffness/weight</div>
            </div>
            <div class="bg-gray-50 rounded p-2">
              <div class="text-lg mb-1">⌓</div>
              <div>Parabolic</div>
              <div class="text-gray-500">Classic tone</div>
            </div>
            <div class="bg-gray-50 rounded p-2">
              <div class="text-lg mb-1">⌢</div>
              <div>Scalloped</div>
              <div class="text-gray-500">Flexible ends</div>
            </div>
          </div>
        </div>

        <!-- Formula Reference -->
        <div class="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
          <h4 class="font-semibold mb-2">Section Properties</h4>
          <ul class="space-y-1">
            <li><strong>I</strong> = Moment of Inertia (mm⁴)</li>
            <li><strong>S</strong> = Section Modulus = I / c (mm³)</li>
            <li><strong>Mass</strong> = Area × Length × Density</li>
            <li><strong>Stiffness Index</strong> = Area × Length (relative)</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
input[type="range"] {
  @apply h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer;
}
input[type="range"]::-webkit-slider-thumb {
  @apply appearance-none w-4 h-4 bg-blue-500 rounded-full cursor-pointer;
}
</style>
