<template>
  <div class="backplot-gcode">
    <!-- Header -->
    <div class="mb-3">
      <h2 class="text-base font-semibold text-gray-900">G-code Backplot & Estimator</h2>
      <p class="text-xs text-gray-600 mt-1">
        Visualize any G-code and estimate machining time
      </p>
    </div>

    <!-- Two-column layout -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Left Panel: Input & Controls -->
      <div class="space-y-3">
        <!-- G-code Input -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">
            G-code Input
          </label>
          <textarea
            v-model="gcodeInput"
            placeholder="Paste G-code here...&#10;G21&#10;G90&#10;G0 X0 Y0&#10;G1 Z-1.5 F300&#10;..."
            class="w-full h-64 px-2 py-1.5 text-[11px] font-mono border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            :disabled="busy"
          />
          <div class="text-[10px] text-gray-500 mt-1">
            {{ gcodeLineCount }} lines
          </div>
        </div>

        <!-- Units Selection -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">
            Units
          </label>
          <div class="flex gap-2">
            <button
              @click="units = 'mm'"
              :class="[
                'px-3 py-1 text-xs rounded border transition-colors',
                units === 'mm'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
            >
              mm
            </button>
            <button
              @click="units = 'inch'"
              :class="[
                'px-3 py-1 text-xs rounded border transition-colors',
                units === 'inch'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
            >
              inch
            </button>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button
            @click="runBackplot"
            :disabled="busy || !gcodeInput.trim()"
            class="flex-1 px-3 py-2 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {{ busy ? 'Generating...' : 'Generate Backplot' }}
          </button>
          <button
            @click="clearAll"
            :disabled="busy"
            class="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
          >
            Clear
          </button>
        </div>

        <!-- Stats Display -->
        <div v-if="stats" class="border border-gray-200 rounded-lg p-3 bg-gray-50">
          <h3 class="text-xs font-semibold text-gray-900 mb-2">Statistics</h3>
          <div class="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span class="text-gray-600">Travel:</span>
              <span class="font-medium text-gray-900 ml-1">{{ stats.travel_mm.toFixed(2) }} mm</span>
            </div>
            <div>
              <span class="text-gray-600">Cutting:</span>
              <span class="font-medium text-gray-900 ml-1">{{ stats.cut_mm.toFixed(2) }} mm</span>
            </div>
            <div>
              <span class="text-gray-600">Rapid Time:</span>
              <span class="font-medium text-gray-900 ml-1">{{ formatTime(stats.t_rapid_min * 60) }}</span>
            </div>
            <div>
              <span class="text-gray-600">Feed Time:</span>
              <span class="font-medium text-gray-900 ml-1">{{ formatTime(stats.t_feed_min * 60) }}</span>
            </div>
            <div class="col-span-2">
              <span class="text-gray-600">Total Time:</span>
              <span class="font-medium text-blue-600 ml-1">{{ formatTime(stats.t_total_min * 60) }}</span>
            </div>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="errorMessage" class="border border-red-200 rounded-lg p-3 bg-red-50">
          <div class="flex items-start gap-2">
            <span class="text-red-600 text-xs">⚠️</span>
            <div class="flex-1">
              <p class="text-xs font-medium text-red-900">Error</p>
              <p class="text-[11px] text-red-700 mt-1">{{ errorMessage }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: SVG Preview -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-xs font-medium text-gray-700">
            Toolpath Preview
          </label>
          <button
            v-if="svgResult"
            @click="downloadSVG"
            class="px-2 py-1 text-[10px] font-medium text-blue-600 hover:text-blue-700 hover:underline"
          >
            Download SVG
          </button>
        </div>
        
        <!-- SVG Container -->
        <div class="border border-gray-300 rounded-lg bg-white overflow-hidden" style="height: 500px;">
          <div v-if="svgResult" class="w-full h-full p-4 overflow-auto" v-html="svgResult" />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-xs">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>No preview available</p>
              <p class="text-[10px] mt-1">Paste G-code and click Generate</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { generateBackplot, estimateGcode, type SimulateResponse } from '@/api/n15'

const gcodeInput = ref('')
const units = ref<'mm' | 'inch'>('mm')
const svgResult = ref<string | null>(null)
const stats = ref<SimulateResponse | null>(null)
const busy = ref(false)
const errorMessage = ref<string | null>(null)

const gcodeLineCount = computed(() => {
  const lines = gcodeInput.value.trim().split('\n')
  return lines.filter(l => l.trim()).length
})

async function runBackplot() {
  if (!gcodeInput.value.trim()) return

  busy.value = true
  errorMessage.value = null
  svgResult.value = null
  stats.value = null

  try {
    // Call both endpoints in parallel
    const [svg, estimate] = await Promise.all([
      generateBackplot({
        gcode: gcodeInput.value,
        units: units.value,
        stroke: 'blue'
      }),
      estimateGcode({
        gcode: gcodeInput.value,
        units: units.value
      })
    ])

    svgResult.value = svg
    stats.value = estimate
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || error?.message || 'Failed to generate backplot'
    console.error('Backplot generation error:', error)
  } finally {
    busy.value = false
  }
}

function downloadSVG() {
  if (!svgResult.value) return

  const blob = new Blob([svgResult.value], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `backplot_${Date.now()}.svg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function clearAll() {
  gcodeInput.value = ''
  svgResult.value = null
  stats.value = null
  errorMessage.value = null
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}m ${secs}s`
}
</script>

<style scoped>
.backplot-gcode {
  @apply p-4;
}

/* SVG styling for better visibility */
.backplot-gcode :deep(svg) {
  max-width: 100%;
  height: auto;
}

.backplot-gcode :deep(svg path) {
  vector-effect: non-scaling-stroke;
}
</style>
