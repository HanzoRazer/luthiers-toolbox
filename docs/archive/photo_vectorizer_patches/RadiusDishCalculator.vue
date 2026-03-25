<script setup lang="ts">
/**
 * RadiusDishCalculator.vue — Calculator tab
 *
 * Now shows brace camber alongside dish depth.
 * The missing link: dish radius → brace pre-bend.
 */
import { ref } from 'vue'
import { calculateDish, getBraceCamber, type BraceCamberResult } from '@/api/radius-dish'

const radius   = ref<number>(20)
const width    = ref<number>(381)
const length   = ref<number>(381)
const braceLen = ref<number>(350)

const loading    = ref(false)
const error      = ref<string | null>(null)
const dishResult = ref<any>(null)
const cambers    = ref<BraceCamberResult[]>([])

// Common brace lengths for a 6-brace OM back (approximate)
const OM_BRACE_LENGTHS = [262, 245, 227, 311, 348, 304]

async function calculate() {
  loading.value = true
  error.value   = null
  try {
    dishResult.value = await calculateDish(radius.value, width.value, length.value)
    // Calculate camber for each OM reference length
    cambers.value = await Promise.all(
      OM_BRACE_LENGTHS.map(L => getBraceCamber(L, radius.value))
    )
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function calcSingleCamber() {
  loading.value = true
  error.value   = null
  try {
    const r = await getBraceCamber(braceLen.value, radius.value)
    cambers.value = [r]
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-5">
    <div class="grid md:grid-cols-2 gap-5">

      <!-- Inputs -->
      <div class="space-y-3">
        <h3 class="font-semibold text-lg">Dish depth calculator</h3>
        <p class="text-sm opacity-70">
          Exact formula: depth = R − √(R² − (W/2)²)
        </p>

        <div class="space-y-3">
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Radius (feet)</span>
            <input v-model.number="radius" type="number" step="1" min="5" max="50"
              class="border p-2 rounded">
          </label>
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Dish width (mm)</span>
            <input v-model.number="width" type="number" step="5" class="border p-2 rounded">
          </label>
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Dish length (mm)</span>
            <input v-model.number="length" type="number" step="5" class="border p-2 rounded">
          </label>
        </div>

        <button
          class="w-full px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
          :disabled="loading"
          @click="calculate"
        >
          Calculate
        </button>
      </div>

      <!-- Dish depth results -->
      <div class="space-y-3">
        <h3 class="font-semibold text-lg">Dish geometry</h3>
        <div v-if="dishResult" class="p-4 bg-gray-50 rounded space-y-2 text-sm">
          <div><strong>Radius:</strong> {{ dishResult.radius_ft }}ft ({{ dishResult.radius_mm }}mm)</div>
          <div><strong>Width depth:</strong>
            <span class="text-blue-700 font-bold">
              {{ dishResult.depth_at_width_mm }}mm
              ({{ (dishResult.depth_at_width_mm / 25.4).toFixed(4) }}")
            </span>
          </div>
          <div v-if="dishResult.depth_at_length_mm !== dishResult.depth_at_width_mm">
            <strong>Length depth:</strong> {{ dishResult.depth_at_length_mm }}mm
          </div>
          <div class="text-xs opacity-60">{{ dishResult.formula }}</div>
        </div>
        <div v-else class="p-4 bg-gray-50 rounded text-sm opacity-60">
          Enter values and click Calculate.
        </div>
      </div>
    </div>

    <!-- Brace camber section -->
    <div class="border rounded p-4 space-y-3">
      <h3 class="font-semibold">Brace camber calculator</h3>
      <p class="text-sm opacity-70">
        The amount the brace bottom must be relieved to sit flush on this dish.
        Formula: camber = L² / (8R)
      </p>

      <div class="flex items-end gap-3">
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Brace length (mm)</span>
          <input v-model.number="braceLen" type="number" step="5" class="border p-2 rounded w-36">
        </label>
        <button
          class="px-3 py-2 rounded border hover:bg-gray-50 transition-colors text-sm"
          :disabled="loading"
          @click="calcSingleCamber"
        >
          Calculate
        </button>
      </div>

      <!-- Camber results -->
      <div v-if="cambers.length">
        <div v-if="cambers.length === 1" class="p-3 bg-green-50 border border-green-200 rounded text-sm">
          <div class="font-medium text-green-800">{{ cambers[0].note }}</div>
          <div class="text-xs opacity-70 mt-1">{{ cambers[0].formula }}</div>
        </div>
        <div v-else>
          <p class="text-sm font-medium mb-2">OM back brace set ({{ radius }}ft radius):</p>
          <table class="w-full text-sm border rounded overflow-hidden">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left p-2">Brace</th>
                <th class="text-left p-2">Length</th>
                <th class="text-left p-2">Camber</th>
                <th class="text-left p-2">Camber (inch)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(c, i) in cambers" :key="i" class="border-t">
                <td class="p-2">Brace {{ i + 1 }}</td>
                <td class="p-2 font-mono">{{ c.brace_length_mm }}mm</td>
                <td class="p-2 font-mono text-blue-700 font-medium">{{ c.camber_mm }}mm</td>
                <td class="p-2 font-mono">{{ c.camber_in }}"</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
      {{ error }}
    </div>
  </div>
</template>
