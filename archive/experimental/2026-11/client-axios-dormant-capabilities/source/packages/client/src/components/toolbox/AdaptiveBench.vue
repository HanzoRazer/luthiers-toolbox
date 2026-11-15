<template>
  <div class="adaptive-bench">
    <!-- Header -->
    <div class="mb-3">
      <h2 class="text-base font-semibold text-gray-900">
        Adaptive Kernel Benchmark
      </h2>
      <p class="text-xs text-gray-600 mt-1">
        Compare offset spiral vs trochoid corner strategies for rectangular pockets
      </p>
    </div>

    <!-- Two-column layout -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Left Panel: Parameters & Controls -->
      <div class="space-y-3">
        <!-- Mode Toggle -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-2">
            Strategy Mode
          </label>
          <div class="flex gap-2">
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
              🌀 Spiral
            </button>
            <button
              :class="[
                'flex-1 px-3 py-2 text-xs font-medium rounded border transition-colors',
                mode === 'trochoid'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              ]"
              :disabled="busy"
              @click="mode = 'trochoid'"
            >
              🔄 Trochoid
            </button>
          </div>
          <p class="text-[10px] text-gray-500 mt-1">
            {{ mode === 'spiral' ? 'Offset-based continuous spiral' : 'Trochoidal corner milling' }}
          </p>
        </div>

        <!-- Rectangle Dimensions -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Width (mm)
            </label>
            <input
              v-model.number="params.width"
              type="number"
              step="1"
              min="10"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Height (mm)
            </label>
            <input
              v-model.number="params.height"
              type="number"
              step="1"
              min="10"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
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
          <div v-if="mode === 'spiral'">
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Stepover (mm)
            </label>
            <input
              v-model.number="params.stepover"
              type="number"
              step="0.1"
              min="0.1"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
          <div v-if="mode === 'trochoid'">
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Loop Pitch (mm)
            </label>
            <input
              v-model.number="params.loop_pitch"
              type="number"
              step="0.1"
              min="0.1"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
        </div>

        <!-- Mode-specific parameters -->
        <div class="grid grid-cols-2 gap-3">
          <div v-if="mode === 'spiral'">
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Corner Fillet (mm)
            </label>
            <input
              v-model.number="params.corner_fillet"
              type="number"
              step="0.1"
              min="0"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
          <div v-if="mode === 'trochoid'">
            <label class="block text-xs font-medium text-gray-700 mb-1">
              Amplitude
            </label>
            <input
              v-model.number="params.amp"
              type="number"
              step="0.1"
              min="0.1"
              max="1"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              :disabled="busy"
            >
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button
            :disabled="busy"
            class="flex-1 px-3 py-2 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            @click="runBenchmark"
          >
            {{ busy ? 'Running...' : 'Run Benchmark' }}
          </button>
          <button
            :disabled="busy"
            class="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            @click="clearResults"
          >
            Clear
          </button>
        </div>

        <!-- Info Display -->
        <div
          v-if="svgResult"
          class="border border-blue-100 rounded-lg p-3 bg-blue-50"
        >
          <h3 class="text-xs font-semibold text-blue-900 mb-2">
            ✓ {{ mode === 'spiral' ? 'Spiral' : 'Trochoid' }} Generated
          </h3>
          <div class="text-[11px] text-blue-700">
            <p>Pocket: {{ params.width }}×{{ params.height }} mm</p>
            <p>Tool: Ø{{ params.tool_dia }} mm</p>
            <p v-if="mode === 'spiral'">
              Stepover: {{ params.stepover }} mm
            </p>
            <p v-if="mode === 'trochoid'">
              Pitch: {{ params.loop_pitch }} mm
            </p>
          </div>
        </div>

        <!-- Error Display -->
        <div
          v-if="errorMessage"
          class="border border-red-200 rounded-lg p-3 bg-red-50"
        >
          <div class="flex items-start gap-2">
            <span class="text-red-600 text-xs">⚠️</span>
            <div class="flex-1">
              <p class="text-xs font-medium text-red-900">
                Error
              </p>
              <p class="text-[11px] text-red-700 mt-1">
                {{ errorMessage }}
              </p>
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
            class="px-2 py-1 text-[10px] font-medium text-blue-600 hover:text-blue-700 hover:underline"
            @click="downloadSVG"
          >
            Download SVG
          </button>
        </div>
        
        <!-- SVG Container -->
        <div
          class="border border-gray-300 rounded-lg bg-white overflow-hidden"
          style="height: 500px;"
        >
          <div
            v-if="svgResult"
            class="w-full h-full p-4 overflow-auto"
            v-html="svgResult"
          />
          <div
            v-else
            class="w-full h-full flex items-center justify-center text-gray-400 text-xs"
          >
            <div class="text-center">
              <svg
                class="w-16 h-16 mx-auto mb-2 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <p>No preview available</p>
              <p class="text-[10px] mt-1">
                Configure parameters and run benchmark
              </p>
            </div>
          </div>
        </div>

        <!-- Mode Comparison Hint -->
        <div class="mt-2 text-[10px] text-gray-500 border-t border-gray-200 pt-2">
          <p class="font-medium text-gray-700 mb-1">
            💡 Kernel Tuning Tip:
          </p>
          <p>
            {{ mode === 'spiral' 
              ? 'Spiral mode: Best for open pockets with gradual depth changes. Adjust stepover for balance between speed and surface finish.'
              : 'Trochoid mode: Best for tight corners and heavy cuts. Tune radius and pitch to control chip load and heat.'
            }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { benchmarkOffsetSpiral, benchmarkTrochoidCorners } from '@/api/n16'

const mode = ref<'spiral' | 'trochoid'>('spiral')

const params = ref({
  width: 100,
  height: 60,
  tool_dia: 6.0,
  stepover: 2.4,
  corner_fillet: 0.0,
  loop_pitch: 2.5,
  amp: 0.4
})

const svgResult = ref<string | null>(null)
const busy = ref(false)
const errorMessage = ref<string | null>(null)

async function runBenchmark() {
  busy.value = true
  errorMessage.value = null
  svgResult.value = null

  try {
    const svg = mode.value === 'spiral'
      ? await benchmarkOffsetSpiral({
          width: params.value.width,
          height: params.value.height,
          tool_dia: params.value.tool_dia,
          stepover: params.value.stepover,
          corner_fillet: params.value.corner_fillet
        })
      : await benchmarkTrochoidCorners({
          width: params.value.width,
          height: params.value.height,
          tool_dia: params.value.tool_dia,
          loop_pitch: params.value.loop_pitch,
          amp: params.value.amp
        })

    svgResult.value = svg
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || error?.message || 'Benchmark failed'
    console.error('Benchmark error:', error)
  } finally {
    busy.value = false
  }
}

function downloadSVG() {
  if (!svgResult.value) return

  const modeLabel = mode.value === 'spiral' ? 'spiral' : 'trochoid'
  const blob = new Blob([svgResult.value], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `adaptive_bench_${modeLabel}_${Date.now()}.svg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function clearResults() {
  svgResult.value = null
  errorMessage.value = null
}
</script>

<style scoped>
.adaptive-bench {
  padding: 1rem;
}

/* SVG styling for better visibility */
.adaptive-bench :deep(svg) {
  max-width: 100%;
  height: auto;
}

.adaptive-bench :deep(svg path) {
  vector-effect: non-scaling-stroke;
}
</style>
