<script setup lang="ts">
/**
 * BraceResultsPanel.vue
 * Results and export panel for bracing calculations.
 */
interface BatchResult {
  total_mass_grams: number
  total_stiffness: number
}

defineProps<{
  batchResult: BatchResult | null
  braceCount: number
  batchName: string
  dxfVersion: string
  includeCenterlines: boolean
  includeLabels: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  'update:dxfVersion': [value: string]
  'update:includeCenterlines': [value: boolean]
  'update:includeLabels': [value: boolean]
  exportDXF: []
}>()
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold text-gray-800">
      Results & Export
    </h2>

    <!-- Batch Summary -->
    <div
      v-if="batchResult"
      class="bg-white border rounded-lg p-4"
    >
      <h3 class="font-semibold text-gray-800 mb-3">
        Batch Summary
      </h3>

      <div class="grid grid-cols-2 gap-4">
        <div class="bg-amber-50 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-amber-700">
            {{ batchResult.total_mass_grams.toFixed(1) }}
          </div>
          <div class="text-xs text-amber-600 mt-1">
            Total Mass (grams)
          </div>
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
        <strong>{{ braceCount }}</strong> braces in set "{{ batchName }}"
      </div>
    </div>

    <!-- Export Options -->
    <div class="bg-white border rounded-lg p-4 space-y-3">
      <h3 class="font-semibold text-gray-800">
        Export Options
      </h3>

      <div>
        <label class="block text-xs text-gray-600 mb-1">DXF Version</label>
        <select
          :value="dxfVersion"
          class="w-full border rounded px-3 py-2 text-sm"
          @change="emit('update:dxfVersion', ($event.target as HTMLSelectElement).value)"
        >
          <option value="R12">
            R12 (Most Compatible)
          </option>
          <option value="R2000">
            R2000
          </option>
          <option value="R2010">
            R2010
          </option>
        </select>
      </div>

      <label class="flex items-center gap-2 text-sm">
        <input
          :checked="includeCenterlines"
          type="checkbox"
          @change="emit('update:includeCenterlines', ($event.target as HTMLInputElement).checked)"
        >
        Include centerlines
      </label>

      <label class="flex items-center gap-2 text-sm">
        <input
          :checked="includeLabels"
          type="checkbox"
          @change="emit('update:includeLabels', ($event.target as HTMLInputElement).checked)"
        >
        Include labels
      </label>
    </div>

    <!-- Export Button -->
    <button
      class="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
      :disabled="loading || braceCount === 0"
      @click="emit('exportDXF')"
    >
      Export DXF Layout
    </button>

    <!-- Profile Diagram -->
    <div class="bg-white border rounded-lg p-4">
      <h3 class="font-semibold text-gray-800 mb-3">
        Profile Reference
      </h3>

      <div class="grid grid-cols-2 gap-4 text-center text-xs">
        <div class="bg-gray-50 rounded p-2">
          <div class="text-lg mb-1">
            ▬
          </div>
          <div>Rectangular</div>
          <div class="text-gray-500">
            Max stiffness
          </div>
        </div>
        <div class="bg-gray-50 rounded p-2">
          <div class="text-lg mb-1">
            ▲
          </div>
          <div>Triangular</div>
          <div class="text-gray-500">
            Good stiffness/weight
          </div>
        </div>
        <div class="bg-gray-50 rounded p-2">
          <div class="text-lg mb-1">
            ⌓
          </div>
          <div>Parabolic</div>
          <div class="text-gray-500">
            Classic tone
          </div>
        </div>
        <div class="bg-gray-50 rounded p-2">
          <div class="text-lg mb-1">
            ⌢
          </div>
          <div>Scalloped</div>
          <div class="text-gray-500">
            Flexible ends
          </div>
        </div>
      </div>
    </div>

    <!-- Formula Reference -->
    <div class="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
      <h4 class="font-semibold mb-2">
        Section Properties
      </h4>
      <ul class="space-y-1">
        <li><strong>I</strong> = Moment of Inertia (mm⁴)</li>
        <li><strong>S</strong> = Section Modulus = I / c (mm³)</li>
        <li><strong>Mass</strong> = Area × Length × Density</li>
        <li><strong>Stiffness Index</strong> = Area × Length (relative)</li>
      </ul>
    </div>
  </div>
</template>
