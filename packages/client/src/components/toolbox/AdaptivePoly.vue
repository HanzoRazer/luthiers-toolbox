<template>
  <div class="p-4 bg-white">
    <!-- Header -->
    <div class="mb-3">
      <h2 class="text-base font-semibold text-gray-900">
        Adaptive Polygon Processor
      </h2>
      <p class="text-xs text-gray-600 mt-1">
        N17: Offset preview | N18: Spiral G-code generation
      </p>
    </div>

    <!-- Two-column layout -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Left Panel: Parameters & Controls -->
      <div class="space-y-3">
        <!-- Mode Toggle -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-2">
            Processing Mode
          </label>
          <div class="flex gap-2">
            <button
              :class="[
                'flex-1 px-3 py-2 text-xs font-medium rounded border transition-colors',
                mode === 'preview'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
              @click="mode = 'preview'"
            >
              📊 Preview (N17)
            </button>
            <button
              :class="[
                'flex-1 px-3 py-2 text-xs font-medium rounded border transition-colors',
                mode === 'spiral'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
              @click="mode = 'spiral'"
            >
              🌀 Spiral (N18)
            </button>
          </div>
          <p class="text-[10px] text-gray-500 mt-1">
            {{ mode === 'preview' ? 'JSON offset rings' : 'Continuous spiral G-code' }}
          </p>
        </div>

        <!-- Polygon Input -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">
            Boundary Polygon (JSON)
          </label>
          <textarea
            v-model="polygonInput"
            placeholder="[[0,0], [100,0], [100,60], [0,60]]"
            class="w-full h-24 px-2 py-1.5 text-[11px] font-mono border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            :disabled="busy"
          />
          <div class="flex items-center justify-between text-[10px] text-gray-500 mt-1">
            <span>{{ pointCount }} points</span>
            <button
              class="text-blue-600 hover:underline"
              :disabled="busy"
              @click="useDefaultPolygon"
            >
              Use default rectangle
            </button>
          </div>
        </div>

        <!-- Tool Parameters -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Tool Diameter (mm)
            </label>
            <input
              v-model.number="params.tool_dia"
              type="number"
              step="0.1"
              min="0.1"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              {{ mode === 'preview' ? 'Stepover (%)' : 'Stepover (mm)' }}
            </label>
            <input
              v-model.number="stepoverValue"
              type="number"
              step="0.1"
              :min="mode === 'preview' ? 10 : 0.1"
              :max="mode === 'preview' ? 90 : undefined"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
        </div>

        <!-- N17 Specific: Link Mode -->
        <div v-if="mode === 'preview'">
          <label class="block text-xs font-medium text-gray-700 mb-1">
            Link Mode
          </label>
          <div class="flex gap-2">
            <button
              :class="[
                'flex-1 px-2 py-1.5 text-xs rounded border transition-colors',
                params.link_mode === 'arc'
                  ? 'bg-gray-700 text-white border-gray-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
              @click="params.link_mode = 'arc'"
            >
              Arc (G2/G3)
            </button>
            <button
              :class="[
                'flex-1 px-2 py-1.5 text-xs rounded border transition-colors',
                params.link_mode === 'linear'
                  ? 'bg-gray-700 text-white border-gray-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
              @click="params.link_mode = 'linear'"
            >
              Linear (G1)
            </button>
          </div>
        </div>

        <!-- N18 Specific: Spiral Parameters -->
        <div
          v-if="mode === 'spiral'"
          class="grid grid-cols-2 gap-3"
        >
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Feed Rate (mm/min)
            </label>
            <input
              v-model.number="params.base_feed"
              type="number"
              step="50"
              min="100"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Cutting Depth (mm)
            </label>
            <input
              v-model.number="params.z"
              type="number"
              step="0.1"
              max="0"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button
            :disabled="busy || !isValidPolygon"
            class="flex-1 px-3 py-2 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            @click="runProcessor"
          >
            {{ busy ? 'Processing...' : (mode === 'preview' ? 'Generate Preview' : 'Generate G-code') }}
          </button>
          <button
            :disabled="busy"
            class="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            @click="clearResults"
          >
            Clear
          </button>
        </div>

        <!-- Error Display -->
        <div
          v-if="errorMessage"
          class="border border-red-200 rounded-lg p-3 bg-red-50"
        >
          <p class="text-xs font-medium text-red-900">
            ⚠️ Error
          </p>
          <p class="text-[11px] text-red-700 mt-1">
            {{ errorMessage }}
          </p>
        </div>

        <!-- Stats Display -->
        <div
          v-if="previewResult"
          class="border border-blue-100 rounded-lg p-3 bg-blue-50"
        >
          <h3 class="text-xs font-semibold text-blue-900 mb-2">
            ✓ Preview Generated (N17)
          </h3>
          <div class="space-y-1 text-[11px] text-blue-700">
            <div class="flex justify-between">
              <span>Total Passes:</span>
              <span class="font-medium">{{ previewResult.meta.total_passes }}</span>
            </div>
            <div class="flex justify-between">
              <span>Total Points:</span>
              <span class="font-medium">{{ previewResult.meta.total_points }}</span>
            </div>
            <div class="flex justify-between">
              <span>Step Distance:</span>
              <span class="font-medium">{{ previewResult.step.toFixed(2) }} mm</span>
            </div>
            <div class="flex justify-between">
              <span>Bbox:</span>
              <span class="font-medium text-[10px]">
                {{ previewResult.bbox.min_x.toFixed(1) }}, {{ previewResult.bbox.min_y.toFixed(1) }} → 
                {{ previewResult.bbox.max_x.toFixed(1) }}, {{ previewResult.bbox.max_y.toFixed(1) }}
              </span>
            </div>
          </div>
        </div>

        <div
          v-if="gcodeResult"
          class="border border-green-100 rounded-lg p-3 bg-green-50"
        >
          <h3 class="text-xs font-semibold text-green-900 mb-2">
            ✓ G-code Generated {{ mode === 'spiral' ? '(N18)' : '(N17)' }}
          </h3>
          <div class="space-y-1 text-[11px] text-green-700">
            <div class="flex justify-between">
              <span>Lines:</span>
              <span class="font-medium">{{ gcodeLineCount }}</span>
            </div>
            <div class="flex justify-between">
              <span>Size:</span>
              <span class="font-medium">{{ gcodeSize }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: Preview/Output -->
      <div class="space-y-3">
        <!-- Preview Container -->
        <div class="border border-gray-300 rounded-lg bg-gray-50 h-[400px] overflow-auto">
          <!-- JSON Preview (N17) -->
          <div
            v-if="mode === 'preview' && previewResult"
            class="p-3"
          >
            <h3 class="text-xs font-semibold text-gray-900 mb-2">
              Offset Rings Preview
            </h3>
            <pre class="text-[10px] font-mono text-gray-700 whitespace-pre-wrap">{{ JSON.stringify(previewResult, null, 2) }}</pre>
          </div>

          <!-- G-code Preview (N17 or N18) -->
          <div
            v-if="gcodeResult"
            class="p-3"
          >
            <h3 class="text-xs font-semibold text-gray-900 mb-2">
              G-code Output
            </h3>
            <pre class="text-[10px] font-mono text-gray-700 whitespace-pre-wrap">{{ gcodePreview }}</pre>
          </div>

          <!-- Empty State -->
          <div
            v-if="!previewResult && !gcodeResult"
            class="flex items-center justify-center h-full text-gray-400"
          >
            <div class="text-center">
              <p class="text-sm">
                No results yet
              </p>
              <p class="text-xs mt-1">
                Configure parameters and click Generate
              </p>
            </div>
          </div>
        </div>

        <!-- Download Button -->
        <button
          v-if="gcodeResult"
          class="w-full px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          @click="downloadGcode"
        >
          💾 Download G-code
        </button>

        <!-- Mode Comparison Hints -->
        <div class="border border-gray-200 rounded-lg p-3 bg-gray-50">
          <h3 class="text-xs font-semibold text-gray-900 mb-2">
            {{ mode === 'preview' ? '📊 N17: Offset Preview' : '🌀 N18: Spiral G-code' }}
          </h3>
          <ul class="text-[10px] text-gray-600 space-y-1 list-disc list-inside">
            <template v-if="mode === 'preview'">
              <li>Generates JSON offset rings using pyclipper</li>
              <li>Shows all offset passes before G-code generation</li>
              <li>Stepover as percentage (40% = 0.4)</li>
              <li>Choose arc or linear linking mode</li>
            </template>
            <template v-else>
              <li>Generates continuous spiral toolpath</li>
              <li>Adaptive engagement control</li>
              <li>Stepover in absolute mm distance</li>
              <li>Ready-to-run G-code output</li>
            </template>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  generatePolygonOffsetPreview, 
  generatePolygonOffsetGcode,
  generateAdaptiveSpiralGcode,
  type OffsetPreview
} from '@/api/n17_n18'

const mode = ref<'preview' | 'spiral'>('preview')
const polygonInput = ref('[[0,0], [100,0], [100,60], [0,60]]')
const stepoverValue = ref(45) // % for preview, mm for spiral

const params = ref({
  tool_dia: 6.0,
  link_mode: 'arc' as 'arc' | 'linear',
  base_feed: 1200,
  z: -1.5,
  safe_z: 5.0
})

const previewResult = ref<OffsetPreview | null>(null)
const gcodeResult = ref<string | null>(null)
const busy = ref(false)
const errorMessage = ref<string | null>(null)

const pointCount = computed(() => {
  try {
    const parsed = JSON.parse(polygonInput.value)
    return Array.isArray(parsed) ? parsed.length : 0
  } catch {
    return 0
  }
})

const isValidPolygon = computed(() => {
  try {
    const parsed = JSON.parse(polygonInput.value)
    return Array.isArray(parsed) && parsed.length >= 3
  } catch {
    return false
  }
})

const gcodeLineCount = computed(() => {
  if (!gcodeResult.value) return 0
  return gcodeResult.value.split('\n').length
})

const gcodeSize = computed(() => {
  if (!gcodeResult.value) return '0 B'
  const bytes = gcodeResult.value.length
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
})

const gcodePreview = computed(() => {
  if (!gcodeResult.value) return ''
  const lines = gcodeResult.value.split('\n')
  if (lines.length <= 50) return gcodeResult.value
  return lines.slice(0, 50).join('\n') + `\n... (${lines.length - 50} more lines)`
})

function useDefaultPolygon() {
  polygonInput.value = '[[0,0], [100,0], [100,60], [0,60]]'
}

async function runProcessor() {
  if (!isValidPolygon.value) {
    errorMessage.value = 'Invalid polygon. Must be valid JSON array with at least 3 points.'
    return
  }

  busy.value = true
  errorMessage.value = null
  previewResult.value = null
  gcodeResult.value = null

  try {
    const polygon = JSON.parse(polygonInput.value)

    if (mode.value === 'preview') {
      // N17: Generate offset preview
      const stepoverFraction = stepoverValue.value / 100 // Convert % to fraction
      previewResult.value = await generatePolygonOffsetPreview({
        polygon,
        tool_dia: params.value.tool_dia,
        stepover: stepoverFraction,
        link_mode: params.value.link_mode,
        units: 'mm'
      })
    } else {
      // N18: Generate spiral G-code
      gcodeResult.value = await generateAdaptiveSpiralGcode({
        polygon,
        tool_dia: params.value.tool_dia,
        stepover: stepoverValue.value, // Already in mm
        z: params.value.z,
        safe_z: params.value.safe_z,
        base_feed: params.value.base_feed,
        units: 'mm'
      })
    }
  } catch (error: any) {
    errorMessage.value = error?.message || 'Processing failed'
    console.error('Processor error:', error)
  } finally {
    busy.value = false
  }
}

function downloadGcode() {
  if (!gcodeResult.value) return

  const modeLabel = mode.value === 'spiral' ? 'spiral' : 'offset'
  const blob = new Blob([gcodeResult.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `adaptive_poly_${modeLabel}_${Date.now()}.nc`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function clearResults() {
  previewResult.value = null
  gcodeResult.value = null
  errorMessage.value = null
}
</script>
