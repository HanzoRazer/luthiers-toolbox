<script setup lang="ts">
/**
 * ArtStudioRosette.vue
 *
 * Interactive rosette channel calculator for classical guitars.
 * Computes channel dimensions and exports DXF for CNC routing.
 */
import { ref, computed, watch, onMounted } from "vue";
import {
  previewRosette,
  exportRosetteDXF,
  listRosettePresets,
  getRosettePreset,
  downloadBlob,
  PURFLING_MATERIALS,
  type RosettePreviewResponse,
  type RosettePresetInfo,
  type PurflingBand,
} from "@/api/art-studio";

// State
const loading = ref(false);
const error = ref<string | null>(null);
const previewResult = ref<RosettePreviewResponse | null>(null);
const presets = ref<RosettePresetInfo[]>([]);
const selectedPreset = ref<string | null>(null);

// Form inputs
const soundholeDiameter = ref(100.0);
const centralBand = ref(3.0);
const channelDepth = ref(1.5);
const centerX = ref(0.0);
const centerY = ref(0.0);
const includePurflingRings = ref(true);

// Purfling configuration
const innerPurfling = ref<PurflingBand[]>([{ material: "bwb", width_mm: 1.5 }]);
const outerPurfling = ref<PurflingBand[]>([{ material: "bwb", width_mm: 1.5 }]);

// Computed
const totalChannelWidth = computed(() => {
  const inner = innerPurfling.value.reduce((sum, b) => sum + b.width_mm, 0);
  const outer = outerPurfling.value.reduce((sum, b) => sum + b.width_mm, 0);
  return inner + centralBand.value + outer;
});

// Methods
async function loadPresets() {
  try {
    presets.value = await listRosettePresets();
  } catch (e: any) {
    console.warn("Failed to load presets:", e);
  }
}

async function applyPreset() {
  if (!selectedPreset.value) return;
  try {
    const preset = await getRosettePreset(selectedPreset.value);
    soundholeDiameter.value = preset.soundhole_diameter_mm;
    centralBand.value = preset.central_band_mm;
    channelDepth.value = preset.channel_depth_mm;
    innerPurfling.value = [...preset.inner_purfling];
    outerPurfling.value = [...preset.outer_purfling];
    await refreshPreview();
  } catch (e: any) {
    error.value = `Failed to load preset: ${e.message}`;
  }
}

async function refreshPreview() {
  loading.value = true;
  error.value = null;
  try {
    previewResult.value = await previewRosette({
      soundhole_diameter_mm: soundholeDiameter.value,
      central_band_mm: centralBand.value,
      inner_purfling: innerPurfling.value,
      outer_purfling: outerPurfling.value,
      channel_depth_mm: channelDepth.value,
    });
  } catch (e: any) {
    error.value = e.message || "Preview failed";
  } finally {
    loading.value = false;
  }
}

async function exportDXF() {
  loading.value = true;
  error.value = null;
  try {
    const blob = await exportRosetteDXF({
      soundhole_diameter_mm: soundholeDiameter.value,
      central_band_mm: centralBand.value,
      inner_purfling: innerPurfling.value,
      outer_purfling: outerPurfling.value,
      channel_depth_mm: channelDepth.value,
      center_x_mm: centerX.value,
      center_y_mm: centerY.value,
      include_purfling_rings: includePurflingRings.value,
    });
    downloadBlob(blob, `rosette_${soundholeDiameter.value}mm.dxf`);
  } catch (e: any) {
    error.value = e.message || "Export failed";
  } finally {
    loading.value = false;
  }
}

function addPurflingBand(side: "inner" | "outer") {
  const band: PurflingBand = { material: "bwb", width_mm: 1.5 };
  if (side === "inner") {
    innerPurfling.value.push(band);
  } else {
    outerPurfling.value.push(band);
  }
}

function removePurflingBand(side: "inner" | "outer", index: number) {
  if (side === "inner") {
    innerPurfling.value.splice(index, 1);
  } else {
    outerPurfling.value.splice(index, 1);
  }
}

// Auto-preview on significant changes
watch([soundholeDiameter, centralBand, channelDepth], () => refreshPreview(), {
  debounce: 300,
} as any);

onMounted(() => {
  loadPresets();
  refreshPreview();
});
</script>

<template>
  <div class="p-4 max-w-5xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">🎸</span>
      Rosette Channel Calculator
    </h1>

    <!-- Error Banner -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4"
    >
      {{ error }}
      <button
        class="ml-2 underline"
        @click="error = null"
      >
        Dismiss
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Panel: Parameters -->
      <div class="space-y-4">
        <!-- Preset Selector -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Load Preset</label>
          <div class="flex gap-2">
            <select
              v-model="selectedPreset"
              class="flex-1 border rounded px-3 py-2 text-sm"
            >
              <option :value="null">
                — Select preset —
              </option>
              <option
                v-for="p in presets"
                :key="p.name"
                :value="p.name"
              >
                {{ p.name }}
              </option>
            </select>
            <button
              class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              :disabled="!selectedPreset || loading"
              @click="applyPreset"
            >
              Apply
            </button>
          </div>
        </div>

        <!-- Basic Dimensions -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Dimensions
          </h3>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Soundhole Diameter (mm)</label>
            <input
              v-model.number="soundholeDiameter"
              type="range"
              min="50"
              max="150"
              step="0.5"
              class="w-full"
            >
            <div class="text-sm text-gray-700 text-right">
              {{ soundholeDiameter.toFixed(1) }} mm
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Central Band Width (mm)</label>
            <input
              v-model.number="centralBand"
              type="range"
              min="0"
              max="20"
              step="0.5"
              class="w-full"
            >
            <div class="text-sm text-gray-700 text-right">
              {{ centralBand.toFixed(1) }} mm
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Channel Depth (mm)</label>
            <input
              v-model.number="channelDepth"
              type="range"
              min="0.5"
              max="4.0"
              step="0.1"
              class="w-full"
            >
            <div class="text-sm text-gray-700 text-right">
              {{ channelDepth.toFixed(1) }} mm
            </div>
          </div>
        </div>

        <!-- Inner Purfling -->
        <div class="bg-white border rounded-lg p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-semibold text-gray-800">
              Inner Purfling
            </h3>
            <button
              class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
              @click="addPurflingBand('inner')"
            >
              + Add Band
            </button>
          </div>

          <div
            v-for="(band, idx) in innerPurfling"
            :key="'inner-' + idx"
            class="flex gap-2 mb-2 items-center"
          >
            <select
              v-model="band.material"
              class="flex-1 border rounded px-2 py-1 text-sm"
            >
              <option
                v-for="m in PURFLING_MATERIALS"
                :key="m.code"
                :value="m.code"
              >
                {{ m.name }}
              </option>
            </select>
            <input
              v-model.number="band.width_mm"
              type="number"
              min="0.5"
              max="10"
              step="0.1"
              class="w-20 border rounded px-2 py-1 text-sm"
            >
            <span class="text-xs text-gray-500">mm</span>
            <button
              v-if="innerPurfling.length > 0"
              class="text-red-500 hover:text-red-700"
              @click="removePurflingBand('inner', idx)"
            >
              ✕
            </button>
          </div>
          <div
            v-if="innerPurfling.length === 0"
            class="text-sm text-gray-400 italic"
          >
            No inner purfling
          </div>
        </div>

        <!-- Outer Purfling -->
        <div class="bg-white border rounded-lg p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-semibold text-gray-800">
              Outer Purfling
            </h3>
            <button
              class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
              @click="addPurflingBand('outer')"
            >
              + Add Band
            </button>
          </div>

          <div
            v-for="(band, idx) in outerPurfling"
            :key="'outer-' + idx"
            class="flex gap-2 mb-2 items-center"
          >
            <select
              v-model="band.material"
              class="flex-1 border rounded px-2 py-1 text-sm"
            >
              <option
                v-for="m in PURFLING_MATERIALS"
                :key="m.code"
                :value="m.code"
              >
                {{ m.name }}
              </option>
            </select>
            <input
              v-model.number="band.width_mm"
              type="number"
              min="0.5"
              max="10"
              step="0.1"
              class="w-20 border rounded px-2 py-1 text-sm"
            >
            <span class="text-xs text-gray-500">mm</span>
            <button
              v-if="outerPurfling.length > 0"
              class="text-red-500 hover:text-red-700"
              @click="removePurflingBand('outer', idx)"
            >
              ✕
            </button>
          </div>
          <div
            v-if="outerPurfling.length === 0"
            class="text-sm text-gray-400 italic"
          >
            No outer purfling
          </div>
        </div>

        <!-- Export Options -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Export Options
          </h3>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-600 mb-1">Center X (mm)</label>
              <input
                v-model.number="centerX"
                type="number"
                step="0.1"
                class="w-full border rounded px-2 py-1 text-sm"
              >
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Center Y (mm)</label>
              <input
                v-model.number="centerY"
                type="number"
                step="0.1"
                class="w-full border rounded px-2 py-1 text-sm"
              >
            </div>
          </div>

          <label class="flex items-center gap-2 text-sm">
            <input
              v-model="includePurflingRings"
              type="checkbox"
            >
            Include individual purfling ring circles
          </label>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-3">
          <button
            class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            :disabled="loading"
            @click="refreshPreview"
          >
            {{ loading ? "Calculating..." : "Preview" }}
          </button>
          <button
            class="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
            :disabled="loading || !previewResult"
            @click="exportDXF"
          >
            Export DXF
          </button>
        </div>
      </div>

      <!-- Right Panel: Preview -->
      <div class="space-y-4">
        <!-- SVG Preview -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">
            Preview
          </h3>

          <div
            v-if="previewResult?.preview_svg"
            class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px]"
            v-html="previewResult.preview_svg"
          />
          <div
            v-else
            class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px] text-gray-400"
          >
            Click Preview to generate
          </div>
        </div>

        <!-- Results Table -->
        <div
          v-if="previewResult"
          class="bg-white border rounded-lg p-4"
        >
          <h3 class="font-semibold text-gray-800 mb-3">
            Channel Dimensions
          </h3>

          <table class="w-full text-sm">
            <tbody>
              <tr class="border-b">
                <td class="py-2 text-gray-600">
                  Soundhole Radius
                </td>
                <td class="py-2 text-right font-mono">
                  {{ previewResult.result.soundhole_radius_mm.toFixed(2) }} mm
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">
                  Channel Inner Radius
                </td>
                <td class="py-2 text-right font-mono">
                  {{
                    previewResult.result.channel_inner_radius_mm.toFixed(2)
                  }}
                  mm
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">
                  Channel Outer Radius
                </td>
                <td class="py-2 text-right font-mono">
                  {{
                    previewResult.result.channel_outer_radius_mm.toFixed(2)
                  }}
                  mm
                </td>
              </tr>
              <tr class="border-b">
                <td class="py-2 text-gray-600">
                  Channel Width
                </td>
                <td class="py-2 text-right font-mono font-bold">
                  {{ previewResult.result.channel_width_mm.toFixed(2) }} mm
                </td>
              </tr>
              <tr>
                <td class="py-2 text-gray-600">
                  Channel Depth
                </td>
                <td class="py-2 text-right font-mono">
                  {{ previewResult.result.channel_depth_mm.toFixed(2) }} mm
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Stack Breakdown -->
        <div
          v-if="previewResult?.result.stack?.length"
          class="bg-white border rounded-lg p-4"
        >
          <h3 class="font-semibold text-gray-800 mb-3">
            Stack Breakdown
          </h3>

          <div class="space-y-2">
            <div
              v-for="(item, idx) in previewResult.result.stack"
              :key="idx"
              class="flex justify-between items-center py-1 px-2 rounded"
              :class="
                item.label.includes('Central') ? 'bg-amber-50' : 'bg-gray-50'
              "
            >
              <span class="text-sm">{{ item.label }}</span>
              <span class="text-xs font-mono text-gray-600">
                {{ item.width_mm.toFixed(1) }} mm ({{
                  item.inner_radius_mm.toFixed(1)
                }}
                → {{ item.outer_radius_mm.toFixed(1) }})
              </span>
            </div>
          </div>
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
