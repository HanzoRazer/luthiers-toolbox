<script setup lang="ts">
/**
 * ArtStudioInlay.vue
 *
 * Fretboard inlay pattern designer.
 * Generates dot, diamond, block, and custom inlay patterns with DXF export.
 */
import { ref, computed, watch, onMounted } from "vue";
import {
  previewInlay,
  exportInlayDXF,
  listInlayPresets,
  getInlayPreset,
  getFretPositions,
  downloadBlob,
  COMMON_SCALE_LENGTHS,
  type InlayPreviewResponse,
  type InlayPresetInfo,
  type InlayPatternType,
  type FretPositionResponse,
} from "@/api/art-studio";

// State
const loading = ref(false);
const error = ref<string | null>(null);
const previewResult = ref<InlayPreviewResponse | null>(null);
const fretData = ref<FretPositionResponse | null>(null);
const presets = ref<InlayPresetInfo[]>([]);
const selectedPreset = ref<string | null>(null);

// Form inputs
const patternType = ref<InlayPatternType>("dot");
const scaleLength = ref(647.7); // Fender scale
const fretboardWidthNut = ref(43.0);
const fretboardWidthBody = ref(56.0);
const numFrets = ref(24);
const inlaySize = ref(6.0);
const doubleAt12 = ref(true);
const doubleSpacing = ref(8.0);

// Fret position checkboxes
const standardFrets = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24];
const selectedFrets = ref<number[]>([...standardFrets]);

// Export options
const dxfVersion = ref("R12");
const layerPrefix = ref("INLAY");

// Pattern types
const patternTypes: { value: InlayPatternType; label: string; icon: string }[] =
  [
    { value: "dot", label: "Dot", icon: "●" },
    { value: "diamond", label: "Diamond", icon: "◆" },
    { value: "block", label: "Block", icon: "■" },
    { value: "trapezoid", label: "Trapezoid", icon: "⬡" },
    { value: "custom", label: "Custom", icon: "✱" },
  ];

// Computed
const selectedScalePreset = computed({
  get: () => {
    const found = COMMON_SCALE_LENGTHS.find(
      (s) => Math.abs(s.mm - scaleLength.value) < 0.1
    );
    return found?.name || null;
  },
  set: (name: string | null) => {
    const found = COMMON_SCALE_LENGTHS.find((s) => s.name === name);
    if (found) scaleLength.value = found.mm;
  },
});

// Methods
async function loadPresets() {
  try {
    presets.value = await listInlayPresets();
  } catch (e: any) {
    console.warn("Failed to load presets:", e);
  }
}

async function applyPreset() {
  if (!selectedPreset.value) return;
  try {
    const preset = await getInlayPreset(selectedPreset.value);
    patternType.value = preset.pattern_type;
    selectedFrets.value = [...preset.fret_positions];
    scaleLength.value = preset.scale_length_mm;
    fretboardWidthNut.value = preset.fretboard_width_nut_mm;
    fretboardWidthBody.value = preset.fretboard_width_body_mm;
    numFrets.value = preset.num_frets;
    inlaySize.value = preset.inlay_size_mm;
    doubleAt12.value = preset.double_at_12;
    doubleSpacing.value = preset.double_spacing_mm;
    await refreshPreview();
  } catch (e: any) {
    error.value = `Failed to load preset: ${e.message}`;
  }
}

async function loadFretPositions() {
  try {
    fretData.value = await getFretPositions(scaleLength.value, numFrets.value);
  } catch (e: any) {
    console.warn("Failed to load fret positions:", e);
  }
}

async function refreshPreview() {
  loading.value = true;
  error.value = null;
  try {
    previewResult.value = await previewInlay({
      pattern_type: patternType.value,
      fret_positions: selectedFrets.value,
      scale_length_mm: scaleLength.value,
      fretboard_width_nut_mm: fretboardWidthNut.value,
      fretboard_width_body_mm: fretboardWidthBody.value,
      num_frets: numFrets.value,
      inlay_size_mm: inlaySize.value,
      double_at_12: doubleAt12.value,
      double_spacing_mm: doubleSpacing.value,
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
    const blob = await exportInlayDXF({
      pattern_type: patternType.value,
      fret_positions: selectedFrets.value,
      scale_length_mm: scaleLength.value,
      fretboard_width_nut_mm: fretboardWidthNut.value,
      fretboard_width_body_mm: fretboardWidthBody.value,
      num_frets: numFrets.value,
      inlay_size_mm: inlaySize.value,
      double_at_12: doubleAt12.value,
      double_spacing_mm: doubleSpacing.value,
      dxf_version: dxfVersion.value,
      layer_prefix: layerPrefix.value,
    });
    downloadBlob(
      blob,
      `inlay_${patternType.value}_${scaleLength.value.toFixed(0)}mm.dxf`
    );
  } catch (e: any) {
    error.value = e.message || "Export failed";
  } finally {
    loading.value = false;
  }
}

function toggleFret(fret: number) {
  const idx = selectedFrets.value.indexOf(fret);
  if (idx >= 0) {
    selectedFrets.value.splice(idx, 1);
  } else {
    selectedFrets.value.push(fret);
    selectedFrets.value.sort((a, b) => a - b);
  }
}

function selectStandardFrets() {
  selectedFrets.value = [...standardFrets];
}

function clearFrets() {
  selectedFrets.value = [];
}

// Watchers
watch([scaleLength, numFrets], () => loadFretPositions());

watch(
  [patternType, scaleLength, inlaySize, doubleAt12],
  () => refreshPreview(),
  { debounce: 300 } as any
);

onMounted(() => {
  loadPresets();
  loadFretPositions();
  refreshPreview();
});
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">◆</span>
      Fretboard Inlay Designer
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
      <!-- Left Panel: Pattern Settings -->
      <div class="space-y-4">
        <!-- Preset Selector -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Load Preset</label
          >
          <div class="flex gap-2">
            <select
              v-model="selectedPreset"
              class="flex-1 border rounded px-3 py-2 text-sm"
            >
              <option :value="null">— Select preset —</option>
              <option v-for="p in presets" :key="p.name" :value="p.name">
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

        <!-- Pattern Type -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Pattern Type</h3>
          <div class="grid grid-cols-5 gap-2">
            <button
              v-for="pt in patternTypes"
              :key="pt.value"
              class="p-3 rounded-lg border-2 text-center transition-all"
              :class="
                patternType === pt.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-400'
              "
              @click="patternType = pt.value"
            >
              <div class="text-2xl">{{ pt.icon }}</div>
              <div class="text-xs mt-1">{{ pt.label }}</div>
            </button>
          </div>
        </div>

        <!-- Scale Length -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Scale Length</h3>

          <select
            v-model="selectedScalePreset"
            class="w-full border rounded px-3 py-2 text-sm"
          >
            <option :value="null">Custom</option>
            <option
              v-for="s in COMMON_SCALE_LENGTHS"
              :key="s.name"
              :value="s.name"
            >
              {{ s.name }}
            </option>
          </select>

          <div>
            <label class="block text-xs text-gray-600 mb-1"
              >Scale Length (mm)</label
            >
            <input
              v-model.number="scaleLength"
              type="number"
              min="500"
              max="800"
              step="0.1"
              class="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
        </div>

        <!-- Fretboard Dimensions -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Fretboard Dimensions</h3>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-600 mb-1"
                >Width at Nut (mm)</label
              >
              <input
                v-model.number="fretboardWidthNut"
                type="number"
                min="35"
                max="60"
                step="0.5"
                class="w-full border rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1"
                >Width at Body (mm)</label
              >
              <input
                v-model.number="fretboardWidthBody"
                type="number"
                min="45"
                max="75"
                step="0.5"
                class="w-full border rounded px-2 py-1 text-sm"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1"
              >Number of Frets</label
            >
            <input
              v-model.number="numFrets"
              type="range"
              min="12"
              max="27"
              class="w-full"
            />
            <div class="text-sm text-gray-700 text-right">
              {{ numFrets }} frets
            </div>
          </div>
        </div>

        <!-- Inlay Settings -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Inlay Settings</h3>

          <div>
            <label class="block text-xs text-gray-600 mb-1"
              >Inlay Size (mm)</label
            >
            <input
              v-model.number="inlaySize"
              type="range"
              min="3"
              max="15"
              step="0.5"
              class="w-full"
            />
            <div class="text-sm text-gray-700 text-right">
              {{ inlaySize.toFixed(1) }} mm
            </div>
          </div>

          <label class="flex items-center gap-2 text-sm">
            <input v-model="doubleAt12" type="checkbox" />
            Double markers at 12th fret
          </label>

          <div v-if="doubleAt12">
            <label class="block text-xs text-gray-600 mb-1"
              >Double Spacing (mm)</label
            >
            <input
              v-model.number="doubleSpacing"
              type="number"
              min="4"
              max="20"
              step="0.5"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
        </div>
      </div>

      <!-- Middle Panel: Fret Selection -->
      <div class="space-y-4">
        <!-- Fret Position Selector -->
        <div class="bg-white border rounded-lg p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-semibold text-gray-800">Fret Positions</h3>
            <div class="flex gap-2">
              <button
                class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                @click="selectStandardFrets"
              >
                Standard
              </button>
              <button
                class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                @click="clearFrets"
              >
                Clear
              </button>
            </div>
          </div>

          <div class="grid grid-cols-6 gap-2">
            <button
              v-for="fret in numFrets"
              :key="fret"
              class="p-2 text-sm rounded border-2 transition-all"
              :class="
                selectedFrets.includes(fret)
                  ? 'border-blue-500 bg-blue-100 font-bold'
                  : 'border-gray-200 hover:border-gray-400'
              "
              @click="toggleFret(fret)"
            >
              {{ fret }}
            </button>
          </div>

          <div class="mt-3 text-xs text-gray-500">
            Selected: {{ selectedFrets.join(", ") || "None" }}
          </div>
        </div>

        <!-- Fret Position Table -->
        <div
          v-if="fretData"
          class="bg-white border rounded-lg p-4 max-h-[400px] overflow-y-auto"
        >
          <h3 class="font-semibold text-gray-800 mb-3">
            Fret Positions (12-TET)
          </h3>

          <table class="w-full text-xs">
            <thead class="bg-gray-50 sticky top-0">
              <tr>
                <th class="py-1 px-2 text-left">Fret</th>
                <th class="py-1 px-2 text-right">Position</th>
                <th class="py-1 px-2 text-right">Spacing</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="pos in fretData.positions"
                :key="pos.fret"
                class="border-b"
                :class="selectedFrets.includes(pos.fret) ? 'bg-blue-50' : ''"
              >
                <td class="py-1 px-2">{{ pos.fret }}</td>
                <td class="py-1 px-2 text-right font-mono">
                  {{ pos.position_mm.toFixed(2) }}
                </td>
                <td class="py-1 px-2 text-right font-mono text-gray-500">
                  {{ pos.distance_from_previous_mm.toFixed(2) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Export Options -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">Export Options</h3>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-600 mb-1"
                >DXF Version</label
              >
              <select
                v-model="dxfVersion"
                class="w-full border rounded px-2 py-1 text-sm"
              >
                <option value="R12">R12 (Most Compatible)</option>
                <option value="R2000">R2000</option>
                <option value="R2010">R2010</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1"
                >Layer Prefix</label
              >
              <input
                v-model="layerPrefix"
                type="text"
                class="w-full border rounded px-2 py-1 text-sm"
              />
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-3">
          <button
            class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            :disabled="loading"
            @click="refreshPreview"
          >
            {{ loading ? "Generating..." : "Preview" }}
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
          <h3 class="font-semibold text-gray-800 mb-3">Preview</h3>

          <div
            v-if="previewResult?.preview_svg"
            class="bg-gray-100 rounded p-2 overflow-auto"
            style="max-height: 500px"
            v-html="previewResult.preview_svg"
          />
          <div
            v-else
            class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px] text-gray-400"
          >
            Click Preview to generate
          </div>
        </div>

        <!-- Inlay Summary -->
        <div v-if="previewResult" class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">Inlay Summary</h3>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-600">Total Inlays:</span>
              <span class="ml-2 font-bold">{{
                previewResult.result.inlays.length
              }}</span>
            </div>
            <div>
              <span class="text-gray-600">Pattern:</span>
              <span class="ml-2 font-bold capitalize">{{ patternType }}</span>
            </div>
            <div>
              <span class="text-gray-600">Scale Length:</span>
              <span class="ml-2 font-mono"
                >{{ previewResult.result.scale_length_mm.toFixed(1) }} mm</span
              >
            </div>
            <div>
              <span class="text-gray-600">Frets:</span>
              <span class="ml-2">{{ previewResult.result.num_frets }}</span>
            </div>
          </div>
        </div>

        <!-- Inlay Details -->
        <div
          v-if="previewResult?.result.inlays?.length"
          class="bg-white border rounded-lg p-4 max-h-[300px] overflow-y-auto"
        >
          <h3 class="font-semibold text-gray-800 mb-3">Inlay Details</h3>

          <table class="w-full text-xs">
            <thead class="bg-gray-50 sticky top-0">
              <tr>
                <th class="py-1 px-2 text-left">Fret</th>
                <th class="py-1 px-2 text-right">X (mm)</th>
                <th class="py-1 px-2 text-right">Y (mm)</th>
                <th class="py-1 px-2 text-center">Double</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(inlay, idx) in previewResult.result.inlays"
                :key="idx"
                class="border-b"
              >
                <td class="py-1 px-2">{{ inlay.fret }}</td>
                <td class="py-1 px-2 text-right font-mono">
                  {{ inlay.center_x_mm.toFixed(2) }}
                </td>
                <td class="py-1 px-2 text-right font-mono">
                  {{ inlay.center_y_mm.toFixed(2) }}
                </td>
                <td class="py-1 px-2 text-center">
                  {{ inlay.is_double ? "●●" : "●" }}
                </td>
              </tr>
            </tbody>
          </table>
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
